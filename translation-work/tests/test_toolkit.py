from __future__ import annotations

import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native
import release
import storage
from native import Document, Error, digest, encoded, fingerprint, validate_text
from storage import Store, file_hash, read, write_atomic
from toolkit import BUILD, CATALOG, MANIFEST, TRANSLATIONS, Toolkit, batch_meta, jsonl, parse_jsonl, validate_zip

PROJECT = Path(__file__).resolve().parents[2]


def sources(count=6):
    return {"Config/text.csv": ("\ufeffTextRef,Value\r\n" + "".join(f'key.{i},"Synthetic message {i} for {{Actor}}"\r\n' for i in range(count))).encode(),
            "Config/tutorial.csv": b'Name,Title,Body,\r\nwelcome,Welcome,"One, two.\r\nA paragraph.",\r\n',
            "Config/pedia.csv": b'Topic,Title,Dependencies,Text,SeeAlso,ImageLoc\r\nLink.test,Test,,"<b>Bold</b> {{0}}",,\r\n',
            "Core/Events.csv": b'Key,Text\r\nevent.title,Event\r\nevent.body,"Synthetic event for {Actor}"\r\n'}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="star dynasties toolkit ")
        self.root = Path(self.temp.name) / "repository"
        self.root.mkdir()
        self.tool = Toolkit(self.root)
        profile=self.root/'translation-work/runtime-support.json'
        profile.parent.mkdir()
        profile.write_bytes(encoded({'schema':1,'deployable':True,'blockers':[],
                                    'evidence':'Synthetic fixtures only; not authorization for a game build'}))

    def tearDown(self):
        self.temp.cleanup()

    def initialize(self, files=None, batch_size=500):
        files = files or sources()
        with self.tool.store.lock():
            self.tool.synchronize(files, batch_size=batch_size, version="synthetic-1")
        return self.tool.load_manifest()

    def all(self):
        return self.tool.load_all(self.tool.load_manifest())[0]

    def payload(self, identities=None, value=None):
        manifest = self.tool.load_manifest()
        records, assignments = self.tool.load_all(manifest)
        identities = list(records) if identities is None else identities
        return {"generation": manifest["generation"], "expected_count": len(identities), "entries": [
            {"batch": assignments[i], "id": i, "source_sha256": records[i]["source_sha256"],
             "PTBR": value if value is not None else records[i]["EN"]} for i in identities]}

    def apply_payload(self, payload, replace=False):
        with self.tool.store.lock():
            return self.tool.apply(payload, replace)

    def complete(self):
        self.apply_payload(self.payload())
        with self.tool.store.lock():
            return self.tool.build()

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file() and ".state" not in p.parts}


