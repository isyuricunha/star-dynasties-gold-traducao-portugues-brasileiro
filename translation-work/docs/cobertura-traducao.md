# Cobertura da tradução PT-BR — Star Dynasties Gold

Estado real em 24/10/2026, após o fechamento dos 39 lotes.

## Revisão independente (24/10/2026)

Revisor externo independente varreu as 19.147 linhas (tokens EN↔PT idênticos em 100%, hashes, vedações e amostras manuais). Achados substanciais corrigidos no mesmo dia:

- **S1**: ~130 linhas recompostas para a concordância com os templates do verbalizador (gerúndio → "quem + verbo finito", dupla cópula → predicado nominal/particípio, presente perfeito com "tem + particípio"). Varredura final: 0 linhas quebradas.
- **S2**: ramos unknown das frases de pronome alinhados ao genérico masculino singular ("Ele tem/é/estava"); `dwas` virou passivo "foi"; `hewas` virou "estava".
- **S4**: 192 linhas com a preposição "de" inserida antes dos possessivos de nome nu (`{d_s}`/`{D_s}`); varredura final: 0.
- **S3**: fontes malformadas recontadas (5 espelhos integrais + 2 fragmentos + 1 marcador `tt()`) e documentadas no glossário.

Minores aceitos (registrados, sem correção): 'Tá bom'/'na corda bamba' em fala de personagem; 'FEEDBACK'/'STEAM WORKSHOP' como nomes de plataforma; TestPack "Execute/Exile/Torture {him(Character)}" (botões de conteúdo de teste). Minores corrigidos: 'abalarme'→'abalada', 'vermelhe'→'em brasa', 'deserditado'→'deserdado', 'Divorciou'→'Divorciou-se de', 'naveta'→'lançadeira' unificado, 'As Leis Pelas Quais Vivemos', 'Filho Mais Novo', 'Romance'→'romance' uniforme.

## Números finais

- Unidades do catálogo: **19.147** (105 CSVs + 1 DLL de gramática do motor).
- Traduzidas: **19.147** (100%). Pendentes: **0**.
- Geração do manifesto: `6884f7b73b062f154fded9b5125961d90763a5839ae831e396535178c7f71bb4`.
- `toolkit.py check --complete` → `valid: true`, `records: 19147`, `pending: 0`.
- Build pós-revisão: **106 arquivos**, fingerprint `8baba66f44814804769146949c371ebacc8e614ef79fbfa749747a05395b6906`.
- `verify-output`: OK, com SHA-256 por arquivo (DLL `ca4671267ad7ac8517eaf101fec79cebe67f5203f30c48ba4f7cede51b4312b2`).
- Pacote: `dist/PTBR.zip` — **sha256 `5714d8d8b17adf0d742a1acb010b57ab74df5f799bbc095724510c132c08e35b`**.

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