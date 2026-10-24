# Cobertura da tradução PT-BR — Star Dynasties Gold

Estado real em 24/10/2026, após o fechamento dos 39 lotes.

## Números finais

- Unidades do catálogo: **19.147** (105 CSVs + 1 DLL de gramática do motor).
- Traduzidas: **19.147** (100%). Pendentes: **0**.
- Geração do manifesto: `6884f7b73b062f154fded9b5125961d90763a5839ae831e396535178c7f71bb4`.
- `toolkit.py check --complete` → `valid: true`, `records: 19147`, `pending: 0`.
- Build: **106 arquivos** gerados, fingerprint `c1e6144cafd71d8a2798cbb7f15f10f2ef861add65a04e957941ddad55225e6b`.
- `verify-output`: OK, com SHA-256 por arquivo (DLL `11369bdaec8c27f436f5f33bb96a18ab6cc4a29bc0f5a4ef97cfa0570772fe68`).
- Pacote: `dist/PTBR.zip` — **sha256 `e538784c7b74c27d87af28305567fcdd3ee2d98c326bc533e8408c01e8ff39a3`**.

## Lotes fechados (39/39)

0001-0010, 0011-0020, 0021-0030, 0031-0038 (500 unidades cada) e 0039 (147 unidades: sad.csv, childTraits e as 100 unidades de gramática da DLL). Todos commitados com identidade de Yuri + co-autoria da Ella; pushes para github/gitlab/YuGit sincronizados até `d56749c`.

## O que a tradução cobre

- Config/text.csv (UI, telas, tutorial, codex, moralrules, táticas) e todo o conteúdo de eventos: BloodlinesDLC, expedições (com vitrine de mecânicas exclusivas), crises, sedução/casamento, designações, tarefas de espionagem, gathering/banquetes, child traits, segredos e a gramática do verbalizador.
- Terminologia registrada em `glossario-ptbr.md`; regras de composição com a DLL em `diretrizes-de-traducao.md` e `gramatica-dinamica.md`.

## Pendências de teste em partida (fora do alcance do build)

1. **Visual em jogo**: confirmar acentuação e ligaduras (Á/É/Ã/Õ/Ç) nas telas principais e nos eventos novos.
2. **Verbalizador da DLL**: conferir em partida as frases com `he()/him()/his()` e os templates `{0} é/tem/era`, os slash de kinship ("meu marido", "{0} dele") e as entradas de parentesco em `kinterms.csv`; dar atenção aos ramos unknown (genérico masculino "ele").
3. **Malformações espelhadas**: as 4 entradas de fonte malformada (ver glossário) permanecerão parcialmente em inglês no jogo; decidir com o usuário se vale um patch upstream ou manter o mirror.
4. **Fluxos longos de eventos**: tutorial guiado, sedução (2+ sucessos), terraformação (5 estágios), quarentena, motim e banquetes; validar colisão de caixa em botões (CAXA ALTA preservada) e quebra de linha em tooltips.
5. **Multi-batch coherence**: revisão de termos repetidos foi feita via corpus nas passagens 0031-0039; uma varredura de consistência automática (ex.: "sensuous"→"sensual", "quearters"→"aposentos" corretos, "Perform"→"Apresentar") ainda pode ser rodada antes da release.

## Artefatos

- `translation-work/dist/PTBR.zip` (pacote de instalação).
- `translation-work/translations/batch-0001..0039.jsonl` + `manifest.json` + `reports/checkpoint.json`.
- `translation-work/docs/`: briefing-do-jogo, fluxo-de-traducao, formato-localizacao, gramatica-dinamica, diretrizes-de-traducao, glossario-ptbr, analise-do-motor, compatibilidade-do-toolkit.