class Workspace(Fixture):
    def test_initial_batches_default_and_last(self):
        manifest = self.initialize(sources(1001))
        self.assertEqual([v["count"] for v in manifest["batches"].values()], [500, 500, 7])
        self.assertEqual(self.tool.check()["translated"], 0)
        self.assertFalse((self.root / "PTBR").exists())
        self.assertEqual(len(self.all()), len(set(self.all())))
        self.assertIn("native", self.tool.catalog(manifest))

    def test_roundtrip_bom_multiline_quotes_blank_rows(self):
        raw = b'\xef\xbb\xbfKey,Text\r\na,"A, \"\"quote\"\"\r\nSecond line"\r\nb,B\r\n,\r\n'
        doc = Document("Core/Example.csv", raw)
        self.assertEqual(doc.render({}), raw)
        rendered = doc.render({doc.units[0]["id"]: 'A synthetic "value", and a\nline'})
        self.assertTrue(rendered.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(rendered.endswith(b'b,B\r\n,\r\n'))
        self.assertEqual(Document("Core/Example.csv", rendered).rows[1][1], 'A synthetic "value", and a\nline')

    def test_duplicate_keys_and_corrupt_csv_fail(self):
        for raw in (b'Key,Text\na,A\na,B\n', b'Key,Text\na,"Bad\n', b'Key,Text\na,A,B\n', b'Key,Text\na,"bad"tail\n'):
            with self.assertRaises(Error):
                Document("Core/Bad.csv", raw)
        with self.assertRaises(Error):
            Document("Config/text.csv", b"TextRef,Value\na,\xff\n")

    def test_token_validation_and_control_encoding(self):
        original = 'Use {he(Actor)} and {Actor}, $1 <b>{0:N2}</b> %s.'
        validate_text(original, 'Synthetic $1 <b>{0:N2}</b> %s {Actor} {he(Actor)}.')
        for value in ('Use {Actor}.', original + '{extra}', original.replace('$1', '$2'), original.replace('</b>', '</i>'), original+'\x00', '\ud800'):
            with self.assertRaises(Error):
                validate_text(original, value)
        with self.assertRaises(Error):
            validate_text(original, '')

    def test_partial_apply_immutable_fields_unknown_and_overwrite(self):
        self.initialize(batch_size=3)
        identities = [r['id'] for r in self.all().values() if r['source_file']=='Config/text.csv'][:3]
        payload = self.payload(identities)
        immutable = {k: {x: y for x, y in v.items() if x not in ('PTBR', 'history')} for k, v in self.all().items()}
        payload["entries"][1]["PTBR"] = "Broken placeholders"
        payload["entries"][2]["id"] = "unknown"
        result = self.apply_payload(payload)
        self.assertEqual(len(result['accepted']), 1)
        self.assertEqual(len(result['rejected']), 2)
        self.assertEqual(immutable, {k: {x: y for x, y in v.items() if x not in ('PTBR', 'history')} for k, v in self.all().items()})
        changed = self.payload([identities[0]], "Synthetic new {Actor}")
        self.assertEqual(len(self.apply_payload(changed)['rejected']), 1)
        self.assertEqual(len(self.apply_payload(changed, replace=True)['accepted']), 1)
        self.assertTrue(self.all()[identities[0]]['history'])
        self.assertFalse((self.root / 'PTBR').exists())

    def test_duplicate_wrong_count_generation_and_original_overwrite_rejected(self):
        self.initialize()
        base = self.payload([next(iter(self.all()))])
        for change in ('duplicate', 'generation', 'count', 'EN'):
            candidate = copy.deepcopy(base)
            if change == 'duplicate':
                candidate['entries'] *= 2
                candidate['expected_count'] = 2
            elif change == 'generation':
                candidate['generation'] = 'wrong'
            elif change == 'count':
                candidate['expected_count'] = 99
            else:
                candidate['entries'][0]['EN'] = 'tampering'
            before = self.snapshot()
            with self.assertRaises(Error):
                self.apply_payload(candidate)
            self.assertEqual(before, self.snapshot())

    def test_one_modified_source_preserves_all_others_and_assignments(self):
        files = sources(1501)
        self.initialize(files)
        self.apply_payload(self.payload())
        before = self.all()
        assignments = self.tool.load_all(self.tool.load_manifest())[1]
        files['Config/text.csv'] = files['Config/text.csv'].replace(b'Synthetic message 700 for', b'Changed source message 700 for')
        with self.tool.store.lock():
            result = self.tool.synchronize(files)
        self.assertEqual(result['counts']['modified'], 1)
        after = self.all()
        changed = [k for k in after if not after[k]['PTBR']]
        self.assertEqual(len(changed), 1)
        self.assertEqual(after[changed[0]]['history'][-1]['PTBR'], before[changed[0]]['PTBR'])
        self.assertEqual(assignments, self.tool.load_all(self.tool.load_manifest())[1])
        self.assertEqual(result['counts']['preserved_translations'], len(after)-1)

    def test_reordering_add_delete_rename_and_duplicate_values(self):
        files = sources()
        self.initialize(files, batch_size=3)
        self.apply_payload(self.payload())
        original_assignments = self.tool.load_all(self.tool.load_manifest())[1]
        rows = files['Core/Events.csv'].decode().splitlines(keepends=True)
        files['Core/Events.csv'] = (rows[0] + rows[2] + rows[1] + 'event.new,Event\r\n').encode()
        with self.tool.store.lock():
            result = self.tool.synchronize(files)
        self.assertEqual(result['counts']['reordered'], 2)
        self.assertEqual(result['counts']['added'], 1)
        for identity, batch in original_assignments.items():
            self.assertEqual(self.tool.load_all(self.tool.load_manifest())[1][identity], batch)
        files['Core/Events.csv'] = files['Core/Events.csv'].replace(b'event.title,', b'event.renamed,')
        with self.tool.store.lock():
            result = self.tool.synchronize(files)
        self.assertEqual(result['counts']['removed'], 1)
        self.assertEqual(result['counts']['added'], 1)
        texts = [r for r in self.all().values() if r['EN'] == 'Event']
        self.assertEqual(len(texts), 2)
        self.assertTrue(all(not r['PTBR'] for r in texts))

    def test_en_overwritten_new_file_and_rollback(self):
        self.initialize()
        self.apply_payload(self.payload())
        old = self.all()
        path = self.root / 'EN/Config/text.csv'
        original_bytes = path.read_bytes()
        path.write_bytes(original_bytes.replace(b'message 1 for', b'rewritten message 1 for'))
        extra = self.root / 'EN/Core/New.csv'
        extra.write_bytes(b'Key,Text\r\nnew,New source\r\n')
        with self.tool.store.lock():
            result = self.tool.sync()
        self.assertEqual(result['counts']['modified'], 1)
        self.assertEqual(result['counts']['added'], 1)
        with self.tool.store.lock():
            self.tool.store.rollback()
        self.assertEqual(self.all(), old)
        self.assertEqual(path.read_bytes(), original_bytes)
        self.assertFalse(extra.exists())
        self.tool.check()

    def test_removed_source_requires_exact_authorization(self):
        files = sources()
        self.initialize(files)
        del files['Core/Events.csv']
        before = self.snapshot()
        with self.tool.store.lock():
            with self.assertRaises(Error):
                self.tool.synchronize(files)
            self.tool.synchronize(files, allow_remove=['Core/Events.csv'])
        self.assertNotEqual(before, self.snapshot())
        self.assertEqual(self.tool.check()['records'], 10)

    def test_noop_sync_apply_dryrun_and_status_do_not_rewrite(self):
        self.initialize()
        before = self.snapshot()
        with self.tool.store.lock():
            self.assertEqual(self.tool.sync()['status'], 'unchanged')
        self.tool.sync(dry_run=True)
        self.tool.status()
        self.tool.store.gc(dry_run=True)
        self.assertEqual(before, self.snapshot())
        first = next(iter(self.all()))
        self.apply_payload(self.payload([first]))
        before = self.snapshot()
        self.assertIsNone(self.apply_payload(self.payload([first]))['transaction'])
        self.assertEqual(before, self.snapshot())

    def test_ambiguous_terms_changes_fail(self):
        files = sources()
        files['Config/terms.csv'] = b'Term,DisplayName,Visible\nTerm.A,A,TRUE\n,B,TRUE\n'
        self.initialize(files)
        files['Config/terms.csv'] = files['Config/terms.csv'].replace(b',B,', b',Changed,')
        with self.tool.store.lock():
            with self.assertRaisesRegex(Error, 'ambíguo'):
                self.tool.synchronize(files)

    def test_missing_catalog_corrupt_batch_and_missing_batch_fail(self):
        manifest = self.initialize()
        catalog = self.root / CATALOG
        catalog.unlink()
        with self.assertRaisesRegex(Error, 'Catálogo'):
            self.tool.check()
        batch = self.root / TRANSLATIONS / next(iter(manifest['batches']))
        batch.write_text('{bad json}\n', encoding='utf-8')
        with self.assertRaises(Error):
            self.tool.check()
        batch.unlink()
        with self.assertRaises(Error):
            self.tool.check()

    def test_source_file_explicit_and_wrong_tree_rejected(self):
        self.initialize()
        incoming = Path(self.temp.name) / 'source file with spaces.csv'
        incoming.write_bytes(b'Key,Text\nnew,New\n')
        with self.tool.store.lock():
            with self.assertRaises(Error):
                self.tool.sync(incoming)
            self.tool.sync(incoming, 'Core/Added.csv')
        self.assertIn('Core/Added.csv', self.tool.load_manifest()['sources'])
        with self.assertRaises(Error):
            self.tool.sync(self.root)

    def test_incomplete_and_stale_output_never_promote(self):
        self.initialize()
        before = self.snapshot()
        with self.tool.store.lock():
            with self.assertRaisesRegex(Error, 'incompleta'):
                self.tool.build()
        self.assertFalse((self.root / 'PTBR').exists())
        self.assertEqual(before, self.snapshot())
        self.complete()
        output = {p: (self.root / 'PTBR' / p).read_bytes() for p in self.tool.output_files()}
        files = {p: (self.root / 'EN' / p).read_bytes() for p in self.tool.load_manifest()['sources']}
        files['Core/Events.csv'] += b'new.pending,Pending\r\n'
        with self.tool.store.lock():
            self.tool.synchronize(files)
            with self.assertRaises(Error):
                self.tool.build()
        self.assertEqual(output, {p: (self.root / 'PTBR' / p).read_bytes() for p in self.tool.output_files()})
        self.assertEqual(self.tool.status()['output'], 'stale')

    def test_build_gate_tamper_missing_forged_complete_and_zip(self):
        self.initialize()
        self.complete()
        self.assertTrue(self.tool.verify_output()['valid'])
        output = self.root / 'PTBR/Config/text.csv'
        previous = output.read_bytes()
        output.write_bytes(previous + b'\n')
        with self.assertRaisesRegex(Error, 'adulterada'):
            self.tool.verify_output()
        output.unlink()
        with self.assertRaises(Error):
            self.tool.verify_output()
        output.write_bytes(previous)
        target = self.root / 'translation-work/dist/PTBR.zip'
        self.tool.package(target)
        first = target.read_bytes()
        self.tool.package(target)
        self.assertEqual(first, target.read_bytes())
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(set(archive.namelist()), self.tool.output_files())
            self.assertNotIn('LICENSE', archive.namelist())
            self.assertFalse(any(x.startswith('PTBR/') for x in archive.namelist()))
        output.write_bytes(previous)
        entry = next(r for r in self.all().values() if r['source_file']=='Core/Events.csv')
        self.apply_payload(self.payload([entry['id']], 'Synthetic replacement'), replace=True)
        proof_path = self.root / BUILD
        proof = json.loads(proof_path.read_bytes())
        proof['complete'] = True
        proof['manifest_sha256'] = 'forged'
        proof_path.write_bytes(encoded(proof))
        with self.assertRaises(Error):
            self.tool.verify_output()

    def test_path_escape_collisions_and_symlinks(self):
        for path in ('../outside.csv', '/abs', 'Core/../outside.csv', 'C:/file.csv', 'Core\\File.csv', 'Core/CON.csv', 'Core/test. /x'):
            with self.assertRaises(Error):
                native.safe_relative(path)
        files = sources()
        files['Core/events.csv'] = files['Core/Events.csv']
        # Collision detection applies to discovery, not a raw mapping injected by tests.
        en = self.root / 'EN'
        for name, raw in files.items():
            p = en / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        link = self.root / 'linked'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name == 'nt':
                process=subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],capture_output=True)
                if process.returncode:
                    self.skipTest('Symlink/junction indisponível neste Windows')
            else:
                self.skipTest('Criação de symlink indisponível')
        with self.assertRaises(Error):
            storage.safe_path(self.root, 'linked/file')

    def test_wrong_installation_modded_unknown_multiple_and_dryrun(self):
        files = sources()
        game = Path(self.temp.name) / 'GOG Games/Star Dynasties'
        for name, raw in files.items():
            p = game / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        (game / 'identity.info').write_text('synthetic identity')
        profile = {'version':'synthetic-1', 'files':{p:digest(v) for p,v in files.items()},
                   'identity':{'identity.info':digest((game/'identity.info').read_bytes())}}
        profile_path = self.root / 'translation-work/trusted-distributions.json'
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_bytes(encoded({'distributions':[profile]}))
        before = self.snapshot()
        game_before = {p.relative_to(game).as_posix():p.read_bytes() for p in game.rglob('*') if p.is_file()}
        self.assertEqual(self.tool.update_sources(game, dry_run=True)['status'], 'dry-run')
        self.assertEqual(before, self.snapshot())
        with self.tool.store.lock():
            self.tool.update_sources(game)
        before = self.snapshot()
        with self.tool.store.lock():
            self.assertEqual(self.tool.update_sources(game)['status'], 'unchanged')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(game_before, {p.relative_to(game).as_posix():p.read_bytes() for p in game.rglob('*') if p.is_file()})
        self.assertEqual(self.tool.autodetect().resolve(), game.resolve())
        (game/'Config/text.csv').write_bytes(files['Config/text.csv']+b'bad,Modded\r\n')
        with self.assertRaises(Error):
            self.tool.verified_installation(game)
        with patch.object(self.tool, 'autodetect', side_effect=Error('Use --game-root')):
            with self.assertRaisesRegex(Error, '--game-root'):
                self.tool.update_sources()
        with self.assertRaises(Error):
            self.tool.verified_installation(game/'Config')
        with self.assertRaises(Error):
            self.tool.verified_installation(self.root)

    def test_concurrent_lock_and_concurrent_file_edit(self):
        self.initialize()
        with self.tool.store.lock():
            with self.assertRaises(Error):
                with Store(self.root).lock():
                    pass
            path = 'translation-work/reports/test.json'
            with self.assertRaisesRegex(Error, 'concorrente'):
                self.tool.store.transact({path:b'new'}, {path:'bad hash'}, 'test')

    def test_game_directory_cannot_be_used_as_repository_even_by_mistake(self):
        game=Path(self.temp.name)/'readonly game'
        game.mkdir()
        (game/'StarDynasties.exe').write_bytes(b'synthetic executable marker; never executed')
        (game/'StarDynasties_Data').mkdir()
        nested=game/'nested repo'
        nested.mkdir()
        for root in (game,nested):
            with self.assertRaisesRegex(Error,'somente leitura'):
                Store(root)
            command=subprocess.run([sys.executable,str(PROJECT/'translation-work/toolkit.py'),'--repo',str(root),'status'],capture_output=True,encoding='utf-8')
            self.assertEqual(command.returncode,1)
            self.assertTrue(command.stderr.startswith('ERRO:'))
            self.assertNotIn('Traceback',command.stderr)
            self.assertFalse((root/'translation-work').exists())

    def test_runtime_blocker_cannot_be_bypassed_by_complete_jsonl(self):
        self.initialize()
        self.apply_payload(self.payload())
        profile=self.root/'translation-work/runtime-support.json'
        profile.write_bytes(encoded({'schema':1,'deployable':False,'blockers':['synthetic grammar blocker']}))
        with self.tool.store.lock():
            with self.assertRaisesRegex(Error,'motor'):
                self.tool.build()
        self.assertFalse((self.root/'PTBR').exists())

    def test_gc_removes_only_eligible_after_crash_and_keeps_recovery(self):
        self.initialize()
        path='translation-work/reports/small.json'
        self.tool.store.policy['max_completed']=3
        with self.tool.store.lock():
            for i in range(10):
                self.tool.store.transact({path:str(i).encode()},{path:file_hash(self.root,path)},'test')
            self.assertLessEqual(len(self.tool.store.inventory()),3)
            with self.assertRaises(RuntimeError):
                self.tool.store.transact({path:b'interrupted'},{path:digest(b'9')},'test',fail_after=1)
            with self.assertRaises(Error):
                self.tool.store.gc(dry_run=False)
            self.tool.store.recover()
            self.assertEqual(read(self.root,path),b'9')
            # Pending rollback/recovery already finished; eligible completed records can be pruned.
            before=self.snapshot()
            plan=self.tool.store.gc(dry_run=True)
            self.assertEqual(before,self.snapshot())
            self.assertTrue(plan['eligible'])
            self.tool.store.gc(dry_run=False)
            self.assertEqual(read(self.root,path),b'9')

    def test_interrupted_multifile_recovery_gc_and_rollback(self):
        self.initialize()
        paths = ['translation-work/reports/a.json','translation-work/reports/b.json']
        with self.tool.store.lock():
            self.tool.store.transact({p:b'old' for p in paths}, {p:None for p in paths}, 'test')
            with self.assertRaises(RuntimeError):
                self.tool.store.transact({p:b'new' for p in paths}, {p:digest(b'old') for p in paths}, 'test', fail_after=1)
            before = self.snapshot()
            with self.assertRaises(Error):
                self.tool.store.gc(dry_run=False)
            self.assertEqual(before, self.snapshot())
            self.assertTrue(self.tool.store.recover())
            self.assertEqual([read(self.root,p) for p in paths],[b'old',b'old'])
            self.tool.store.transact({p:b'new' for p in paths}, {p:digest(b'old') for p in paths}, 'test')
            self.tool.store.rollback()
        self.assertEqual([read(self.root,p) for p in paths],[b'old',b'old'])

    def test_staging_crash_recovers_without_accepted_loss(self):
        self.initialize()
        path='translation-work/reports/crash.json'
        actual = storage.write_atomic
        def broken(target, data):
            if target.name.endswith('.after'):
                raise OSError('simulated disk error during staging')
            return actual(target,data)
        with self.tool.store.lock():
            with patch('storage.write_atomic',side_effect=broken):
                with self.assertRaises(OSError):
                    self.tool.store.transact({path:b'test'}, {path:None}, 'test')
            self.assertTrue(self.tool.store.recover())
        self.assertIsNone(read(self.root,path))
        self.tool.check()

    def test_gc_refuses_corrupt_receipt_unknown_file_and_low_disk(self):
        self.initialize()
        directory=next(self.tool.store.transactions.iterdir())
        receipt=directory/'receipt.json'
        previous=receipt.read_bytes()
        receipt.write_bytes(b'{bad}')
        with self.assertRaises(Error):
            self.tool.store.gc(dry_run=True)
        receipt.write_bytes(previous)
        rogue=directory/'user-file.txt'
        rogue.write_text('never remove me')
        with self.assertRaises(Error):
            self.tool.store.gc(dry_run=True)
        self.assertTrue(rogue.exists())
        rogue.unlink()
        with self.tool.store.lock(), patch('storage.shutil.disk_usage',return_value=type('Disk',(),{'free':1})()):
            with self.assertRaisesRegex(Error,'Espaço'):
                self.tool.store.transact({'translation-work/reports/x.json':b'x'}, {'translation-work/reports/x.json':None},'test')

    def test_storage_scale_100_batches_500_tiny_applies(self):
        # Actual 500-record batches, not 100 artificially empty files.
        self.initialize(sources(50000), batch_size=500)
        manifest=self.tool.load_manifest()
        self.assertGreaterEqual(len(manifest['batches']),100)
        self.tool.store.policy.update(max_completed=5,max_bytes=4*1024*1024)
        name='batch-0001.jsonl'
        record=next(r for r in self.tool.load_batch(name,manifest) if r['source_file']=='Config/text.csv')
        untouched={n:(read(self.root,TRANSLATIONS+n), (self.root/TRANSLATIONS/n).stat().st_mtime_ns)
                   for n in manifest['batches'] if n!=name}
        for iteration in range(500):
            payload={'generation':manifest['generation'],'expected_count':1,'entries':[
                {'batch':name,'id':record['id'],'source_sha256':record['source_sha256'],
                 'PTBR':f'Synthetic review {iteration} for {{Actor}}'}]}
            self.apply_payload(payload,replace=True)
            latest=self.tool.store.inventory()[-1]
            receipt=self.tool.store.receipt(self.tool.store.transactions/latest['id'])
            self.assertEqual({x['path'] for x in receipt['changes']},{TRANSLATIONS+name,MANIFEST})
        for n,(data,mtime) in untouched.items():
            self.assertEqual(read(self.root,TRANSLATIONS+n),data)
            self.assertEqual((self.root/TRANSLATIONS/n).stat().st_mtime_ns,mtime)
        inventory=self.tool.store.inventory()
        self.assertLessEqual(len(inventory),5)
        total=sum(x['bytes'] for x in inventory)
        self.assertLessEqual(total,4*1024*1024)
        final=next(r for r in self.tool.load_batch(name,self.tool.load_manifest()) if r['id']==record['id'])
        self.assertIn('499',final['PTBR'])
        print(f'\nSCALE: 500 applies / {len(manifest["batches"])} batches / {len(inventory)} snapshots / {total} bytes retained')


