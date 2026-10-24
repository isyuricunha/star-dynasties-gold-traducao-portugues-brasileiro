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

## Pendências de decisão

- Traduções definitivas de nomes de instalações e expedições (Terraforming, Necropolis etc.): decidir ao traduzir os lotes correspondentes.
- Tratamento entre nobres ("my lord", "your grace"): decidir no primeiro lote de eventos com fala; registrar aqui.
