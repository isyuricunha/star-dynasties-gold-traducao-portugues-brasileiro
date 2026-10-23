# Limite do adaptador CSV e bloqueio de publicação

## Evidência estática, sem alterar ou executar o jogo

Inspeção em 23/10/2026 da biblioteca original `StarDynasties_Data/Managed/Pawley.StarDynasties.Engine.dll`, cuja SHA-256 consta em [trusted-distributions.json](../trusted-distributions.json). Foi utilizada reflexão **ReflectionOnlyLoadFrom** do .NET Framework para ler tipos, assinaturas e operandos `ldstr` de métodos. Nenhum método da biblioteca foi invocado; nenhum arquivo da instalação foi escrito. As anotações abaixo resumem fatos técnicos, sem redistribuir uma DLL modificada.

O enum `Pawley.StarDynasties.Engine.Language` declara somente `English=0` e `German=1`. Há classes de parsing distintas `Text.Parsing.ParsingHelper` e `ParsingHelper_de`. A mera criação de `pt.csv` não registra um terceiro idioma nem escolhe regras gramaticais portuguesas.

Na classe `ParsingHelper`, a leitura dos operandos de métodos mostrou:

| Método | Literais observados / encaminhamento |
|---|---|
| `he(Character)` | `you`, `he`, `she`, `they`, passados à rotina `pronoun` |
| `He(Character)` | As mesmas formas iniciadas por maiúscula |
| `his(Character)` / `His(Character)` | Possessivos ingleses, passados à rotina de pronomes |
| `hehas(...)` / `Hehas(...)` | Pronomes ingleses e as formas ` have` / ` has` |
| `DInternal(...)` | Formas inglesas de referência ao jogador/pessoa não visível e consulta a sexo/parentesco |
| `pronoun(...)` | Consulta se é a personagem do jogador, se é visível e seu sexo |

A presença e o encaminhamento dessas constantes no corpo dos métodos são evidência de geração fora dos CSVs. `Config/Localization/de.csv` contém expressões alemãs próprias, reforçando que a localização oficial não se limita a trocar texto externo.

## Consequência para a tradução

Uma frase com `{he(Actor)}` pode manter um pronome em inglês mesmo quando as palavras ao redor estiverem traduzidas. O adaptador atual preserva expressões exatamente, como exige a integridade técnica. Portanto, **a tradução dos 19.047 campos não seria suficiente para afirmar uma experiência integral em PT-BR**.

Não foi implementado um substituidor de pronomes, um patch binário, um carregador de mods ou uma alteração das expressões. Inventar nomes de funções portuguesas ou remover tokens por conta própria não seria uma solução testada.

O controle versionado [runtime-support.json](../runtime-support.json) registra `deployable=false` e as pendências. `build` e `verify-output` recusam um perfil bloqueado, mesmo diante de JSONLs sintéticos completos; a CI não publica por consequência. Fixtures de teste usam um perfil independente que só autoriza os seus próprios recursos sintéticos.

## Próxima etapa técnica necessária

1. Mapear todas as funções de gramática relevantes, seus contratos e superfícies de UI fora dos CSVs.
2. Escolher uma extensão do motor comprovadamente suportada ou uma transformação nativa reconstruível, sem modificar a instalação original.
3. Separar os valores linguísticos que a Ella deverá decidir da implementação e dos identificadores imutáveis.
4. Testar reconstrução, atualização entre versões e execução em um ambiente autorizado, incluindo jogador/terceiros, sexo, visibilidade, parentesco e capitalização.
5. Auditar termos gerados por código, menus e acentos; só então registrar a implementação/evidência e habilitar o build.

Essa etapa não foi concluída. Alterar apenas o booleano do perfil não implementa o suporte. O repositório preserva uma preparação utilizável, mas **a definição de pronto do projeto integral permanece bloqueada por essa limitação**.

## Outros limites identificados

- Os logs consultados mostram versão `1.0.4.0-gog`; versões de `mod.xml` e “SavedOnGameVersion” se referem à autoria dos pacotes e não substituem a versão do runtime.
- A presença de recursos de Bloodlines não comprova ativação; um log anterior registra a checagem GOG como falsa.
- Não houve instalação nem teste em uma cópia executável do jogo. Compatibilidade com saves, Steam, outros sistemas operacionais e mods está sem validação.
- Os CSVs são fontes externas acessíveis, mas não provam que todos os textos da interface estejam externos. O catálogo explicita o escopo e não apresenta sua completude como cobertura integral do jogo.
