#!/usr/bin/env python3
"""Manual PT-BR localization workspace. Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from native import CONFIG, NON_TEXT, Document, Error, digest, encoded, fingerprint, safe_relative, validate_text
from storage import Store, file_hash, read, safe_path, write_atomic

WORK = "translation-work/"
TRANSLATIONS = WORK + "translations/"
MANIFEST = TRANSLATIONS + "manifest.json"
CATALOG = WORK + "source-catalog.json"
BUILD = WORK + "reports/build-manifest.json"
RUNTIME = WORK + "runtime-support.json"
BATCH_PATTERN = re.compile(r"batch-\d{4,}\.jsonl\Z")


def jsonl(records):
    return b"".join((json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8") for x in records)


def parse_jsonl(data: bytes):
    try:
        lines = data.decode("utf-8").splitlines()
        result = [json.loads(x) for x in lines]
    except (UnicodeError, ValueError) as exc:
        raise Error(f"JSONL inválido: {exc}") from exc
    if not lines or any(not isinstance(x, dict) for x in result):
        raise Error("JSONL vazio ou registros não são objetos")
    return result


def original(record):
    return {k: v for k, v in record.items() if k not in ("PTBR", "history")}


def batch_meta(records, raw=None):
    return {"sha256": digest(raw if raw is not None else jsonl(records)), "count": len(records),
            "translated": sum(bool(x["PTBR"].strip()) for x in records),
            "original_sha256": fingerprint([original(x) for x in records])}


def discover(tree: Path):
    if not tree.is_dir() or tree.is_symlink():
        raise Error(f"Árvore de recursos inválida: {tree}")
    files = {}
    for folder in ("Config", "Core", "BloodlinesDLC"):
        directory = safe_path(tree, folder)
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.csv")):
            relative = path.relative_to(tree).as_posix()
            if folder == "Config" and path.name not in CONFIG:
                if path.name in NON_TEXT:
                    continue
                raise Error(f"CSV Config desconhecido; classifique antes de importar: {relative}")
            raw = read(tree, relative)
            Document(relative, raw)
            files[relative] = raw
    if not files or "Config/text.csv" not in files:
        raise Error("Árvore incompleta: Config/text.csv ausente; informe a raiz do jogo/EN")
    folded = [x.casefold() for x in files]
    if len(folded) != len(set(folded)):
        raise Error("Colisão de caminhos sem distinção de maiúsculas")
    return files


class Toolkit:
    def __init__(self, root: Path):
        self.root = root.absolute()
        self.store = Store(self.root)

    def load_manifest(self):
        data = read(self.root, MANIFEST)
        if data is None:
            raise Error("Workspace não extraído. Execute update-sources --game-root CAMINHO")
        try:
            manifest = json.loads(data)
            if manifest["schema"] != 1 or manifest["game"] != "Star Dynasties":
                raise Error("Manifesto de outro jogo/esquema")
            if manifest["generation"] != fingerprint(manifest["sources"]):
                raise Error("Geração de fontes inconsistente")
            for path in manifest["sources"]:
                safe_relative(path)
            for batch in manifest["batches"]:
                if not BATCH_PATTERN.fullmatch(batch):
                    raise Error("Nome de batch inválido")
        except (ValueError, KeyError, TypeError) as exc:
            raise Error("Manifesto inválido") from exc
        return manifest

    def load_batch(self, name, manifest):
        if name not in manifest["batches"]:
            raise Error(f"Batch desconhecido: {name}")
        raw = read(self.root, TRANSLATIONS + name)
        if raw is None:
            raise Error(f"Batch ausente: {name}")
        records = parse_jsonl(raw)
        if any(not isinstance(x.get("PTBR"), str) or not isinstance(x.get("history"), list) for x in records):
            raise Error(f"Tipos inválidos em {name}")
        meta = batch_meta(records, raw)
        if meta != manifest["batches"][name]:
            raise Error(f"Batch editado fora de apply/corrompido: {name}; restaure ou use um payload apply")
        if any(set(x) != {"id", "source_file", "key", "locator", "row", "column", "EN", "context", "source_sha256", "PTBR", "history"} for x in records):
            raise Error(f"Campos inválidos em {name}")
        for record in records:
            if not isinstance(record["PTBR"], str) or not isinstance(record["history"], list):
                raise Error(f"Tipos inválidos em {name}")
        return records

    def load_all(self, manifest):
        records, assignments = {}, {}
        directory = safe_path(self.root, TRANSLATIONS.rstrip("/"))
        actual = {x.name for x in directory.glob("batch-*.jsonl")}
        if actual != set(manifest["batches"]):
            raise Error("Inventário de batches divergente")
        for name in sorted(manifest["batches"]):
            batch = self.load_batch(name, manifest)
            if len(batch) > manifest["batch_size"]:
                raise Error("Batch excede tamanho configurado")
            for record in batch:
                if record["id"] in records:
                    raise Error(f"ID duplicado: {record['id']}")
                records[record["id"]] = record
                assignments[record["id"]] = name
        if len(records) != manifest["record_count"]:
            raise Error("Contagem do manifesto divergente")
        return records, assignments

    def catalog(self, manifest):
        raw = read(self.root, CATALOG)
        if raw is None or digest(raw) != manifest["catalog_sha256"]:
            raise Error("Catálogo aceito ausente/corrompido; restaure do Git")
        catalog = json.loads(raw)
        if catalog["generation"] != manifest["generation"]:
            raise Error("Catálogo de outra geração")
        return catalog

    def assert_sources(self, manifest):
        files = discover(safe_path(self.root, "EN"))
        if {p: digest(v) for p, v in files.items()} != {p: x["sha256"] for p, x in manifest["sources"].items()}:
            raise Error("EN mudou desde a geração aceita; execute sync antes de continuar")
        return files

    def verified_installation(self, game_root: Path):
        # Only distribution fingerprints reviewed in this repository are trusted.
        game_root = game_root.absolute()
        if game_root.resolve().is_relative_to(self.root.resolve()) or self.root.resolve().is_relative_to(game_root.resolve()):
            raise Error("Instalação e repositório não podem se sobrepor")
        profiles = json.loads(read(self.root, WORK + "trusted-distributions.json"))["distributions"]
        files = discover(game_root)
        hashes = {p: digest(v) for p, v in files.items()}
        matches = []
        for profile in profiles:
            if hashes == profile["files"] and all(file_hash(game_root, p) == h for p, h in profile["identity"].items()):
                matches.append(profile)
        if len(matches) != 1:
            raise Error("Instalação desconhecida, incompleta ou modificada. Os hashes não correspondem a um original revisado; "
                        "use inspect-source e revise trusted-distributions.json. Não importe uma instalação já traduzida.")
        return files, matches[0]

    def autodetect(self):
        candidates = set()
        local = read(self.root, WORK + ".state/local-install.json")
        if local:
            candidates.add(json.loads(local)["game_root"])
        if os.name == "nt":
            try:
                import winreg
                for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    for branch in (r"SOFTWARE\GOG.com\Games\1177048612", r"SOFTWARE\WOW6432Node\GOG.com\Games\1177048612"):
                        try:
                            with winreg.OpenKey(hive, branch) as key:
                                candidates.add(winreg.QueryValueEx(key, "path")[0])
                        except OSError:
                            pass
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
                    steam = Path(winreg.QueryValueEx(key, "SteamPath")[0])
                    libraries = [steam]
                    vdf = steam / "steamapps/libraryfolders.vdf"
                    if vdf.is_file():
                        libraries += [Path(x.replace("\\\\", "\\")) for x in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8"))]
                    for library in libraries:
                        acf = library / "steamapps/appmanifest_1194590.acf"
                        if acf.is_file():
                            match = re.search(r'"installdir"\s+"([^"]+)"', acf.read_text(encoding="utf-8"))
                            if match and "/" not in match[1] and "\\" not in match[1] and match[1] not in (".", ".."):
                                candidates.add(str(library / "steamapps/common" / match[1]))
            except (OSError, ImportError):
                pass
            # Known bounded GOG locations; contents must still pass the exact distribution proof.
            candidates.update((r"D:\GOG Games\Star Dynasties", r"C:\GOG Games\Star Dynasties"))
        valid = {}
        for candidate in candidates:
            try:
                self.verified_installation(Path(candidate))
                valid[str(Path(candidate).resolve())] = Path(candidate)
            except (Error, OSError):
                continue
        if len(valid) != 1:
            raise Error("Nenhuma instalação original única acessível. Use: python translation-work/toolkit.py "
                        "update-sources --game-root \"CAMINHO/Star Dynasties\"")
        return next(iter(valid.values()))

    def update_sources(self, game_root=None, dry_run=False, batch_size=500):
        location = Path(game_root) if game_root else self.autodetect()
        files, profile = self.verified_installation(location)
        result = self.synchronize(files, dry_run=dry_run, batch_size=batch_size,
                                  version=profile["version"], installation=location)
        return {"game_root": str(location), "version": profile["version"], **result}

    def sync(self, input_path=None, source_file=None, allow_remove=(), dry_run=False, batch_size=500):
        en = safe_path(self.root, "EN")
        if input_path:
            incoming = Path(input_path).absolute()
            if incoming.is_symlink() or (hasattr(incoming, "is_junction") and incoming.is_junction()):
                raise Error("Fonte é link/junction")
            if incoming.is_file():
                if not source_file:
                    raise Error("Importação de arquivo exige --source-file Core/Nome.csv (sem adivinhar caminhos)")
                files = discover(en)
                Document(source_file, incoming.read_bytes())
                files[source_file] = incoming.read_bytes()
            else:
                if incoming.resolve() == self.root.resolve():
                    raise Error("Informe EN ou a raiz da árvore nativa, não a raiz do repo")
                files = discover(incoming)
        else:
            files = discover(en)
        return self.synchronize(files, dry_run=dry_run, batch_size=batch_size, allow_remove=allow_remove)

    def synchronize(self, files, dry_run=False, batch_size=500, allow_remove=(), version=None, installation=None):
        self.store.clean()
        if not 1 <= batch_size <= 10000:
            raise Error("batch-size deve estar entre 1 e 10000")
        initial = read(self.root, MANIFEST) is None
        previous = None if initial else self.load_manifest()
        before_manifest_hash = digest(encoded(previous)) if previous else None
        observed_en = {"EN/" + p: file_hash(self.root, "EN/" + p) for p in files.keys() | (previous["sources"].keys() if previous else set())}
        old_records, assignments = ({}, {}) if initial else self.load_all(previous)
        old_catalog = None if initial else self.catalog(previous)
        if previous:
            batch_size = previous["batch_size"]
        removed_files = set(previous["sources"] if previous else ()) - files.keys()
        if removed_files != set(allow_remove):
            if removed_files or allow_remove:
                raise Error(f"Cópia incompleta/remoção não autorizada: {sorted(removed_files)}. "
                            "Para remoção intencional, liste exatamente --allow-remove CAMINHO")
        required = {"Config/text.csv", "Config/tutorial.csv", "Config/pedia.csv"}
        if not required <= files.keys():
            raise Error(f"Fontes essenciais ausentes: {sorted(required - files.keys())}")
        if old_catalog and "Config/terms.csv" in files and previous["sources"].get("Config/terms.csv", {}).get("sha256") != digest(files["Config/terms.csv"]):
            raise Error("Config/terms.csv mudou: chaves nativas ausentes tornam o remapeamento ambíguo; revisão do parser necessária")
        sources, units = {}, {}
        documents = {}
        for path, raw in sorted(files.items()):
            doc = Document(path, raw)
            documents[path] = doc
            if doc.render({}) != raw:
                raise Error(f"Round-trip não é lossless: {path}")
            sources[path] = {"sha256": digest(raw), "bytes": len(raw), "records": len(doc.units), "encoding": "utf-8-bom" if doc.bom else "utf-8"}
            for unit in doc.units:
                if unit["id"] in units:
                    raise Error("ID nativo duplicado")
                units[unit["id"]] = unit
        generation = fingerprint(sources)
        source_unchanged = bool(previous and previous["sources"] == sources)
        if source_unchanged and old_catalog and "native" in old_catalog:
            return {"status": "unchanged", "generation": generation, "files": len(files), "records": len(units)}
        if old_catalog and {x["id"]: x for x in old_catalog["records"]} != {k: original(v) for k, v in old_records.items()}:
            raise Error("Catálogo anterior e campos imutáveis dos batches divergiram")
        current, details, counts = {}, [], Counter()
        for identity, unit in units.items():
            old = old_records.get(identity)
            record = {**unit, "PTBR": "", "history": []}
            if old is None:
                classification = "added"
            elif old["source_sha256"] != unit["source_sha256"]:
                classification = "modified"
                record["history"] = (old["history"] + [{"generation": previous["generation"], "EN": old["EN"],
                                                        "PTBR": old["PTBR"], "source_sha256": old["source_sha256"], "reason": "source/context changed"}])[-3:]
            else:
                record["PTBR"] = old["PTBR"]
                record["history"] = old["history"]
                classification = "reordered" if old["row"] != unit["row"] else "unchanged"
                if old["PTBR"]:
                    counts["preserved_translations"] += 1
            counts[classification] += 1
            if classification != "unchanged":
                details.append({"classification": classification, "id": identity, "source_file": unit["source_file"],
                                "previous_EN": old["EN"] if old else None, "EN": unit["EN"],
                                "previous_PTBR": old["PTBR"] if old else None, "batch": assignments.get(identity)})
            current[identity] = record
        for identity in old_records.keys() - current.keys():
            old = old_records[identity]
            counts["removed"] += 1
            details.append({"classification": "removed", "id": identity, "source_file": old["source_file"],
                            "previous_EN": old["EN"], "EN": None, "previous_PTBR": old["PTBR"], "batch": assignments[identity], "previous_record": old})
        batches = {name: [] for name in (previous["batches"] if previous else {})}
        # Existing membership/order remain stable; never repack holes in older batches.
        for identity in old_records:
            if identity in current:
                batches[assignments[identity]].append(current[identity])
        names = sorted(batches)
        last = names[-1] if names else None
        next_number = int(last[6:-6]) + 1 if last else 1
        for identity in units:
            if identity in assignments:
                continue
            if last is None or len(batches[last]) >= batch_size:
                last = f"batch-{next_number:04d}.jsonl"
                next_number += 1
                batches[last] = []
            batches[last].append(current[identity])
            assignments[identity] = last
        batches = {k: v for k, v in batches.items() if v}
        for detail in details:
            detail["batch"] = assignments.get(detail["id"], detail["batch"])
        catalog = {"schema": 1, "generation": generation, "records": list(units.values()),
                   "native": {p: {"sha256": digest(raw), "base64": base64.b64encode(raw).decode("ascii")} for p, raw in files.items()}}
        catalog_raw = encoded(catalog)
        manifest = {"schema": 1, "game": "Star Dynasties", "source_language": "EN", "target_language": "pt-BR",
                    "version": version or (previous["version"] if source_unchanged else "manually supplied; version unverified"),
                    "generation": generation, "sources": sources, "catalog_sha256": digest(catalog_raw),
                    "batch_size": batch_size, "record_count": len(units),
                    "batches": {k: batch_meta(v) for k, v in sorted(batches.items())}}
        changed_files = {"added": sorted(files.keys() - (previous["sources"].keys() if previous else set())),
                         "removed": sorted(removed_files), "modified": sorted(p for p in files if previous and p in previous["sources"] and digest(files[p]) != previous["sources"][p]["sha256"])}
        changed_batches = [k for k in sorted(set(batches) | set(previous["batches"] if previous else ()))
                           if (previous["batches"].get(k) if previous else None) != manifest["batches"].get(k)]
        report = {"schema": 1, "status": "validated", "previous_generation": previous["generation"] if previous else None,
                  "generation": generation, "counts": dict(counts), "files": changed_files,
                  "batches": changed_batches, "existing_pending": sum(not r["PTBR"] for r in old_records.values()),
                  "pending": sum(not r["PTBR"] for r in current.values()),
                  "details": sorted(details, key=lambda x: (x["source_file"], x["id"])),
                  "warnings": ["Config/terms.csv usa slots fixos; alterações exigem revisão.", "Compatibilidade em execução não testada."],
                  "next": "Ella: revisar briefing, diff e batches pendentes. PTBR não foi alterado."}
        summary = {"status": "dry-run" if dry_run else "synchronized", "generation": generation, "files": len(files),
                   "records": len(units), "batches": len(batches), "counts": dict(counts), "changed_batches": changed_batches}
        if dry_run:
            return {**summary, "diff": report}
        changes = {"EN/" + p: raw for p, raw in files.items()}
        changes.update({"EN/" + p: None for p in removed_files})
        changes.update({TRANSLATIONS + name: jsonl(rows) for name, rows in batches.items()})
        changes.update({TRANSLATIONS + name: None for name in (previous["batches"] if previous else {}) if name not in batches})
        changes[CATALOG] = catalog_raw
        changes[MANIFEST] = encoded(manifest)
        changes[WORK + "reports/sync-latest.json"] = encoded(report)
        changes[WORK + "reports/sync-latest.md"] = ("# Última sincronização aceita\n\nGeração: `" + generation + "`\n\n" +
            "\n".join(f"- {key}: {value}" for key, value in sorted(counts.items())) +
            "\n\nIDs, textos anteriores, traduções históricas e batches: [sync-latest.json](./sync-latest.json).\n" +
            "Este relatório só corresponde à geração acima. Falhas posteriores não o substituem.\n").encode("utf-8")
        if installation:
            changes[WORK + ".state/local-install.json"] = encoded({"game_root": str(installation.absolute())})
        expected = {p: file_hash(self.root, p) for p in changes}
        expected.update(observed_en)
        expected[MANIFEST] = before_manifest_hash
        if previous:
            expected.update({TRANSLATIONS + k: v["sha256"] for k, v in previous["batches"].items()})
            expected[CATALOG] = previous["catalog_sha256"]
        transaction = self.store.transact(changes, expected, "sync")
        return {**summary, "transaction": transaction}

    def apply(self, payload, replace=False):
        self.store.clean()
        manifest = self.load_manifest()
        manifest_hash = digest(encoded(manifest))
        if not isinstance(payload, dict) or set(payload) != {"generation", "expected_count", "entries"}:
            raise Error("Payload exige generation, expected_count e entries")
        entries = payload["entries"]
        if not isinstance(entries, list) or type(payload["expected_count"]) is not int or payload["expected_count"] != len(entries):
            raise Error("expected_count divergente")
        if payload["generation"] != manifest["generation"]:
            raise Error("Payload de outra geração de fontes")
        seen, loaded, accepted, rejected = set(), {}, [], []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"batch", "id", "source_sha256", "PTBR"}:
                raise Error("Entrada exige apenas batch, id, source_sha256, PTBR")
            if not isinstance(entry["id"], str) or entry["id"] in seen:
                raise Error("ID duplicado/inválido no payload")
            seen.add(entry["id"])
        source_preconditions = {}
        for entry in entries:
            identity, name = entry["id"], entry["batch"]
            try:
                if not isinstance(name, str):
                    raise Error("Batch inválido")
                if name not in loaded:
                    loaded[name] = self.load_batch(name, manifest)
                matches = [r for r in loaded[name] if r["id"] == identity]
                if len(matches) != 1:
                    raise Error("ID desconhecido no batch informado")
                record = matches[0]
                if record["source_sha256"] != entry["source_sha256"]:
                    raise Error("Fingerprint da entrada divergente")
                source = "EN/" + record["source_file"]
                source_preconditions[source] = manifest["sources"][record["source_file"]]["sha256"]
                if file_hash(self.root, source) != source_preconditions[source]:
                    raise Error("Fonte mudou em EN; execute sync")
                validate_text(record["EN"], entry["PTBR"])
                if record["PTBR"] and record["PTBR"] != entry["PTBR"] and not replace:
                    raise Error("Tradução existente protegida; use --replace após revisão")
                if record["PTBR"] != entry["PTBR"]:
                    if record["PTBR"]:
                        record["history"] = (record["history"] + [{"generation": manifest["generation"], "EN": record["EN"], "PTBR": record["PTBR"], "source_sha256": record["source_sha256"], "reason": "explicit replacement"}])[-3:]
                    record["PTBR"] = entry["PTBR"]
                accepted.append(identity)
            except (Error, KeyError, TypeError) as exc:
                rejected.append({"id": identity, "reason": str(exc)})
        changes, expected = {}, {MANIFEST: manifest_hash, **source_preconditions}
        new_manifest = copy.deepcopy(manifest)
        for name, rows in loaded.items():
            meta = batch_meta(rows)
            if meta != manifest["batches"][name]:
                changes[TRANSLATIONS + name] = jsonl(rows)
                expected[TRANSLATIONS + name] = manifest["batches"][name]["sha256"]
                new_manifest["batches"][name] = meta
        if changes:
            changes[MANIFEST] = encoded(new_manifest)
        transaction = self.store.transact(changes, expected, "apply") if changes else None
        return {"accepted": accepted, "rejected": rejected, "transaction": transaction}

    def check(self, complete=False, deep=True):
        self.store.clean()
        manifest = self.load_manifest()
        records, _ = self.load_all(manifest)
        catalog = self.catalog(manifest)
        if {x["id"]: x for x in catalog["records"]} != {k: original(v) for k, v in records.items()}:
            raise Error("Campos originais divergiram do catálogo aceito")
        if deep:
            files = self.assert_sources(manifest)
            native_units = {u["id"]: u for p, raw in files.items() for u in Document(p, raw).units}
            if native_units != {k: original(v) for k, v in records.items()}:
                raise Error("Batches não correspondem às fontes nativas")
        else:
            # Fast output gate: hashes only, no native rebuild or CSV parse.
            for path, meta in manifest["sources"].items():
                if file_hash(self.root, "EN/" + path) != meta["sha256"]:
                    raise Error(f"Fonte stale: {path}")
            actual = self.source_names()
            if actual != set(manifest["sources"]):
                raise Error("Inventário de fontes divergente")
        for record in records.values():
            if record["PTBR"]:
                validate_text(record["EN"], record["PTBR"])
        translated = sum(bool(x["PTBR"].strip()) for x in records.values())
        if complete and translated != len(records):
            raise Error(f"Tradução incompleta: {translated}/{len(records)}; PTBR foi preservado")
        return {"valid": True, "generation": manifest["generation"], "records": len(records), "translated": translated,
                "pending": len(records) - translated, "batches": len(manifest["batches"])}

    def source_names(self):
        en = safe_path(self.root, "EN")
        names = set()
        for directory in ("Config", "Core", "BloodlinesDLC"):
            folder = safe_path(en, directory)
            if folder.exists():
                for path in folder.glob("*.csv"):
                    relative = path.relative_to(en).as_posix()
                    safe_path(en, relative)
                    # EN is exclusively managed: even extra numeric config files are unexpected.
                    names.add(relative)
        return names

    def build(self):
        self.check(complete=True)
        runtime_hash = self.runtime_gate()
        manifest = self.load_manifest()
        records, _ = self.load_all(manifest)
        by_file = {}
        for r in records.values():
            by_file.setdefault(r["source_file"], {})[r["id"]] = r["PTBR"]
        output = {}
        for path in manifest["sources"]:
            raw = read(self.root, "EN/" + path)
            rendered = Document(path, raw).render(by_file.get(path, {}))
            reopened = Document(path, rendered)
            values = {u["id"]: u["EN"] for u in reopened.units}
            if values != by_file.get(path, {}):
                raise Error(f"Valores reconstruídos divergentes: {path}")
            output[path] = rendered
        proof = {"schema": 1, "game": "Star Dynasties", "version": manifest["version"], "complete": True,
                 "source_generation": manifest["generation"], "manifest_sha256": file_hash(self.root, MANIFEST),
                 "catalog_sha256": manifest["catalog_sha256"], "records": len(records),
                 "runtime_support_sha256": runtime_hash,
                 "translation_fingerprint": fingerprint(manifest["batches"]),
                 "files": {p: digest(v) for p, v in output.items()}}
        proof["build_fingerprint"] = fingerprint(proof)
        changes = {"PTBR/" + p: raw for p, raw in output.items()}
        existing = self.output_files()
        changes.update({"PTBR/" + p: None for p in existing - output.keys()})
        changes[BUILD] = encoded(proof)
        expected = {p: file_hash(self.root, p) for p in changes}
        expected.update({MANIFEST: proof["manifest_sha256"], CATALOG: proof["catalog_sha256"]})
        expected[RUNTIME] = runtime_hash
        expected.update({TRANSLATIONS + k: v["sha256"] for k, v in manifest["batches"].items()})
        expected.update({"EN/" + k: v["sha256"] for k, v in manifest["sources"].items()})
        transaction = self.store.transact(changes, expected, "build")
        return {"status": "built", "files": len(output), "build_fingerprint": proof["build_fingerprint"], "transaction": transaction}

    def output_files(self):
        output = safe_path(self.root, "PTBR")
        result = set()
        if output.exists():
            for path in output.rglob("*"):
                relative = path.relative_to(output).as_posix()
                safe_path(output, relative)
                if path.is_file():
                    result.add(relative)
        return result

    def verify_output(self):
        status = self.check(complete=True, deep=False)
        runtime_hash = self.runtime_gate()
        manifest = self.load_manifest()
        raw = read(self.root, BUILD)
        if raw is None:
            raise Error("Build manifest ausente; execute build quando a tradução estiver completa")
        proof = json.loads(raw)
        expected_fingerprint = proof.pop("build_fingerprint", None)
        if expected_fingerprint != fingerprint(proof):
            raise Error("Build manifest adulterado")
        if (proof.get("schema") != 1 or proof.get("complete") is not True or
            proof.get("source_generation") != manifest["generation"] or proof.get("records") != status["records"] or
            proof.get("manifest_sha256") != file_hash(self.root, MANIFEST) or
            proof.get("catalog_sha256") != manifest["catalog_sha256"] or
            proof.get("runtime_support_sha256") != runtime_hash or
            proof.get("translation_fingerprint") != fingerprint(manifest["batches"])):
            raise Error("PTBR stale: fontes/traduções mudaram desde build")
        if not proof.get("files") or self.output_files() != set(proof["files"]) or set(proof["files"]) != set(manifest["sources"]):
            raise Error("Inventário PTBR ausente/divergente")
        for path, checksum in proof["files"].items():
            if file_hash(self.root, "PTBR/" + path) != checksum:
                raise Error(f"Saída PTBR adulterada: {path}")
        return {**status, "build_fingerprint": expected_fingerprint, "files": proof["files"]}

    def runtime_gate(self):
        raw = read(self.root, RUNTIME)
        if raw is None:
            raise Error("Perfil de suporte do motor ausente; build bloqueado")
        profile = json.loads(raw)
        if profile.get("schema") != 1 or profile.get("deployable") is not True or profile.get("blockers"):
            raise Error("Build/publicação bloqueados por suporte incompleto do motor: " + "; ".join(profile.get("blockers", ["perfil inválido"])))
        return digest(raw)

    def package(self, target):
        result = self.verify_output()
        target = Path(target).absolute()
        if not target.resolve().is_relative_to(safe_path(self.root, WORK.rstrip("/")).resolve()) or target.suffix != ".zip":
            raise Error("ZIP deve ficar sob translation-work/, fora de PTBR")
        safe_path(self.root, target.relative_to(self.root).as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".zip.tmp")
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for path in sorted(result["files"]):
                    info = zipfile.ZipInfo(path, (2020, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, read(self.root, "PTBR/" + path))
            validate_zip(temporary, result["files"])
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return {"zip": str(target), "files": len(result["files"]), "sha256": digest(target.read_bytes())}

    def status(self):
        status = self.check(deep=False)
        proof = read(self.root, BUILD)
        output = "absent"
        if proof:
            try:
                self.verify_output()
                output = "valid"
            except Error:
                output = "stale"
        snapshots = self.store.inventory()
        status.update({"output": output, "storage": {"transactions": len(snapshots),
                      "completed": sum(x["status"] in ("committed", "rolled-back") for x in snapshots),
                      "bytes": sum(x["bytes"] for x in snapshots), "limits": self.store.policy,
                      "reclaimable_bytes": self.store.gc(dry_run=True)["reclaimable_bytes"]}})
        runtime = read(self.root, RUNTIME)
        status["runtime_support"] = json.loads(runtime) if runtime else {"deployable": False, "blockers": ["Perfil ausente"]}
        return status


def validate_zip(path, files):
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(x.casefold() for x in names)) or set(names) != set(files) or not names:
                raise Error("Inventário ZIP divergente/vazio")
            for item in archive.infolist():
                safe_relative(item.filename)
                if item.filename.startswith("PTBR/") or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise Error("ZIP contém wrapper/link")
                if digest(archive.read(item)) != files[item.filename]:
                    raise Error("Hash ZIP divergente")
            if archive.testzip():
                raise Error("ZIP corrompido")
    except zipfile.BadZipFile as exc:
        raise Error("ZIP inválido") from exc


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    commands = p.add_subparsers(dest="command", required=True)
    update = commands.add_parser("update-sources", help="Importar originais verificados + sincronizar em uma transação")
    update.add_argument("--game-root", type=Path)
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--batch-size", type=int, default=500)
    for name in ("sync", "extract", "diff"):
        sync = commands.add_parser(name)
        sync.add_argument("--input", type=Path)
        sync.add_argument("--source-file")
        sync.add_argument("--allow-remove", action="append", default=[])
        sync.add_argument("--batch-size", type=int, default=500)
        sync.add_argument("--dry-run", action="store_true")
    apply = commands.add_parser("apply")
    apply.add_argument("payload", type=Path)
    apply.add_argument("--replace", action="store_true")
    check = commands.add_parser("check")
    check.add_argument("--complete", action="store_true")
    for name in ("status", "resume", "build", "verify-output", "recover", "rollback", "checkpoint"):
        commands.add_parser(name)
    gc = commands.add_parser("gc")
    gc.add_argument("--dry-run", action="store_true")
    package = commands.add_parser("package")
    package.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "dist/PTBR.zip")
    inspect = commands.add_parser("inspect-source")
    inspect.add_argument("--game-root", type=Path, required=True)
    return p


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args()
    try:
        toolkit = Toolkit(args.repo)
    except (Error, OSError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    command = args.command
    dry = getattr(args, "dry_run", False) or command == "diff"
    def run():
        if command == "recover":
            return {"recovered": toolkit.store.recover()}
        if command == "rollback":
            return {"transaction": toolkit.store.rollback()}
        if command == "gc":
            return toolkit.store.gc(dry_run=dry)
        if command == "update-sources":
            return toolkit.update_sources(args.game_root, dry, args.batch_size)
        if command in ("sync", "extract", "diff"):
            return toolkit.sync(args.input, args.source_file, args.allow_remove, dry, args.batch_size)
        if command == "apply":
            return toolkit.apply(json.loads(args.payload.read_text(encoding="utf-8")), args.replace)
        if command == "check":
            return toolkit.check(args.complete)
        if command in ("status", "resume"):
            return toolkit.status()
        if command == "build":
            return toolkit.build()
        if command == "verify-output":
            return toolkit.verify_output()
        if command == "package":
            return toolkit.package(args.output)
        if command == "checkpoint":
            status = toolkit.status()
            changes = {WORK + "reports/checkpoint.json": encoded(status)}
            return {"transaction": toolkit.store.transact(changes, {p: file_hash(toolkit.root, p) for p in changes}, "checkpoint"), **status}
        if command == "inspect-source":
            files = discover(args.game_root)
            return {"game_root": str(args.game_root), "files": {p: digest(v) for p, v in files.items()},
                    "notice": "Inspeção não aprova originalidade/versão e não altera o perfil de confiança."}
        raise Error("Comando não implementado")
    try:
        readonly = dry or command in ("check", "status", "resume", "verify-output", "inspect-source")
        if readonly:
            result = run()
        else:
            with toolkit.store.lock():
                if command != "recover":
                    toolkit.store.recover()
                result = run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if isinstance(result, dict) and result.get("rejected") else 0
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
