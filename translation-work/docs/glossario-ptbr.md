# Glossário PT-BR — decisões da Ella

Decisões da revisão linguística da Ella. Formato: **original → escolha** (gênero/classe; contexto; exemplo de chave; justificativa; revisão). Termo novo entra aqui antes de aparecer num lote. Palavras iguais em inglês não são equivalência automática entre contextos.

Revisão base: 23/10/2026.

## Níveis políticos e território

- **House → Casa** (f.; a Casa, uma Casa). Unidade social-política central. `Config/pedia.csv` `Link.house`. "Casa" capta o sentido dinástico; "lar" e "residência" ficam para sentidos físicos.
- **Faction → Facção** (f.). `Link.faction`. Padrão do gênero estratégico.
- **League → Liga** (f.). Aliança de facções sob um arconte. `Link.league`.
- **Domain → Domínio** (m.). Conjunto sob um governante superior. `Link.domain`.
- **Colony → Colônia** (f.). Assentamento habitado. `Link.colony`.
- **Capital → Capital** (f.).

## Títulos e papéis

- **ruler → governante** (m., neutro pelo contexto). `Link.head` distingue: **Head of a House → chefe da Casa**; "head" sozinho, nas áreas da casa, é o chefe.
- **duke → duque / duchess → duquesa.**
- **baron → barão / baroness → baronesa.**
- **archon → arconte** (m.). Título inventado do mundo; forma lusófona consagrada.
- **vassal → vassalo** (m.; vassala quando feminino determinado). **vassalage → vassalagem** (f.). `Link.vassalage`.
- **heir → herdeiro/herdeira** conforme o personagem; sem gênero determinado, herdeiro. `BloodlinesDLC/Heir.csv`.
- **ward → tutelado/tutelada.** `BloodlinesDLC/WardTraits.csv`: pupila sob tutela da casa.
- **regent → regente.** **spy → espião/espiã** conforme personagem; agente de intriga quando genérico.
- **Role → cargo** (m.). Áreas da casa (`roles.csv`): **Administration → Administração, War → Guerra, Diplomacy → Diplomacia, Security → Segurança, Technology → Tecnologia.**

## Conceitos de jogo

- **bloodline → linhagem** (f.) como conceito; **Bloodlines** (DLC) fica em inglês como nome próprio.
- **dynasty → dinastia** (f.). **succession → sucessão** (f.). **inheritance → herança** (f.).
- **bloodline upgrade → aprimoramento de linhagem;** **ultimate → poder supremo** (provisório; revisar no lote de `CoreBloodlineUltimates.csv`).
- **trait → traço** (m.). **skill → habilidade** (f.). **tactic → tática** (f.). **fleet → frota** (f.).
- **intrigue → intriga** (f.). **secret → segredo** (m.). **agent → agente** (m.).
- **expedition → expedição** (f.). **installation → instalação** (f.). **artifact → artefato** (m.).
- **crisis → crise** (f.). **AP (Action Points) → PA (Pontos de Ação).** Confirmar no corpus de `text.csv` antes de generalizar.
- **reputation → reputação** (f.). **approval → aprovação** (f.). **opinion → opinião** (f.). **morality/moral acts → moral / atos morais.**
- **upbringing → criação** (f.). `ChildUpbringing.csv`. **kin → parente** (m., neutro). `kinterms.csv`.

## Nomes próprios fixos

- Pawley Games, Iceberg Interactive, GOG: sem tradução.
- Bloodlines (DLC), Unity: sem tradução.

- Question/astonishment bateria: "my {Up(title(PlayerCharacter))}" e "sire" viram o título interpolado (`Meu {Up(title(PlayerCharacter))}!`, `Meu Duque!`); "my lord" → "meu senhor"; "your grace" → "vossa graça".
- Kinship (`MapTerm`): self → "meu {0}", player → "seu {0}", male → "{0} dele", female → "{0} dela", unknown → "{0} dele" (aplicado em 0039 e alinhado à diretriz).

## Termos resolvidos nos lotes 0017-0039

- **seduction → sedução** (f.). **woo → cortejar**. **love interest → interesse amoroso**. **spouse → cônjuge** (m.). **wingman → asa** (f., ajuda romântica); "fazer de asa".
- **terraforming → terraformação** (f.). **Eden ship / "nave do Éden"** → Nave do Éden (nome próprio). **New Earth → Nova Terra**. **ringworld → mundo-anel** (m.). **black hole → buraco negro** (m.). **wormhole → buraco de minhoca**.
- **starship maneuvers**: **slingshot → Estilingue** (jogo de cartas do mundo, CA no nome do jogo; "jogo de cartas" preservado). **power bout → luta de robôs de poder**. **zero-gravity ballet → balé de gravidade zero**.
- **viridium → viridium** (m., recurso próprio do mundo; sem tradução). **sincomeia → sincomeia** (f., comida sintética). **sintohol / synthol → sintohol** (m., álcool sintético). **hoverbike → hoverbike** (f.). **nerve whip → chicote de nervos**.
- **Pulmão de Chacoalho (Shivering Lung)** → Pulmão de Chacoalho (doença; nome popular preserva a origem).
- **Cidade dos Casebres (Shantytown)** → Cidade dos Casebres.
- **Rede de Espionagem (Spy Network)** → Rede de Espionagem / rede de espionagem. **Espião no Sistema** (NameShown). **Relatório de Casa** → Relatório de Casa.
- **distant relative → parente distante**. **romance (Emotion) → romance** (minúsculo). **Seduction Attempt → Tentativa de Sedução** (Flag NameShown, CA mantida).
- **sabotage → sabotagem** (f.). **quarantine → quarentena** (f.). **unrest → agitação** (f.). **insurrection → insurreição / movimento insurrecionista**. **populist movement → movimento populista**.
- **heirloom → herança de família** (com o contexto de posse).
- **Title (rótulo vazio de evento)** → **Título** (caixa de frase).

## Fontes malformadas (espelhadas verbatim por obrigação do validador)

O EN com chaves/parênteses desbalanceados faz o validador tratar todo o restante da string como literal. Para não quebrar o guard, estas 5 entradas foram aprovadas com o fragmento EN verbatim (o bug é da fonte, não da tradução):

1. `batch-0021.jsonl` — `{PlayerSystem]'s domestic affairs` (chave `]` em vez de `}`).
2. `batch-0022.jsonl` — `{d(LovingChild})`.
3. `batch-0022.jsonl` — `{TaskMaster) did a great job revamping...` (parêntese sem chave de abertura; string inteira espelhada).
4. `batch-0030.jsonl` — `{ifPC(Guest,"you feel your heart harden",concat(Guest,"'s heart hardens")}` (ifPC sem fechar).
5. `batch-0038.jsonl` — `{him(Archon) before {he(Archon)} has the chance...` (him aberto no EN).

Duas entradas mantêm fragmento literal de token malformado dentro de texto já traduzido (o token solto aparece no jogo): `batch-0030.jsonl` `(d(Shy)}` e `batch-0038.jsonl` `(his(Child)}`. O marcador `tt()` de `batch-0027.jsonl` ("New Action available: Gift ancient book") também permanece em inglês por contrato do validador.
