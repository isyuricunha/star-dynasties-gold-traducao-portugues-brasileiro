from __future__ import annotations

import base64
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from managed_codec import EMPTY, ManagedDocument, check_toolchain, command, invoke
from native import MANAGED_PATH, Document, Error, encoded, validate_record, validate_text
from storage import file_hash
from toolkit import Toolkit
from test_toolkit import Fixture, PROJECT, sources


def compile_harness(work):
    if os.name == 'nt':
        compiler=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        if not compiler.exists():raise AssertionError('Missing .NET Framework C# compiler')
    else:
        compiler=shutil.which('mcs')
        if not compiler:raise AssertionError('Missing Mono C# compiler (mono-devel)')
    library=PROJECT/'translation-work/vendor/mono-cecil-0.11.6/Mono.Cecil.dll'
    shutil.copyfile(library,work/'Mono.Cecil.dll')
    executable=work/'RuntimeTests.exe'
    build=subprocess.run([str(compiler),'/nologo','/optimize+','/target:exe','/out:'+str(executable),
                          '/reference:'+str(library),'/reference:System.Web.Extensions.dll',
                          str(PROJECT/'translation-work/tests/GrammarRuntimeTests.cs')],capture_output=True)
    if build.returncode:raise AssertionError(build.stdout.decode(errors='replace'))
    return executable


def harness_command(executable):
    return [str(executable)] if os.name == 'nt' else [shutil.which('mono'), str(executable)]


class PortableToolchainTests(unittest.TestCase):
    def test_pinned_files_survive_git_normalization_and_fresh_checkout(self):
        lock=json.loads((PROJECT/'translation-work/managed/toolchain.json').read_bytes())
        runtime=json.loads((PROJECT/'translation-work/runtime-support.json').read_bytes())
        paths={"translation-work/"+p for p in lock['files']}
        paths.update(runtime['adapter_files'])
        paths.update(['.gitattributes','translation-work/managed/toolchain.json','EN/Config/text.csv'])
        with tempfile.TemporaryDirectory(prefix='star git LF ') as folder:
            root=Path(folder)/'repository';root.mkdir()
            for name in paths:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(PROJECT/name,target)
            def git(*args):
                return subprocess.run(['git','-C',str(root),'-c','core.autocrlf=true',*args],
                                      check=True,capture_output=True).stdout
            git('init');git('add','.')
            exported=Path(folder)/'checkout'
            git('checkout-index','--all','--prefix='+exported.as_posix()+'/')
            for name in paths:
                self.assertEqual((root/name).read_bytes(),git('show',':'+name),name)
                self.assertEqual((root/name).read_bytes(),(exported/name).read_bytes(),name)
            with patch('managed_codec.HOME',exported/'translation-work'):
                check_toolchain()
                source=exported/'translation-work/managed/Launcher.cs'
                source.write_bytes(source.read_bytes()+b'// changed\n')
                with self.assertRaisesRegex(Error,'Launcher.cs'):
                    check_toolchain()


def markers(document):
    result = {}
    for u in document.units:
        context = u["context"]
        if context["empty_allowed"]:
            value = EMPTY
        else:
            value = "marker_" + context["role"].replace("-", "_") + "_çã"
            if context["argument"]:
                value += " {0} END"
        result[u["id"]] = value
    return result


class SyntaxTests(unittest.TestCase):
    def test_only_display_arguments_can_change(self):
        pairs = [
            ('{D(Actor,"Someone")}', '{D(Actor,"referência_çã")}'),
            ('{fb(Head,"Your house\'s team")}', '{fb(Head,"equipe_çã")}'),
            ('{if(isNull(Actor),"a person",Actor)}', '{if(isNull(Actor),"referência_çã",Actor)}'),
            ('{mf(Actor,"Sir","Lady")}', '{mf(Actor,"forma_a","forma_b")}'),
            ('{if(isVisible(Actor),concat("The child ",Actor),"")}', '{if(isVisible(Actor),concat("prefixo_çã ",Actor),"")}'),
        ]
        for original, target in pairs:
            validate_text(original, target)
        for original, target in [
            ('{fetch("General.Accept")}', '{fetch("General.Refuse")}'),
            ('{showVar(Actor,"ExperienceCount")}', '{showVar(Actor,"OtherKey")}'),
            ('{roleIcon("Technology")}', '{roleIcon("OtherKey")}'),
            ('{D(Actor,"Someone")}', '{D(OtherActor,"referência")}'),
            ('{fb(Actor,"Somebody")}', '{concat(Actor,"referência")}'),
            ('{if("T","yes","no")}', '{if("F","sim","não")}'),
            ('{D(Actor,"Someone")}', '{D(Actor,"{fetch(secret)}")}'),
        ]:
            with self.assertRaises(Error, msg=(original,target)):
                validate_text(original, target)