class RealResources(unittest.TestCase):
    def test_all_real_sources_lossless_and_license(self):
        manifest=Toolkit(PROJECT).load_manifest()
        self.assertTrue(manifest['sources'])
        for path,meta in manifest['sources'].items():
            raw=(PROJECT/'EN'/path).read_bytes()
            self.assertEqual(digest(raw),meta['sha256'])
            self.assertEqual(Document(path,raw).render({}),raw)
        status=Toolkit(PROJECT).check()
        self.assertEqual(status['records'],manifest['record_count'])
        self.assertGreaterEqual(status['translated'],0)
        self.assertLessEqual(status['translated'],status['records'])
        license_text=(PROJECT/'LICENSE').read_bytes()
        self.assertEqual(digest(license_text),'e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd')
        self.assertGreater(len(license_text),20000)

    def test_public_readme_briefing_and_day_one_license(self):
        public=(PROJECT/'README.md').read_text(encoding='utf-8')
        current_count=f"{Toolkit(PROJECT).load_manifest()['record_count']:,}".replace(',','.')
        for required in ('1194590/header.jpg',current_count,'Bloodlines','PTBR.zip',
                         'StarDynasties.exe','English','restaur','pix@yuricunha.com','traducao.yuricunha.com',
                         '📜 Licença','./LICENSE','by-nc-sa/4.0','Yuri Cunha','Pawley Games','Iceberg Interactive'):
            self.assertIn(required.lower(),public.lower())
        for forbidden in ('TODO','INSERIR_LINK','100% traduzido','Bifrost','OpenAI'):
            self.assertNotIn(forbidden,public)
        self.assertNotIn('Ella',public)
        self.assertIn('pronomes',public)
        self.assertTrue(any(word in public.lower() for word in ('em preparação','em tradução','disponível')))
        briefing=(PROJECT/'translation-work/docs/briefing-do-jogo.md').read_text(encoding='utf-8')
        self.assertGreater(len(briefing),10000)
        self.assertIn('Link.collapse',briefing)
        self.assertIn('https://gpawley.itch.io/star-dynasties',briefing)


