"""Star Dynasties CSV: edit cell spans, never reserialize unrelated bytes."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import quote


class Error(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def fingerprint(value) -> str:
    return digest(encoded(value))


CONFIG = {
    "text.csv": ("TextRef", ["Value"]),
    "tutorial.csv": ("Name", ["Title", "Body"]),
    "pedia.csv": ("Topic", ["Title", "Text"]),
    "terms.csv": ("Term", ["DisplayName"]),
    "skills.csv": ("Skill", ["DisplayName"]),
    "roles.csv": ("Role", ["AreaName", "RulingCouncilMemberTitle", "LeadingCouncilMemberTitle", "RoleDescription", "CouncilMemberDescription"]),
    "kinterms.csv": ("KinType", ["PartialKinTerm"]),
    "emotions.csv": ("Emotion", ["Description"]),
    "moralacts.csv": ("MoralAct", ["Description", "ReciprocalDescription"]),
    "moralrules.csv": ("MoralRule", ["Description", "OpinionDescription"]),
    "status.csv": ("StatusEvent", ["Description"]),
    "tactics.csv": ("Name", ["Title"]),
    "updates.csv": ("Update", ["Summary", "Short", "Title", "Description", "Help"]),
    "updatesExtra.csv": ("Name", ["Value"]),
}
NON_TEXT = {"ai.csv", "colors.csv", "de_kinterms.csv", "emotion_params.csv", "general.csv", "moralapplication.csv"}


def safe_relative(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path or ":" in path or "\x00" in path:
        raise Error(f"Caminho inseguro: {path!r}")
    p = PurePosixPath(path)
    if p.is_absolute() or any(x in ("", ".", "..") for x in path.split("/")):
        raise Error(f"Caminho inseguro: {path!r}")
    if any(x.endswith((" ", ".")) for x in p.parts):
        raise Error(f"Caminho incompatível com Windows: {path!r}")
    reserved = {"con", "prn", "aux", "nul"} | {f"{a}{b}" for a in ("com", "lpt") for b in range(1, 10)}
    if any(x.split(".")[0].lower() in reserved for x in p.parts):
        raise Error(f"Nome reservado: {path!r}")
    return path


def schema(path: str):
    safe_relative(path)
    p = PurePosixPath(path)
    if len(p.parts) != 2 or p.suffix != ".csv":
        raise Error(f"Recurso fora do perfil: {path}")
    if p.parts[0] == "Config" and p.name in CONFIG:
        return CONFIG[p.name]
    if p.parts[0] in ("Core", "BloodlinesDLC"):
        return "Key", ["Text"]
    raise Error(f"CSV não suportado: {path}")


def spans(text: str):
    """Strict comma CSV with CRLF/LF and original token spans (Unicode offsets)."""
    rows, row = [], []
    i, size = 0, len(text)
    while i < size:
        start = i
        if text[i] == '"':
            i += 1
            while True:
                if i >= size:
                    raise Error("CSV: campo com aspas não fechado")
                if text[i] == '"':
                    if i + 1 < size and text[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            if i < size and text[i] not in ",\r\n":
                raise Error("CSV: caractere após fechamento de aspas")
        else:
            while i < size and text[i] not in ",\r\n":
                if text[i] == '"':
                    raise Error("CSV: aspas em campo não delimitado")
                i += 1
        row.append((start, i))
        if i == size:
            rows.append(row)
            break
        if text[i] == ",":
            i += 1
            if i == size:
                row.append((i, i))
                rows.append(row)
            continue
        if text[i] == "\r":
            i += 1
            if i >= size or text[i] != "\n":
                raise Error("CSV: CR sem LF")
        i += 1
        rows.append(row)
        row = []
    return rows


class Document:
    def __init__(self, path: str, raw: bytes):
        self.path = safe_relative(path)
        self.raw = raw
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        try:
            self.text = raw.decode("utf-8-sig")
            self.rows = list(csv.reader(io.StringIO(self.text, newline=""), strict=True))
        except (UnicodeError, csv.Error) as exc:
            raise Error(f"{path}: UTF-8/CSV inválido: {exc}") from exc
        self.spans = spans(self.text)
        if len(self.rows) != len(self.spans) or not self.rows:
            raise Error(f"{path}: mapeamento CSV inconsistente")
        self.header = self.rows[0]
        key_column, self.columns = schema(path)
        if len(set(x for x in self.header if x)) != len([x for x in self.header if x]):
            raise Error(f"{path}: cabeçalho duplicado")
        if self.header[0] != key_column or any(x not in self.header for x in self.columns):
            raise Error(f"{path}: esquema desconhecido: {self.header}")
        if key_column == "Key" and self.header != ["Key", "Text"]:
            raise Error(f"{path}: esquema de eventos desconhecido")
        self.units = []
        seen = set()
        for row_number, row in enumerate(self.rows[1:]):
            if not any(row):
                continue
            if len(row) != len(self.header):
                raise Error(f"{path}: linha {row_number}: número de colunas inválido")
            key = row[0]
            if not key and path != "Config/terms.csv":
                raise Error(f"{path}: linha {row_number}: chave ausente")
            locator = key if key else f"@fixed-slot:{row_number}"
            if locator in seen:
                raise Error(f"{path}: chave duplicada: {locator}")
            seen.add(locator)
            context = {c: row[i] for i, c in enumerate(self.header) if c and c not in self.columns}
            for column in self.columns:
                col = self.header.index(column)
                value = row[col]
                if not value.strip():
                    continue
                unit = {"id": f"{path}#{quote(locator, safe='')}:{column}", "source_file": path,
                        "key": key, "locator": locator, "row": row_number, "column": column,
                        "EN": value, "context": context}
                unit["source_sha256"] = fingerprint({k: unit[k] for k in ("source_file", "key", "locator", "column", "EN", "context")})
                self.units.append(unit)

    def render(self, translations: dict[str, str]) -> bytes:
        changes = []
        ids = {u["id"] for u in self.units}
        if translations.keys() - ids:
            raise Error(f"{self.path}: ID desconhecido na reconstrução")
        for u in self.units:
            value = translations.get(u["id"], u["EN"])
            if value == u["EN"]:
                continue
            validate_text(u["EN"], value)
            start, end = self.spans[u["row"] + 1][self.header.index(u["column"])]
            old = self.text[start:end]
            if old.startswith('"') or any(c in value for c in ',"\r\n'):
                value = '"' + value.replace('"', '""') + '"'
            changes.append((start, end, value))
        text = self.text
        for start, end, value in sorted(changes, reverse=True):
            text = text[:start] + value + text[end:]
        result = (b"\xef\xbb\xbf" if self.bom else b"") + text.encode("utf-8")
        rebuilt = Document(self.path, result)
        if len(rebuilt.rows) != len(self.rows) or rebuilt.header != self.header:
            raise Error(f"{self.path}: reconstrução alterou estrutura")
        allowed = {(u["row"] + 1, self.header.index(u["column"])) for u in self.units}
        for i, (old, new) in enumerate(zip(self.rows, rebuilt.rows)):
            if len(old) != len(new) or any(a != b and (i, j) not in allowed for j, (a, b) in enumerate(zip(old, new))):
                raise Error(f"{self.path}: reconstrução alterou dados não traduzíveis")
        return result


def protected(text: str):
    # Preserve entire expressions; no unsupported invention of Portuguese engine functions.
    tokens = []
    depth = 0
    start = 0
    outside = []
    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            if depth:
                depth -= 1
                if depth == 0:
                    tokens.append(text[start:i + 1])
            else:
                outside.append("}")
    if depth:
        outside.append(text[start:])
    tokens.extend(outside)
    tokens.extend(re.findall(r"</?[A-Za-z][^<>]*>", text))
    tokens.extend(re.findall(r"\$\d+|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdif]", text))
    return Counter(tokens)


def validate_text(original: str, translated: str):
    if not isinstance(translated, str) or not translated.strip():
        raise Error("PTBR deve ser uma string não vazia")
    if any(ord(c) < 32 and c not in "\t\r\n" for c in translated):
        raise Error("PTBR contém caractere de controle")
    try:
        translated.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise Error("PTBR não é UTF-8 válido") from exc
    if protected(original) != protected(translated):
        raise Error("Placeholders, tags ou substituições $n/% foram alterados")
