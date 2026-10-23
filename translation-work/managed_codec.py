"""Native CLR grammar extraction/reconstruction; no game execution or translation service."""
from __future__ import annotations

import base64
import functools
import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

from native import Error, MANAGED_PATH, digest, fingerprint, validate_text

HOME = Path(__file__).resolve().parent
EMPTY = "[[EMPTY]]"


def check_toolchain():
    lock = json.loads((HOME / "managed/toolchain.json").read_text(encoding="utf-8"))
    for path, checksum in lock["files"].items():
        if digest((HOME / path).read_bytes()) != checksum:
            raise Error(f"Adaptador CLR alterado sem recompilação/verificação: {path}")


def command():
    check_toolchain()
    executable = str(HOME / "managed/GrammarTool.exe")
    if os.name == "nt":
        return [executable]
    mono = shutil.which("mono")
    if mono:
        return [mono, executable]
    raise Error("Leitura/build da gramática CLR exige .NET Framework 4.x no Windows ou Mono com System.Web.Extensions. A verificação rápida de Release não exige CLR.")


def invoke(mode, payload):
    try:
        result = subprocess.run(command() + [mode], input=payload, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Error(f"Falha ao executar o adaptador CLR: {exc}") from exc
    if result.returncode:
        raise Error(result.stderr.decode("utf-8-sig", errors="replace").strip())
    try:
        return json.loads(result.stdout.decode("utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        raise Error("Resposta inválida do adaptador CLR") from exc


@functools.lru_cache(maxsize=4)
def inspect(raw: bytes):
    return invoke("inspect-stdin", base64.b64encode(raw))


def native_value(value: str):
    return "" if value == EMPTY else value


def validate_grammar(record, translated):
    context = record["context"]
    if context.get("kind") != "managed-grammar-v1":
        raise Error("Contexto de gramática inválido")
    if translated == EMPTY:
        if not context.get("empty_allowed"):
            raise Error("Saída vazia só é permitida nos sufixos s/es explicitamente mapeados")
        return
    validate_text(record["EN"], translated)
    if context.get("argument"):
        if translated.count("{0}") != 1 or "{" in translated.replace("{0}", "") or "}" in translated.replace("{0}", ""):
            raise Error("Template de referência exige exatamente um {0}")
    elif "{" in translated or "}" in translated:
        raise Error("Texto de gramática não é uma nova expressão do parser")


class ManagedDocument:
    encoding = "cli-managed"
    bom = False

    def __init__(self, path, raw):
        if path != MANAGED_PATH:
            raise Error(f"DLL fora do perfil suportado: {path}")
        self.path, self.raw = path, raw
        data = inspect(raw)
        self.is_patched = data["patched"]
        self.data = data
        shapes = json.loads((HOME / "managed/engine-shapes.json").read_text(encoding="utf-8"))["method_shapes"]
        if not self.is_patched and data["method_shapes"] != shapes:
            raise Error("A estrutura dos métodos de gramática mudou; revisar o adaptador antes de sincronizar esta versão")
        if data["public_key"]:
            raise Error("Assembly com strong name exige outro perfil de assinatura")
        self.units = []
        for row, entry in enumerate(data["units"]):
            key = entry["key"]
            unit = {"id": f"{path}#{quote(key, safe='')}:Grammar", "source_file": path,
                    "key": key, "locator": key, "row": row, "column": "Grammar", "EN": entry["EN"],
                    "context": {"kind": "managed-grammar-v1", "method": entry["method"],
                                "role": entry["role"], "operation": entry["operation"],
                                "argument": entry["argument"], "empty_allowed": entry["empty_allowed"],
                                "method_shape": data["method_shapes"][entry["method"]]}}
            unit["source_sha256"] = fingerprint({k: unit[k] for k in ("source_file", "key", "locator", "column", "EN", "context")})
            self.units.append(unit)

    def render(self, translations):
        known = {u["id"]: u for u in self.units}
        if translations.keys() - known.keys():
            raise Error("ID de gramática desconhecido")
        values = {}
        for identity, translated in translations.items():
            validate_grammar(known[identity], translated)
            values[known[identity]["key"]] = native_value(translated)
        if all(values.get(u["key"], u["EN"]) == u["EN"] for u in self.units):
            return self.raw
        if self.is_patched:
            raise Error("Reconstrua a partir de EN original; uma DLL já localizada não é uma fonte")
        payload = json.dumps({"assembly": base64.b64encode(self.raw).decode("ascii"),
                              "translations": values}, ensure_ascii=False).encode("utf-8")
        output = invoke("rewrite-stdin", payload)
        try:
            raw = base64.b64decode(output["assembly"], validate=True)
        except (ValueError, KeyError) as exc:
            raise Error("DLL reconstruída inválida") from exc
        rebuilt = ManagedDocument(self.path, raw)
        expected = {u["key"]: values.get(u["key"], u["EN"]) for u in self.units}
        if {u["key"]: u["EN"] for u in rebuilt.units} != expected:
            raise Error("Gramática reconstruída diverge dos valores aprovados")
        if rebuilt.data["references"] != self.data["references"]:
            raise Error("A reconstrução alterou dependências CLR")
        return raw