class ManagedTests(Fixture):
    @classmethod
    def setUpClass(cls):
        command()  # A real toolchain is required; never silently skip native-format verification.
        source = PROJECT / 'EN' / MANAGED_PATH
        if not source.exists():
            location = json.loads((PROJECT/'translation-work/.state/local-install.json').read_text(encoding='utf8'))['game_root']
            source = Path(location)/MANAGED_PATH
        cls.raw = source.read_bytes()
        cls.doc = ManagedDocument(MANAGED_PATH, cls.raw)

    def test_100_units_noop_and_immutable_roles(self):
        self.assertEqual(len(self.doc.units),100)
        self.assertEqual(self.doc.render({}),self.raw)
        self.assertEqual(len({u['id'] for u in self.doc.units}),100)
        self.assertFalse(self.doc.is_patched)
        self.assertEqual(self.doc.data['runtime'],'v2.0.50727')

    def test_real_dll_from_unrelated_directory_without_mono_path(self):
        environment=os.environ.copy()
        environment.pop('MONO_PATH',None)
        process=subprocess.run(command()+['inspect-stdin'],input=base64.b64encode(self.raw),
                               cwd=self.root,env=environment,capture_output=True)
        self.assertEqual(process.returncode,0,process.stderr.decode('utf-8-sig',errors='replace'))
        self.assertEqual(len(json.loads(process.stdout.decode('utf-8-sig'))['units']),100)

    def test_empty_input_reports_payload_error(self):
        with self.assertRaisesRegex(Error,'Assembly input is empty'):
            invoke('inspect-stdin',b'\n')

    def test_deterministic_reconstruction_and_full_value_reopen(self):
        values=markers(self.doc)
        first=self.doc.render(values)
        self.assertEqual(first,self.doc.render(values))
        rebuilt=ManagedDocument(MANAGED_PATH,first)
        self.assertTrue(rebuilt.is_patched)
        self.assertEqual({u['id']:u['EN'] for u in rebuilt.units},
                         {identity:('' if value==EMPTY else value) for identity,value in values.items()})
        self.assertEqual(self.doc.data['references'],rebuilt.data['references'])

    def test_empty_requires_explicit_suffix_marker_and_templates_are_safe(self):
        suffix=next(u for u in self.doc.units if u['context']['empty_allowed'])
        pronoun=next(u for u in self.doc.units if '::he(' in u['key'])
        template=next(u for u in self.doc.units if u['context']['argument'])
        validate_record(suffix,EMPTY)
        for unit,value in [(suffix,''),(pronoun,EMPTY),(template,'missing reference'),
                           (template,'{0} {0}'),(template,'{0} {OtherActor}')]:
            with self.assertRaises(Error):
                validate_record(unit,value)
        with self.assertRaises(Error):
            self.doc.render({'unknown':'value'})

    def test_unknown_method_structure_fails_closed(self):
        changed=copy.deepcopy(self.doc.data)
        changed['method_shapes'][next(iter(changed['method_shapes']))]='unknown'
        with patch('managed_codec.inspect',return_value=changed):
            with self.assertRaisesRegex(Error,'estrutura'):
                ManagedDocument(MANAGED_PATH,self.raw)

    def test_import_dryrun_append_and_single_entry_change_preserve_work(self):
        files=sources()
        self.initialize(files,batch_size=500)
        self.apply_payload(self.payload())
        before=self.all()
        previous_assignments=self.tool.load_all(self.tool.load_manifest())[1]
        candidate={**files,MANAGED_PATH:self.raw}
        old_state=self.snapshot()
        result=self.tool.synchronize(candidate,dry_run=True)
        self.assertEqual(result['counts']['added'],100)
        self.assertEqual(self.snapshot(),old_state)
        with self.tool.store.lock():
            result=self.tool.synchronize(candidate)
        self.assertEqual(result['counts']['preserved_translations'],len(before))
        after,assignments=self.tool.load_all(self.tool.load_manifest())
        for identity,record in before.items():
            self.assertEqual(after[identity],record)
            self.assertEqual(assignments[identity],previous_assignments[identity])
        self.assertEqual(read_bytes(self.root/'EN'/MANAGED_PATH),self.raw)
        self.assertFalse((self.root/'PTBR').exists())
        self.assertEqual(self.tool.check()['pending'],100)

    def test_complete_fixture_build_zip_and_fast_gate_need_no_clr(self):
        self.initialize({**sources(),MANAGED_PATH:self.raw})
        values=markers(self.doc)
        payload=self.payload()
        for entry in payload['entries']:
            if entry['id'] in values:entry['PTBR']=values[entry['id']]
        self.apply_payload(payload)
        with self.tool.store.lock():self.tool.build()
        with patch('managed_codec.command',side_effect=AssertionError('fast gate must not run CLR')):
            result=self.tool.verify_output()
            self.assertIn(MANAGED_PATH,result['files'])
            self.tool.package(self.root/'translation-work/dist/PTBR.zip')
        import zipfile
        with zipfile.ZipFile(self.root/'translation-work/dist/PTBR.zip') as archive:
            self.assertIn(MANAGED_PATH,archive.namelist())
            self.assertFalse(any('Mono.Cecil' in name or 'GrammarTool' in name or name.endswith('.md') for name in archive.namelist()))
        output=self.root/'PTBR'/MANAGED_PATH
        output.write_bytes(output.read_bytes()+b'TAMPER')
        with self.assertRaises(Error):self.tool.verify_output()

    def test_existing_localized_binary_is_not_an_original_source(self):
        native=self.doc.render(markers(self.doc))
        with self.tool.store.lock():
            with self.assertRaisesRegex(Error,'já localizada'):
                self.tool.synchronize({**sources(),MANAGED_PATH:native})
        self.assertFalse((self.root/'EN').exists())

    def test_adapter_fingerprints_block_changed_engineering_files(self):
        self.initialize(sources())
        self.apply_payload(self.payload())
        adapter = self.root/'translation-work/adapter-fixture.cs'
        adapter.write_bytes(b'accepted adapter fixture')
        profile = self.root/'translation-work/runtime-support.json'
        profile.write_bytes(encoded({'schema': 1, 'deployable': True, 'blockers': [],
                                    'adapter_files': {'translation-work/adapter-fixture.cs':
                                                      file_hash(self.root, 'translation-work/adapter-fixture.cs')}}))
        with self.tool.store.lock():
            self.tool.build()
        with patch('managed_codec.command', side_effect=AssertionError('fast gate must not run CLR')):
            self.tool.verify_output()
            adapter.write_bytes(b'changed adapter fixture')
            with self.assertRaisesRegex(Error, 'revalidação'):
                self.tool.verify_output()
            with self.tool.store.lock():
                with self.assertRaisesRegex(Error, 'revalidação'):
                    self.tool.build()
        adapter.write_bytes(b'accepted adapter fixture')
        configuration = json.loads(profile.read_bytes())
        configuration['required_sources'] = [MANAGED_PATH]
        profile.write_bytes(encoded(configuration))
        with self.tool.store.lock():
            with self.assertRaisesRegex(Error, 'Fonte obrigatória'):
                self.tool.build()

    def test_real_engine_runtime_with_controlled_environment(self):
        local_file=PROJECT/'translation-work/.state/local-install.json'
        if not local_file.is_file():
            self.skipTest('Real-engine execution requires read-only game dependencies in .state/local-install.json')
        work=self.root/'runtime-test'
        work.mkdir()
        executable=compile_harness(work)
        values=markers(self.doc)
        binary=work/'marker-engine.dll'
        binary.write_bytes(self.doc.render(values))
        expected=work/'expected.json'
        expected.write_bytes(encoded({u['key']:('' if values[u['id']]==EMPTY else values[u['id']]) for u in self.doc.units}))
        local=json.loads(local_file.read_text(encoding='utf8'))
        dependencies=Path(local['game_root'])/'StarDynasties_Data/Managed'
        process=subprocess.run(harness_command(executable)+[str(binary),str(work/'runtime-fixture.dll'),str(dependencies),str(expected)],capture_output=True)
        self.assertEqual(process.returncode,0,process.stderr.decode('utf8',errors='replace'))
        result=json.loads(process.stdout.decode('utf-8-sig'))
        self.assertGreaterEqual(result['runtime_checks'],111)
        self.assertTrue(result['clickable_context_preserved'])
        self.assertTrue(result['native_quoted_arguments_tested'])

    def test_one_dll_source_literal_invalidates_only_its_unit(self):
        self.initialize({**sources(),MANAGED_PATH:self.raw})
        payload=self.payload()
        values=markers(self.doc)
        for entry in payload['entries']:
            if entry['id'] in values:entry['PTBR']=values[entry['id']]
        self.apply_payload(payload)
        before=self.all()
        work=self.root/'source-update-test'
        work.mkdir()
        executable=compile_harness(work)
        original=work/'original.dll';original.write_bytes(self.raw)
        changed=work/'changed.dll'
        process=subprocess.run(harness_command(executable)+['source-change',str(original),str(changed)],capture_output=True)
        self.assertEqual(process.returncode,0,process.stderr.decode(errors='replace'))
        with self.tool.store.lock():result=self.tool.synchronize({**sources(),MANAGED_PATH:changed.read_bytes()})
        self.assertEqual(result['counts']['modified'],1)
        self.assertEqual(result['counts']['preserved_translations'],len(before)-1)
        after=self.all()
        invalidated=[r for r in after.values() if not r['PTBR']]
        self.assertEqual(len(invalidated),1)
        self.assertEqual(invalidated[0]['EN'],'changed-source-female')
        self.assertEqual(invalidated[0]['history'][-1]['PTBR'],before[invalidated[0]['id']]['PTBR'])


def read_bytes(path):
    return path.read_bytes()


if __name__=='__main__':unittest.main()
