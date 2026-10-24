# Diretrizes de tradução — autoria da Ella

**Estado: decisões base aprovadas pela Ella em 23/10/2026, a partir do briefing e do corpus.** O glossário complementa este arquivo com termos; aqui ficam as regras de estilo e de decisão. Exceções novas entram neste arquivo antes de aparecerem nos lotes.

## Fonte e voz

- Fonte única: inglês de `EN/` (GOG Windows 1.0.4.0-gog). Nada é traduzido de ponte.
- Jogador tratado por "você". Sem "tu", salvo fala de personagem que peça registro arcaico ou regional, e aí com verbo correto.
- Narrador em terceira pessoa, tempo presente quando o original está no presente; cartas, relatórios e dilemas mantêm o tempo do original.
- Registro geral: drama político-familiar de ficção científica com feudalismo espacial. Governantes e cerimônias podem ser solenes; falas cotidianas são naturais e diretas. Proibido burocratês e solenidade em UI.
- Tom administrativo de relatórios de crise é mantido quando o original tem, sem virar "oficialês" com artigos engessados.

## Caixa e pontuação

- Corpo de texto em caixa de frase. Nada de copiar Title Case.
- Rótulos de menu/botão que o original guarda em CAIXA ALTA continuam em CAIXA ALTA no PT-BR: `NEW GAME` → `NOVO JOGO`, `OPTIONS` → `OPÇÕES`. Confiro no `Config/text.csv` antes de decidir cada rótulo.
- Rótulos guardados em caixa mista (`Custom`) seguem caixa de frase (`Personalizado`).
- Botões e rótulos curtos sem ponto final; frases completas e avisos com pontuação normal.
- Ênfase em CAIXA ALTA na fala do original é preservada como recurso de voz.
- Reticências do original são mantidas como `...`.

## Expressões e integridade

- Tokens entre chaves (`{TargetCharacter}`, `{spouseOf(TargetCharacter)}`, `{0}`, `{he(Actor)}`) são invioláveis em nome, caixa e quantidade; posição pode mudar para caber no PT.
- Tags (`<b>`, `<i>`, `<icv>`, `<link="...">`) preservadas; argumento textual de `link` traduzível conforme o guia de gramática.
- `$1`, `$2` de `kinterms.csv` preservados na posição que o português pedir.
- Gramática da DLL: `context.argument=true` exige exatamente um `{0}`; `[[EMPTY]]` só nos quatro sufixos `s/es` com `empty_allowed=true`.
- Gênero de personagem: usar os ramos do motor (player/male/female/unknown) quando existirem; em texto livre, preferir redação neutra para referentes de gênero desconhecido.

## Nomes e termos

- Nomes de personagens, casas e colônias gerados não são traduzidos (o toolkit não toca nas listas de nomes).
- Níveis políticos seguem o glossário: House=Casa, Faction=Facção, League=Liga, Domain=Domínio, Colony=Colônia. Títulos: duke=duque, baron=barão, archon=arconte, ruler=governante, head=chefe.
- "Bloodlines" como nome do DLC permanece em inglês; "bloodline" como conceito é "linhagem".
- Termo novo do mundo: decidir uma vez, registrar no glossário com chave de exemplo, e usar igual em todos os lotes.

## Composição com as funções da DLL (contrato verificado no lote 0039)

- `he()`/`He()`: emitem o sujeito "você/ele/ela" (unknown também "ele", masculino genérico; registrado no glossário). Verbo seguinte fica na 3ª pessoa do singular, que serve a todos os ramos.
- `him()` → objeto: "você/ele/ela" (forma tônia; evito posicionar onde só clítico serve). `himself()` → "você mesmo/ele mesmo/ela mesma"; componho frases que aceitem o ramo.
- `his()`/`His()` → player "seu", male "dele", female "dela", unknown "dele". Composição por ocorrência: para referente subordinado (fora do jogador), ordem pós-nominal ("os esforços {his(adminHead)}" = "os esforços dele"); quando a frase pedir "seu" pré-posto, construo sem artigo ("grandes esforços {his(adminHead)}") para o ramo player não quebrar.
- `d()`/`D()` (DInternal): sujeito pronome, igual a `he()`. `dis/dhas/dwas` (e maiúsculas) emitem "NOME é/tem/foi" com `{0}` = nome: nada de adjetivo generificado depois; uso predicados invariantes (substantivos, "sofreu ferimentos", "está a salvo"). Particípio depois de `dhas` = presente perfeito ("tem designado"); depois de `dwas` = passivo ("foi designado"). Gerúndio nunca vem direto depois destes tokens: reescrevo como "quem + verbo finito" ou predicado nominal.
- `heis/hehas/hewas` (frases de pronome): "você é/tem/estava", "ele é/tem/estava", "ela é/tem/estava" (unknown = genérico masculino, singular). `s()`/`es()` viram `[[EMPTY]]`.
- `d_s()`/`dp_s()`: `{0}'s` → `{0}` (emite só o nome/referente; a preposição `de` é escrita na frase PT que antecede o token, ex. "os espiões de {d_s(Assignee)}"). Sítios com o token pós-nominal sem preposição foram corrigidos no lote final.
- `s()`/`es()`: sufixos de 3ª pessoa do inglês; em PT os dois ramos viram `[[EMPTY]]` (você/ele/ela grita: sem desinência). É o uso autorizado dos quatro slots `empty_allowed`.
- `listAsSentence()`: conjunção → "e".
- Kinship (`MapTerm`, `Verbalise*`): determinantes self/player viram "{0}" puro (o contexto de família indica a posse; evita erro de concordância com gênero imprevisível); male/unknown = "{0} dele"; female = "{0} dela". "distant relative" → "parente distante" e variantes com "meu/seu" resolvidas por serem strings fixas.
- Regra geral pós-token: nenhum adjetivo, particípio ou artigo que precise concordar com gênero desconhecido pode vir imediatamente depois de token que emite pronome ou nome.

## Processo por lote

1. Ler o lote inteiro antes de traduzir: chaves, contextos, pares Título/Descrição.
2. Traduzir em grupos de até 100 unidades, revisando o grupo contra o original antes de aplicar.
3. Aplicar pelo payload com `generation`, `expected_count` e `source_sha256`; rejeição é corrigida e reaplicada só do pendente.
4. `check` após cada aplicação; `checkpoint` ao fechar cada lote; commit por lote fechado.
5. Ao reencontrar termo já traduzido, conferir no glossário e no corpus antes de variar.

Requisitos técnicos independentes de estilo continuam os do [guia técnico](../README.md): preservar expressões, tags e substituições; não alterar chaves, campos EN ou metadados; aplicar apenas PTBR pelo toolkit; revisar mensagens relacionadas e registrar decisões no glossário. A tradução inclui as 100 unidades do motor, conforme [gramatica-dinamica.md](gramatica-dinamica.md).