class FakeGitHub:
    """In-memory GitHub server. No network, credentials or real repository writes."""
    def __init__(self,root,sha):
        self.root=root
        self.sha=sha
        self.release=None
        self.tags={}
        self.calls=[]
        self.fail_upload=False
        self.stale=False
        self.checks=0

    def endpoint(self,suffix):
        return suffix

    def assert_current(self,sha):
        self.checks+=1
        if self.stale or sha!=self.sha:
            raise Error('stale default branch')

    def releases(self):
        return [copy.deepcopy(self.release)] if self.release else []

    def request(self,method,endpoint,payload=None,raw=None,missing=False):
        self.calls.append((method,endpoint))
        if endpoint.startswith('git/ref/tags/'):
            tag=endpoint.split('/')[-1]
            return {'object':{'type':'commit','sha':self.tags[tag]}} if tag in self.tags else None
        if method=='POST' and endpoint=='git/refs':
            tag=payload['ref'].split('/')[-1]
            if tag in self.tags:
                raise Error('ref already reserved')
            self.tags[tag]=payload['sha']
            release.git(self.root,'tag',tag,payload['sha'])
            return {'ref':payload['ref']}
        if endpoint.startswith('releases/tags/'):
            return copy.deepcopy(self.release)
        if method=='POST' and endpoint=='releases':
            self.release={**payload,'id':1,'upload_url':'https://uploads.github.com/synthetic/assets{?name}',
                          'assets':[],'published_at':None,'html_url':'https://github.com/synthetic/release'}
            return copy.deepcopy(self.release)
        if method=='GET' and endpoint=='releases/1/assets':
            return copy.deepcopy(self.release['assets'])
        if method=='POST' and endpoint.startswith('https://uploads.github.com/'):
            if self.fail_upload:
                self.fail_upload=False
                raise Error('simulated upload interruption')
            asset={'name':'PTBR.zip','state':'uploaded','size':len(raw),'digest':'sha256:'+digest(raw)}
            self.release['assets'].append(asset)
            return copy.deepcopy(asset)
        if method=='PATCH' and endpoint=='releases/1':
            self.release.update(payload)
            self.release['published_at']='2026-10-23T12:00:00Z'
            return copy.deepcopy(self.release)
        if method=='GET' and endpoint=='releases/1':
            return copy.deepcopy(self.release)
        raise AssertionError((method,endpoint))


