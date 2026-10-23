# Gramática dinâmica — passagem para Ella

O catálogo reúne 105 CSVs e uma DLL: **106 fontes e 19.147 unidades**. As 100 unidades novas estão no final de `batch-0039.jsonl`, que passou de 47 para 147 registros. As 19.047 entradas anteriores foram preservadas. Nenhum PTBR foi preenchido pela engenharia.

Leia `EN`, `context.method`, `context.role` e `context.operation` juntos. `player` refere-se ao jogador; `male`, `female` e `unknown` são os ramos nativos para outros personagens. As unidades de verbo contêm frases completas por ramo, permitindo decidir tratamento e concordância sem concatenar obrigatoriamente pronome e verbo. Revise parentesco junto de `Config/kinterms.csv`.

Quando `context.argument=true`, conserve **exatamente um `{0}`**. Ele recebe a referência nativa ao personagem ou termo. Pode mudar de posição, mas não pode ser removido, duplicado ou renomeado. Não o substitua por um nome próprio.

`PTBR=""` sempre significa pendente, inclusive nas duas unidades cujo EN é vazio. Somente nos quatro slots de sufixo `s/es`, identificados por `context.empty_allowed=true`, é permitido escrever **`[[EMPTY]]`** para aprovar conscientemente uma saída nativa vazia. O marcador não aparece no jogo. A escolha exige revisão linguística do uso dessas funções nos CSVs.

Use o mesmo payload e comando `apply` dos demais textos. Não edite EN, chaves, contexto, fingerprints ou manifesto. `check --complete` exige aprovação explícita de todas as unidades.

## Aspas dentro das expressões dos CSVs

Pode traduzir o conteúdo textual não vazio somente nestes argumentos conhecidos (índices iniciados em zero):

| Função | Argumentos de apresentação |
|---|---|
| `d`, `D`, `dhas`, `Dhas`, `dis`, `Dis`, `dwas`, `Dwas`, `d_s`, `D_s` | 1 |
| `dp`, `Dp`, `dp_s`, `Dp_s` | 2 |
| `fb` | 1 |
| `if`, `mf` | 1 e 2 |
| `concat` | 0 e 1 |
| `link` | 0 |
| `listAsSentence` | 1 |

O validador protege funções, estrutura e strings de lógica, como IDs de `fetch`, `showVar` e `roleIcon`. Strings vazias e sintaxe desconhecida permanecem protegidas. Não traduza argumentos de variável/condição. Investigue rejeições sem remover tokens para contorná-las.

## Entrega e teste

Registre escolhas nas diretrizes e no glossário, traduza manualmente, aplique e revise pelo fluxo existente. O pacote completo conterá os CSVs e `StarDynasties_Data/Managed/Pawley.StarDynasties.Engine.dll`. O auxiliar e Mono.Cecil não serão instalados no jogo.

Testes de engenharia usam valores sintéticos e não aprovam português. Depois da revisão completa, teste a saída no jogo em ambiente autorizado, observando diferentes personagens, vínculos clicáveis, parentesco e contexto de campanha. A instalação original fornecida por Yuri continua somente leitura.
