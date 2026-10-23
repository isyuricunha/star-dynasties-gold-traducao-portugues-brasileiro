"""Changed-file journals, guarded recovery and bounded local rollback storage."""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from native import Error, digest, encoded, fingerprint, safe_relative

DEFAULT_POLICY = {"max_completed": 10, "max_bytes": 512 * 1024 * 1024, "min_free_bytes": 16 * 1024 * 1024}


def is_link(path: Path):
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    except FileNotFoundError:
        return False


def safe_path(root: Path, relative: str) -> Path:
    safe_relative(relative)
    root = root.absolute()
    if is_link(root):
        raise Error(f"Raiz é link/junction: {root}")
    path = root
    for part in relative.split("/"):
        path = path / part
        if is_link(path):
            raise Error(f"Link/junction recusado: {path}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise Error(f"Escape da raiz: {path}")
    return path


def read(root: Path, relative: str) -> bytes | None:
    path = safe_path(root, relative)
    if not path.exists():
        return None
    if not path.is_file():
        raise Error(f"Não é arquivo: {path}")
    return path.read_bytes()


def file_hash(root: Path, relative: str):
    data = read(root, relative)
    return digest(data) if data is not None else None


def fsync_dir(path: Path):
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def write_atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, root: Path):
        self.root = root.absolute()
        if not self.root.is_dir():
            raise Error("A raiz do repositório precisa existir")
        for ancestor in (self.root, *self.root.parents):
            if (ancestor / "StarDynasties.exe").is_file() and (ancestor / "StarDynasties_Data").is_dir():
                raise Error("A instalação do jogo é somente leitura; o repositório não pode ficar nela")
        self.state = safe_path(self.root, "translation-work/.state")
        self.transactions = self.state / "transactions"
        self.policy = dict(DEFAULT_POLICY)
        config = read(self.root, "translation-work/storage-policy.json")
        if config:
            self.policy.update(json.loads(config))
        if any(type(self.policy[k]) is not int or self.policy[k] < 1 for k in DEFAULT_POLICY):
            raise Error("Política de armazenamento inválida")
        self.locked = False

    @contextmanager
    def lock(self):
        safe_path(self.root, "translation-work/.state/operation.lock")
        self.state.mkdir(parents=True, exist_ok=True)
        lock_path = self.state / "operation.lock"
        handle = lock_path.open("a+b")
        try:
            if lock_path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise Error("Outra operação está usando o repositório") from exc
            self.locked = True
            yield self
        finally:
            if self.locked:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            self.locked = False
            handle.close()

    def receipt(self, directory: Path):
        safe_path(self.root, directory.relative_to(self.root).as_posix())
        raw = read(self.root, (directory / "receipt.json").relative_to(self.root).as_posix())
        if raw is None:
            raise Error(f"Journal incompleto/protegido: {directory.name}; use recover")
        try:
            result = json.loads(raw)
            checksum = result.pop("checksum")
        except (ValueError, KeyError, TypeError) as exc:
            raise Error(f"Receipt corrompido: {directory.name}") from exc
        if checksum != fingerprint(result) or result.get("id") != directory.name or result.get("schema") != 1:
            raise Error(f"Receipt corrompido: {directory.name}")
        if result.get("status") not in ("preparing", "prepared", "applying", "committed", "rolled-back"):
            raise Error("Status de transação desconhecido")
        seen = set()
        for index, item in enumerate(result["changes"]):
            relative = item["path"]
            safe_path(self.root, relative)
            if relative.casefold() in seen or not self.allowed(relative):
                raise Error("Caminhos duplicados ou fora do escopo no journal")
            seen.add(relative.casefold())
            backup = directory / f"{index}.before"
            if item["before"] is not None:
                data = read(self.root, backup.relative_to(self.root).as_posix())
                if (data is None and result["status"] != "preparing") or (data is not None and digest(data) != item["before"]):
                    raise Error(f"Backup corrompido: {directory.name}/{index}")
            elif backup.exists():
                raise Error("Backup inesperado")
            staged = read(self.root, (directory / f"{index}.after").relative_to(self.root).as_posix())
            if staged is not None and (item["after"] is None or digest(staged) != item["after"]):
                raise Error("Staging corrompido; preserve o journal para revisão")
        expected = {"receipt.json"} | {f"{i}.before" for i, x in enumerate(result["changes"]) if x["before"] is not None}
        expected |= {f"{i}.after" for i, x in enumerate(result["changes"]) if x["after"] is not None}
        if any((p.name not in expected and not (result["status"] == "preparing" and self.staging_temp(p.name, expected))) or
               not p.is_file() or p.is_symlink() for p in directory.iterdir()):
            raise Error(f"Conteúdo desconhecido/protegido no journal: {directory.name}")
        return result

    @staticmethod
    def staging_temp(name, expected):
        import re
        return any(re.fullmatch(re.escape(x) + r"\.tmp-[0-9a-f]{32}", name) for x in expected)

    @staticmethod
    def allowed(path: str):
        return (path.startswith("EN/") or path.startswith("PTBR/") or
                path.startswith("translation-work/translations/") or
                path.startswith("translation-work/reports/") or
                path in ("translation-work/source-catalog.json", "translation-work/.state/local-install.json"))

    @staticmethod
    def save_receipt(directory: Path, receipt: dict):
        write_atomic(directory / "receipt.json", encoded({**receipt, "checksum": fingerprint(receipt)}))

    def inventory(self):
        result = []
        if self.transactions.exists():
            safe_path(self.root, "translation-work/.state/transactions")
            for directory in self.transactions.iterdir():
                if not directory.is_dir():
                    raise Error("Arquivo inesperado no armazenamento de transações")
                receipt = self.receipt(directory)
                size = sum(p.stat().st_size for p in directory.iterdir())
                result.append({"id": directory.name, "bytes": size, "status": receipt["status"],
                               "created_ns": receipt["created_ns"], "kind": receipt["kind"]})
        return sorted(result, key=lambda x: (x["created_ns"], x["id"]))

    def clean(self):
        pending = [x for x in self.inventory() if x["status"] not in ("committed", "rolled-back")]
        if pending:
            raise Error(f"Transação interrompida protegida: {pending[0]['id']}; execute recover")

    def gc(self, dry_run=True, reserve_bytes=0, reserve_count=0):
        self.clean()
        completed = self.inventory()
        count = len(completed) + reserve_count
        size = sum(x["bytes"] for x in completed) + reserve_bytes
        eligible = []
        # Always retain the most recent rollback, even if configuration cannot accommodate it.
        for item in completed[:-1]:
            if count <= self.policy["max_completed"] and size <= self.policy["max_bytes"]:
                break
            eligible.append(item)
            count -= 1
            size -= item["bytes"]
        if count > self.policy["max_completed"] or size > self.policy["max_bytes"]:
            raise Error(f"Orçamento insuficiente sem sacrificar recuperação: mínimo {size} bytes/{count} snapshots")
        if not dry_run:
            if not self.locked:
                raise Error("GC exige lock")
            for item in eligible:
                directory = self.transactions / item["id"]
                self.receipt(directory)
                # All targets have been resolved beneath the repository and validated above.
                shutil.rmtree(directory)
        return {"eligible": eligible, "reclaimable_bytes": sum(x["bytes"] for x in eligible),
                "remaining_count": count, "remaining_bytes": size}

    def transact(self, changes: dict[str, bytes | None], expected: dict[str, str | None], kind: str, fail_after=None):
        if not self.locked:
            raise Error("Operação exige lock")
        self.clean()
        actual_changes = {}
        old = {}
        for relative, new in sorted(changes.items()):
            if not self.allowed(relative):
                raise Error(f"Escrita fora do escopo: {relative}")
            before = read(self.root, relative)
            current = digest(before) if before is not None else None
            if relative not in expected or current != expected[relative]:
                raise Error(f"Edição concorrente: {relative}")
            if before != new:
                actual_changes[relative] = new
                old[relative] = before
        if not actual_changes:
            return None
        if kind != "build" and any(p.startswith("PTBR/") for p in actual_changes):
            raise Error("Somente build pode alterar PTBR")
        needed = sum(len(x or b"") for x in old.values()) + sum(len(x or b"") for x in actual_changes.values())
        metadata_budget = 4096 + len(actual_changes) * 1024
        if needed + metadata_budget > self.policy["max_bytes"]:
            raise Error(f"Transação requer pelo menos {needed + metadata_budget} bytes; ajuste storage-policy.json")
        if shutil.disk_usage(self.root).free < needed + metadata_budget + self.policy["min_free_bytes"]:
            raise Error("Espaço livre insuficiente para staging + rollback + headroom")
        # Reserve BEFORE pruning; no pruning until a new successful snapshot exists.
        self.gc(dry_run=True, reserve_bytes=needed + metadata_budget, reserve_count=1)
        self.transactions.mkdir(parents=True, exist_ok=True)
        identity = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
        directory = self.transactions / identity
        directory.mkdir()
        receipt = {"schema": 1, "id": identity, "created_ns": time.time_ns(), "kind": kind,
                   "status": "preparing", "changes": [
                       {"path": p, "before": digest(old[p]) if old[p] is not None else None,
                        "after": digest(new) if new is not None else None}
                       for p, new in actual_changes.items()]}
        self.save_receipt(directory, receipt)
        for index, (relative, new) in enumerate(actual_changes.items()):
            before = old[relative]
            if before is not None:
                write_atomic(directory / f"{index}.before", before)
            if new is not None:
                write_atomic(directory / f"{index}.after", new)
        receipt["status"] = "prepared"
        self.save_receipt(directory, receipt)
        # Catch editors changing any precondition while we prepared the journal.
        for relative, checksum in expected.items():
            if file_hash(self.root, relative) != checksum:
                receipt["status"] = "rolled-back"
                self.save_receipt(directory, receipt)
                raise Error(f"Edição concorrente antes da promoção: {relative}")
        receipt["status"] = "applying"
        self.save_receipt(directory, receipt)
        for index, item in enumerate(receipt["changes"]):
            path = safe_path(self.root, item["path"])
            if item["after"] is None:
                path.unlink(missing_ok=True)
                fsync_dir(path.parent)
            else:
                write_atomic(path, (directory / f"{index}.after").read_bytes())
            if fail_after is not None and index + 1 == fail_after:
                raise RuntimeError("Interrupção simulada após promoção parcial")
        for item in receipt["changes"]:
            if file_hash(self.root, item["path"]) != item["after"]:
                raise Error("Falha ao verificar promoção; execute recover")
        receipt["status"] = "committed"
        self.save_receipt(directory, receipt)
        for path in directory.glob("*.after"):
            path.unlink()
        self.gc(dry_run=False)
        return identity

    def recover(self):
        if not self.locked:
            raise Error("Recuperação exige lock")
        recovered = []
        for item in self.inventory():
            if item["status"] in ("committed", "rolled-back"):
                continue
            directory = self.transactions / item["id"]
            receipt = self.receipt(directory)
            if receipt["status"] == "preparing":
                if any(file_hash(self.root, x["path"]) != x["before"] for x in receipt["changes"]):
                    raise Error("Preparação interrompida com edição externa; revisão necessária")
                # No promotion has started. Only validated local staging exists here.
                shutil.rmtree(directory)
                recovered.append(item["id"])
                continue
            for change in receipt["changes"]:
                if file_hash(self.root, change["path"]) not in (change["before"], change["after"]):
                    raise Error(f"Conflito na recuperação: {change['path']}; preserve os arquivos para revisão")
            for index, change in enumerate(receipt["changes"]):
                path = safe_path(self.root, change["path"])
                if change["before"] is None:
                    path.unlink(missing_ok=True)
                else:
                    write_atomic(path, (directory / f"{index}.before").read_bytes())
            receipt["status"] = "rolled-back"
            self.save_receipt(directory, receipt)
            for path in directory.glob("*.after"):
                path.unlink()
            recovered.append(item["id"])
        return recovered

    def rollback(self):
        self.clean()
        items = [x for x in self.inventory() if x["status"] == "committed"]
        if not items:
            raise Error("Nenhum checkpoint de rollback disponível")
        receipt = self.receipt(self.transactions / items[-1]["id"])
        if receipt["kind"] == "build":
            raise Error("Rollback de build exige restauração revisada em Git; PTBR não será alterado")
        changes, expected = {}, {}
        for index, item in enumerate(receipt["changes"]):
            if file_hash(self.root, item["path"]) != item["after"]:
                raise Error("Checkpoint não corresponde ao estado atual; rollback recusado")
            changes[item["path"]] = (self.transactions / receipt["id"] / f"{index}.before").read_bytes() if item["before"] else None
            expected[item["path"]] = item["after"]
        catalog_path = "translation-work/source-catalog.json"
        if catalog_path in changes:
            import base64
            prior_raw = changes[catalog_path]
            current_raw = read(self.root, catalog_path)
            prior = json.loads(prior_raw)["native"] if prior_raw else {}
            current = json.loads(current_raw)["native"] if current_raw else {}
            if prior_raw and not prior:
                raise Error("Catálogo anterior sem snapshot nativo; restaure pelo Git")
            for source in prior.keys() | current.keys():
                relative = "EN/" + safe_relative(source)
                data = base64.b64decode(prior[source]["base64"], validate=True) if source in prior else None
                if source in prior and digest(data) != prior[source]["sha256"]:
                    raise Error("Snapshot nativo anterior corrompido")
                if source in current and file_hash(self.root, relative) != current[source]["sha256"]:
                    raise Error("EN editado depois da sincronização; rollback recusado")
                changes[relative] = data
                expected[relative] = file_hash(self.root, relative)
        return self.transact(changes, expected, "rollback")
