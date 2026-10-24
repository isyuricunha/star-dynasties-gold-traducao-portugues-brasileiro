"""Read-only planning and Actions-only, idempotent GitHub Release publication."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from native import Error, digest, encoded
from toolkit import BUILD, RUNTIME, TRANSLATIONS, Toolkit, parse_jsonl

CANONICAL_REPO = "isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro"
SEMVER = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")


def git(root, *args, allow_failure=False):
    process = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if process.returncode and not allow_failure:
        raise Error(f"Git falhou: {' '.join(args[:2])}: {process.stderr.decode('utf-8', errors='replace').strip()}")
    return process


def revision(root, ref):
    return git(root, "rev-parse", "--verify", ref + "^{commit}").stdout.decode().strip()


def ancestor(root, older, newer):
    return git(root, "merge-base", "--is-ancestor", older, newer, allow_failure=True).returncode == 0


def git_files(root, ref, prefix):
    paths = git(root, "ls-tree", "-r", "--name-only", "-z", ref, "--", prefix).stdout.split(b"\0")
    result = {}
    for path in paths:
        if path:
            name = path.decode("utf-8")
            result[name[len(prefix) + 1:]] = git(root, "show", f"{ref}:{name}").stdout
    return result


def tagged_records(root, ref):
    records = {}
    for name, raw in git_files(root, ref, TRANSLATIONS.rstrip("/")).items():
        if re.fullmatch(r"batch-\d{4,}\.jsonl", name):
            for record in parse_jsonl(raw):
                if record["id"] in records:
                    raise Error("IDs duplicados no histórico da Release")
                records[record["id"]] = record
    if not records:
        raise Error("Release anterior sem JSONL versionado; revisão da migração necessária")
    return records


def stable_releases(releases):
    stable = []
    seen = set()
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        tag = release.get("tag_name", "")
        match = SEMVER.fullmatch(tag)
        if not match:
            raise Error(f"Release publicada com versão ambígua: {tag}")
        if tag in seen or not release.get("published_at"):
            raise Error("Metadados de Release publicados ausentes/duplicados")
        seen.add(tag)
        stable.append((tuple(map(int, match.groups())), release))
    return [x[1] for x in sorted(stable, key=lambda x: x[0])]


def plan(root, sha, releases, repository=CANONICAL_REPO):
    if repository != CANONICAL_REPO or not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise Error("Repo/SHA de publicação inválido")
    toolkit = Toolkit(root)
    proof = toolkit.verify_output()
    if revision(root, "HEAD") != sha:
        raise Error("Checkout não corresponde ao SHA solicitado")
    # A verified working tree must also be the exact committed native/source workspace.
    if git(root, "diff", "--exit-code", sha, "--", "EN", "PTBR", "translation-work/translations", "translation-work/source-catalog.json", BUILD, RUNTIME, allow_failure=True).returncode:
        raise Error("Fontes/JSONL/PTBR/build manifest não correspondem ao commit")
    candidate = {p: digest(raw) for p, raw in git_files(root, sha, "PTBR").items()}
    if candidate != proof["files"]:
        raise Error("PTBR não está integralmente versionado no commit")
    published = stable_releases(releases)
    for release in published:
        tag_sha = revision(root, "refs/tags/" + release["tag_name"])
        if not ancestor(root, tag_sha, sha):
            raise Error(f"Tag não ancestral ao candidato: {release['tag_name']}")
    previous = published[-1] if published else None
    previous_tag = previous["tag_name"] if previous else None
    previous_files = {p: digest(raw) for p, raw in git_files(root, previous_tag, "PTBR").items()} if previous else {}
    if previous and not previous_files:
        raise Error("Release anterior sem árvore PTBR; revisão necessária")
    if previous and previous_files == candidate:
        return {"publish": False, "reason": "PTBR idêntico à última Release publicada", "tag": previous_tag,
                "previous_release": previous, "sha": sha}
    if previous:
        major, minor, patch = map(int, SEMVER.fullmatch(previous_tag).groups())
        tag = f"v{major}.{minor}.{patch + 1}"
    else:
        tag = "v1.0.0"
    existing = git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}", allow_failure=True)
    if existing.returncode == 0 and existing.stdout.decode().strip() != sha:
        raise Error(f"Tag {tag} já existe em outro commit; nunca será movida")
    current = tagged_records(root, sha)
    old = tagged_records(root, previous_tag) if previous else {}
    added = current.keys() - old.keys()
    removed = old.keys() - current.keys()
    changed = {k for k in current.keys() & old.keys() if (current[k]["PTBR"], current[k]["source_sha256"]) != (old[k]["PTBR"], old[k]["source_sha256"])}
    retained = (current.keys() & old.keys()) - changed
    native_changed = sorted(p for p in candidate.keys() | previous_files.keys() if candidate.get(p) != previous_files.get(p))
    manifest = toolkit.load_manifest()
    lines = [f"# Star Dynasties — PT-BR {tag}", ""]
    if previous:
        lines += [f"Comparação com {previous_tag}: {len(added)} unidades novas, {len(changed)} alteradas, "
                  f"{len(removed)} removidas e {len(retained)} mantidas.", ""]
        if not added and not changed and not removed:
            lines += ["Os arquivos nativos mudaram sem alteração nas unidades PT-BR; esta versão não implica revisão linguística adicional.", ""]
        prior_raw = git(root, "show", f"{previous_tag}:{BUILD}").stdout
        previous_build = json.loads(prior_raw)
        if previous_build.get("version") != manifest["version"]:
            lines += [f"Base de recursos: {previous_build.get('version')} → {manifest['version']}.", ""]
        lines += [f"[Comparar commits](https://github.com/{repository}/compare/{previous_tag}...{sha})", ""]
    else:
        lines += [f"Primeiro pacote completo validado: {len(current)} unidades de texto em {len(candidate)} arquivos nativos. "
                  "Escopo: interface, tutorial, enciclopédia, eventos do jogo base e recursos de Bloodlines.", ""]
    lines += [f"Base analisada: {manifest['version']}. O pacote de textos não concede acesso ao DLC.",
              "Validação automatizada de formato, integridade e completude. Teste em execução não é comprovado por esta automação.", "",
              "## Instalação", "", "Faça backup de Config, Core, BloodlinesDLC e da DLL Pawley.StarDynasties.Engine em StarDynasties_Data/Managed. Extraia **PTBR.zip** na pasta que contém "
              "StarDynasties.exe, mesclando as pastas. Use **English** no menu de idiomas. "
              "Consulte o README para compatibilidade, restauração e limitações.", "", "## Recursos nativos alterados", ""]
    lines += [f"- `{p}`" for p in native_changed]
    return {"publish": True, "tag": tag, "sha": sha, "previous_tag": previous_tag,
            "counts": {"added": len(added), "modified": len(changed), "removed": len(removed), "retained": len(retained)},
            "changed_files": native_changed, "notes": "\n".join(lines) + "\n"}


class GitHub:
    def __init__(self, repository, token):
        if repository != CANONICAL_REPO or not token:
            raise Error("Publicação exige repo canônico e GITHUB_TOKEN do Actions")
        self.repository = repository
        self.token = token

    def request(self, method, endpoint, payload=None, raw=None, missing=False):
        url = endpoint if endpoint.startswith("https://") else "https://api.github.com" + endpoint
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ("api.github.com", "uploads.github.com"):
            raise Error("Host da API de publicação não permitido")
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "StarDynasties-PTBR-toolkit"}
        data = raw if raw is not None else (encoded(payload) if payload is not None else None)
        if data is not None:
            headers["Content-Type"] = "application/zip" if raw is not None else "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if missing and exc.code == 404:
                return None
            raise Error(f"GitHub API: {method} {parsed.path}: HTTP {exc.code}; revise a execução antes de tentar novamente") from exc

    def endpoint(self, suffix):
        base = f"/repos/{self.repository}"
        return base if not suffix else f"{base}/{suffix.lstrip('/')}"

    def releases(self):
        result, page = [], 1
        while True:
            chunk = self.request("GET", self.endpoint(f"releases?per_page=100&page={page}"))
            result.extend(chunk)
            if len(chunk) < 100:
                return result
            page += 1

    def assert_current(self, sha):
        repo = self.request("GET", self.endpoint(""))
        branch = repo.get("default_branch")
        if branch != "main":
            raise Error("Branch padrão mudou; revise o workflow antes de publicar")
        commit = self.request("GET", self.endpoint("commits/" + urllib.parse.quote(branch, safe="")))
        if commit.get("sha") != sha:
            raise Error("Candidato stale: a branch padrão avançou; a execução mais recente publicará")


def asset_ok(asset, zip_data):
    return (asset.get("name") == "PTBR.zip" and asset.get("state") == "uploaded" and
            asset.get("size") == len(zip_data) and asset.get("digest") == "sha256:" + digest(zip_data))


def publish(root, repository, sha, api):
    api.assert_current(sha)
    result = plan(root, sha, api.releases(), repository)
    zip_path = root / "translation-work/dist/PTBR.zip"
    Toolkit(root).package(zip_path)
    zip_data = zip_path.read_bytes()
    if not result["publish"]:
        assets = result["previous_release"].get("assets", [])
        if not any(asset_ok(a, zip_data) for a in assets):
            raise Error("Release existente sem asset íntegro verificável; não criar versão duplicada. Revise/repare o asset da Release.")
        return {"status": "skipped", **result}
    tag = result["tag"]
    api.assert_current(sha)
    tag_ref = api.request("GET", api.endpoint("git/ref/tags/" + tag), missing=True)
    if tag_ref is None:
        # Reserve the exact commit before drafting; an interrupted attempt can reuse this ref.
        api.request("POST", api.endpoint("git/refs"), {"ref": "refs/tags/" + tag, "sha": sha})
    else:
        obj = tag_ref["object"]
        for _ in range(5):
            if obj["type"] != "tag":
                break
            obj = api.request("GET", api.endpoint("git/tags/" + obj["sha"]))["object"]
        if obj.get("type") != "commit" or obj.get("sha") != sha:
            raise Error("Tag remoto reservado por outro commit; publicação recusada")
    existing = api.request("GET", api.endpoint("releases/tags/" + tag), missing=True)
    if existing and not existing.get("draft"):
        raise Error("Release apareceu após planejamento; reexecute para comparar o estado publicado")
    api.assert_current(sha)
    if existing:
        if existing.get("tag_name") != tag:
            raise Error("Draft incompatível")
        # A draft with no created Git tag still has to name this exact target SHA.
        if existing.get("target_commitish") != sha:
            raise Error("Draft pertence a outro SHA; revisão manual necessária")
        release = existing
    else:
        release = api.request("POST", api.endpoint("releases"), {"tag_name": tag, "target_commitish": sha,
                              "name": f"Star Dynasties — Português Brasileiro {tag}", "body": result["notes"],
                              "draft": True, "prerelease": False})
    assets = api.request("GET", api.endpoint(f"releases/{release['id']}/assets"))
    named = [a for a in assets if a.get("name") == "PTBR.zip"]
    if len(named) > 1 or (named and not asset_ok(named[0], zip_data)):
        raise Error("Asset existente divergente; não apagar nem sobrescrever automaticamente")
    if not named:
        upload = release["upload_url"].split("{")[0] + "?name=PTBR.zip"
        uploaded = api.request("POST", upload, raw=zip_data)
        if not asset_ok(uploaded, zip_data):
            raise Error("Upload não retornou tamanho/digest esperado; draft preservado")
    api.assert_current(sha)
    # Confirm the exact tag target through the API (lightweight or annotated tags).
    tag_ref = api.request("GET", api.endpoint("git/ref/tags/" + tag), missing=True)
    if tag_ref:
        obj = tag_ref["object"]
        for _ in range(5):
            if obj["type"] != "tag":
                break
            obj = api.request("GET", api.endpoint("git/tags/" + obj["sha"]))["object"]
        if obj.get("type") != "commit" or obj.get("sha") != sha:
            raise Error("Tag remoto não aponta ao SHA verificado")
    release = api.request("PATCH", api.endpoint(f"releases/{release['id']}"),
                          {"draft": False, "body": result["notes"], "make_latest": "true"})
    final = api.request("GET", api.endpoint(f"releases/{release['id']}"))
    if final.get("draft") or final.get("tag_name") != tag or not any(asset_ok(a, zip_data) for a in final.get("assets", [])):
        raise Error("Release/asset não confirmado após publicação")
    return {"status": "published", "tag": tag, "sha": sha, "url": final["html_url"]}


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "publish"])
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--repository", default=CANONICAL_REPO)
    parser.add_argument("--sha")
    parser.add_argument("--releases", type=Path, help="plan: JSON fixture of published releases; no network")
    args = parser.parse_args()
    try:
        sha = args.sha or revision(args.repo, "HEAD")
        if args.command == "plan":
            if args.releases is None:
                raise Error("plan exige --releases JSON para planejamento somente leitura")
            result = plan(args.repo, sha, json.loads(args.releases.read_text(encoding="utf-8")), args.repository)
        else:
            if (os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REPOSITORY") != CANONICAL_REPO or
                os.environ.get("GITHUB_REF") != "refs/heads/main" or os.environ.get("GITHUB_SHA") != sha or
                os.environ.get("GITHUB_EVENT_NAME") not in ("push", "workflow_dispatch")):
                raise Error("publish só é permitido pelo Actions canônico em main e no SHA do evento")
            result = publish(args.repo, args.repository, sha, GitHub(args.repository, os.environ.get("GITHUB_TOKEN")))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