class ReleaseTests(Fixture):
    def prepare_git(self):
        self.initialize()
        self.complete()
        for args in [('init','-b','main'),('config','core.autocrlf','false'),('config','user.email','fixture@example.invalid'),('config','user.name','Synthetic test')]:
            release.git(self.root,*args)
        return self.commit()

    def commit(self):
        release.git(self.root,'add','EN','PTBR','translation-work/translations','translation-work/source-catalog.json','translation-work/reports','translation-work/runtime-support.json')
        release.git(self.root,'commit','-m','Synthetic fixture')
        return release.revision(self.root,'HEAD')

    def release_fixture(self,tag='v1.0.0'):
        return {'tag_name':tag,'draft':False,'prerelease':False,'published_at':'2026-01-01T00:00:00Z','assets':[]}

    def test_first_next_identical_and_real_changelog(self):
        sha=self.prepare_git()
        plan=release.plan(self.root,sha,[])
        self.assertEqual(plan['tag'],'v1.0.0')
        self.assertTrue(plan['publish'])
        release.git(self.root,'tag','v1.0.0')
        self.assertFalse(release.plan(self.root,sha,[self.release_fixture()])['publish'])
        identity=next(r['id'] for r in self.all().values() if r['source_file']=='Core/Events.csv' and '{' not in r['EN'])
        self.apply_payload(self.payload([identity],'Synthetic reviewed string'),replace=True)
        with self.tool.store.lock():
            self.tool.build()
        sha=self.commit()
        plan=release.plan(self.root,sha,[self.release_fixture()])
        self.assertEqual(plan['tag'],'v1.0.1')
        self.assertEqual(plan['counts']['modified'],1)
        self.assertIn('Core/Events.csv',plan['changed_files'])
        self.assertIn('/compare/v1.0.0...',plan['notes'])

    def test_publish_creates_release_asset_exact_tag_and_retry_skips(self):
        sha=self.prepare_git()
        api=FakeGitHub(self.root,sha)
        result=release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertEqual(result['status'],'published')
        self.assertEqual(api.tags['v1.0.0'],sha)
        self.assertFalse(api.release['draft'])
        self.assertEqual(api.release['assets'][0]['name'],'PTBR.zip')
        self.assertGreaterEqual(api.checks,3)
        result=release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertEqual(result['status'],'skipped')
        self.assertEqual(len(api.tags),1)
        self.assertEqual(len(api.release['assets']),1)

    def test_publish_interruption_resumes_same_draft_and_version(self):
        sha=self.prepare_git()
        api=FakeGitHub(self.root,sha)
        api.fail_upload=True
        with self.assertRaisesRegex(Error,'interruption'):
            release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertTrue(api.release['draft'])
        self.assertEqual(api.tags['v1.0.0'],sha)
        result=release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertEqual(result['tag'],'v1.0.0')
        self.assertEqual(result['status'],'published')
        self.assertEqual(len(api.tags),1)

    def test_publish_stale_or_remote_tag_conflict_fails_closed(self):
        sha=self.prepare_git()
        api=FakeGitHub(self.root,sha)
        api.stale=True
        with self.assertRaisesRegex(Error,'stale'):
            release.publish(self.root,release.CANONICAL_REPO,sha,api)
        api.stale=False
        api.tags['v1.0.0']='1'*40
        with self.assertRaisesRegex(Error,'outro commit'):
            release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertIsNone(api.release)
        api.tags={}
        with patch.object(api,'assert_current',side_effect=[None,Error('stale after packaging')]):
            with self.assertRaisesRegex(Error,'stale after packaging'):
                release.publish(self.root,release.CANONICAL_REPO,sha,api)
        self.assertEqual(api.tags,{})

    def test_no_native_translation_change_changelog_is_honest(self):
        sha=self.prepare_git()
        release.git(self.root,'tag','v1.0.0')
        source=self.root/'EN/Core/Events.csv'
        source.write_bytes(source.read_bytes()+b',\r\n')
        with self.tool.store.lock():
            self.tool.sync()
            self.tool.build()
        sha=self.commit()
        plan=release.plan(self.root,sha,[self.release_fixture()])
        self.assertEqual(plan['counts']['modified'],0)
        self.assertIn('sem alteração nas unidades',plan['notes'])

    def test_conflicting_next_tag_and_prereleases(self):
        sha=self.prepare_git()
        release.git(self.root,'tag','v1.0.0')
        first=self.release_fixture()
        identity=next(r['id'] for r in self.all().values() if r['source_file']=='Core/Events.csv' and '{' not in r['EN'])
        self.apply_payload(self.payload([identity],'Synthetic later string'),replace=True)
        with self.tool.store.lock():
            self.tool.build()
        sha=self.commit()
        release.git(self.root,'tag','v1.0.1','v1.0.0')
        with self.assertRaisesRegex(Error,'outro commit'):
            release.plan(self.root,sha,[first])
        self.assertEqual(release.stable_releases([first,{**first,'tag_name':'v9.0.0','prerelease':True}]),[first])

    def test_stale_nonancestor_conflicting_tags_and_missing_metadata(self):
        sha=self.prepare_git()
        with self.assertRaises(Error):
            release.plan(self.root,sha,[self.release_fixture('invalid')])
        with self.assertRaises(Error):
            release.plan(self.root,sha,[self.release_fixture('v9.0.0')])
        release.git(self.root,'tag','v1.0.0')
        release.git(self.root,'checkout','--orphan','divergent')
        release.git(self.root,'commit','--allow-empty','-m','Unrelated')
        other=release.revision(self.root,'HEAD')
        # Unrelated history is rejected even with a valid on-disk output.
        with self.assertRaises(Error):
            release.plan(self.root,other,[self.release_fixture()])
        release.git(self.root,'checkout','main')
        nativefile=self.root/'PTBR/Core/Events.csv'
        nativefile.write_bytes(b'changed')
        with self.assertRaises(Error):
            release.plan(self.root,sha,[])

    def test_zip_missing_empty_traversal_and_bad_hash(self):
        self.prepare_git()
        target=self.root/'translation-work/dist/PTBR.zip'
        with self.assertRaises((OSError,Error)):
            validate_zip(target,{'Config/text.csv':'bad'})
        target.parent.mkdir(parents=True)
        for names in ([],['../outside'],['PTBR/Config/text.csv'],['Config/text.csv','Config/text.csv']):
            with zipfile.ZipFile(target,'w') as archive:
                for name in names:
                    archive.writestr(name,b'test')
            with self.assertRaises(Error):
                validate_zip(target,{'Config/text.csv':'bad'})

    def test_workflow_paths_no_rebuild_and_actual_release_wiring(self):
        text=(PROJECT/'.github/workflows/release.yml').read_text()
        self.assertIn("paths: ['PTBR/**']",text)
        self.assertIn('workflow_dispatch:',text)
        self.assertIn('contents: write',text)
        self.assertIn('cancel-in-progress: false',text)
        self.assertIn('verify-output',text)
        self.assertIn('release.py publish',text)
        self.assertNotIn('toolkit.py build',text)
        self.assertNotIn('pull_request',text)


if __name__=='__main__':
    unittest.main()
