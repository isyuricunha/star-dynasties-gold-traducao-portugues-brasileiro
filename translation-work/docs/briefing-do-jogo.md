# Briefing de Star Dynasties para a tradução PT-BR

Pesquisa inicial preparada pela desenvolvedora do toolkit em **23/10/2026**. Este briefing já está escrito para a passagem à Ella; ela deve consultá-lo e atualizar informações verificáveis que surgirem durante a tradução. Nenhuma equivalência PT-BR apresentada aqui constitui terminologia aprovada.

## Identidade e fontes

Star Dynasties é desenvolvido pela Pawley Games e publicado pela Iceberg Interactive. A Steam registra o lançamento completo em 01/09/2021, após acesso antecipado iniciado em 16/03/2021. O jogo reúne estratégia por turnos, administração de uma dinastia e histórias produzidas pelas relações entre personagens. O autor identifica Unity na página do projeto. A instalação examinada também contém o runtime Mono e bibliotecas gerenciadas de Unity.

A base local é GOG para Windows, **1.0.4.0-gog**, identificada no log de inicialização. O metadado GOG informa `buildId=56067213234031252`, jogo `1177048612`; o conteúdo Bloodlines aparece como `1567705613`. O nome “Gold” do repositório não aparece como uma versão técnica separada nos arquivos. O perfil cobre os recursos fornecidos do jogo base e do DLC, sem presumir equivalência binária com Steam.

Fontes consultadas:

1. [Steam — Star Dynasties, AppID 1194590](https://store.steampowered.com/app/1194590/Star_Dynasties/): identidade, autores, datas, descrição do gênero e idiomas oferecidos.
2. [Pawley Games / Glen Pawley no itch.io](https://gpawley.itch.io/star-dynasties): premissa, foco na dinastia, vassalos, casamentos, espionagem e reputação. É uma apresentação do próprio desenvolvedor.
3. [Steam — Bloodlines, AppID 1852400](https://store.steampowered.com/app/1852400/Star_Dynasties_Bloodlines/): lançamento em 09/03/2022 e sistemas específicos da expansão.
4. [Enciclopédia original](../../EN/Config/pedia.csv): fonte primária detalhada para mundo, sociedade e regras. As chaves citadas abaixo identificam os verbetes sem depender da linha física do CSV.
5. [Tutorial original](../../EN/Config/tutorial.csv), [cargos](../../EN/Config/roles.csv), [habilidades](../../EN/Config/skills.csv) e [texto geral](../../EN/Config/text.csv): uso concreto dos termos e instruções para o jogador.
6. Arquivos originais em [Core](../../EN/Core/) e [BloodlinesDLC](../../EN/BloodlinesDLC/): contexto dos eventos, dilemas e vozes. O catálogo mantém o arquivo e a chave nativa de cada unidade.
7. Instalação fornecida, fora do repo: `logs/log.txt`, `goggame-1177048612.info`, `goggame-1567705613.info`, `Config/releasenotes.txt`, `Core/mod.xml`, `BloodlinesDLC/mod.xml`. Não são destinos de escrita do toolkit. Os metadados de identidade necessários são representados por hashes em [trusted-distributions.json](../trusted-distributions.json).
8. [Discussão de traduções na comunidade Steam](https://steamcommunity.com/app/1194590/discussions/0/3083250789421731361/): distingue uma resposta de representante sobre investigação de suporte em 2021 de uma explicação posterior de jogador sobre substituições dinâmicas. A fala do jogador é contexto secundário, não documentação oficial do motor.

As ligações relativas deste briefing partem de `translation-work/docs/`: os recursos do jogo estão em `../../EN/`. A consulta técnica da DLL está registrada separadamente em [analise-do-motor.md](./analise-do-motor.md).

## A ruptura que define o cenário

Segundo `Link.collapse`, a Terra foi destruída no século XXII. A civilização já possuía colônias, mas dependia de Sol para sua coordenação, logística e economia. A destruição do planeta e os danos a outras estruturas do sistema interromperam essa sustentação. As colônias passaram por violência e escassez antes de uma estabilização gradual.

**O motivo da catástrofe é incerto dentro do universo.** A teoria de um experimento científico descontrolado é descrita como uma crença corrente. Evitar transformar hipótese em fato ao traduzir frases com marcas de incerteza.

O mundo jogável surge depois desse colapso. A tecnologia avançada existe como herança material: máquinas, instalações e artefatos ainda são usados, mas o conhecimento para recriá-los ou expandi-los foi perdido em larga medida. Isso diferencia o cenário de uma fantasia de progresso tecnológico contínuo. Os textos de expedições devem preservar a combinação de descoberta, ignorância, risco e oportunidade, sem assumir que a sociedade compreende os mecanismos encontrados.

Referências locais: `Link.collapse`, `Link.colony`, `Link.technology`, `Link.damagedcolony`, `Link.expeditionevents` em `pedia.csv`. A apresentação do desenvolvedor no itch.io corrobora o contraste entre sociedade feudal e máquinas antigas.

## A organização social e o mapa político

`House` é uma unidade social e política, não apenas uma construção física. A enciclopédia relaciona sua origem a grupos que tomaram controle de espaços e recursos nas colônias depois da catástrofe. Uma casa reúne seu chefe, parentes e conselheiros; também exerce poder sobre pessoas que não integram esse núcleo.

Os membros de uma casa residem normalmente na mesma colônia. Casamento e parentesco não significam automaticamente pertencer à mesma casa: o casamento pode transferir um cônjuge para a casa do outro. Esse detalhe muda a interpretação de mensagens sobre recrutamento, nascimento, herança e tamanho da casa.

Uma colônia tem sua própria organização de poder. Colônias podem reunir-se em uma `Faction`, sob um `duke`; seus `barons` têm obrigações e expectativas de autonomia. Uma `League` reúne facções sob um `archon`. O governante superior também pode controlar diretamente uma facção e um sistema de capital. `House`, `Faction`, `League`, `Domain` e `Colony` não são intercambiáveis.

Vassalagem envolve tributos, defesa, contribuição de frotas e reparação de injustiças. A expectativa moral da relação ajuda a explicar por que certas recusas ou punições afetam reputação e aprovação. Não reduzir tudo a uma aliança militar voluntária.

Referências: `Link.house`, `Link.head`, `Link.faction`, `Link.league`, `Link.vassalage`, `Link.domain`, `Link.tax`, `Link.morality`. Os verbetes também permitem distinguir autoridade formal, controle de território e reconhecimento de legitimidade.

## Personagens, relações e voz

A campanha acompanha uma pessoa e seus sucessores, dentro de uma rede política que muda com o tempo. O material consultado não estabelece um elenco fixo universal de protagonistas e vilões. Nomes de casas, pessoas e sistemas podem variar entre campanhas; o toolkit não traduz as listas geradoras de nomes próprios.

Textos narrativos alternam entre descrições de acontecimentos, perspectivas pessoais e falas/ações de terceiros. Em `Core/Romance.csv`, por exemplo, `Romance.LoveInterest.Default.Update.Description` usa perspectiva em primeira pessoa e funções que determinam como outra personagem será referida. Em eventos de crise, instruções e resultados podem adotar um tom mais administrativo. A perspectiva deve ser verificada na cadeia do evento, não inferida apenas da primeira frase de uma linha.

Casamento, filhos, adoção, casos amorosos, rivalidades e sucessão têm consequências sociais e políticas. Em `Adoption`, `Romance`, `Seduction*`, `Dynastic_jp*` e nos eventos familiares de Bloodlines, uma escolha aparentemente íntima pode produzir obrigações ou ressentimentos posteriores. Preservar quem age, quem é afetado e quem está narrando.

O tom geral mistura drama familiar, ameaça, negociação, honra e situações extraordinárias de ficção científica. Não uniformizar automaticamente toda fala como linguagem burocrática. Também não inserir humor, solenidade ou informalidade que o contexto não sustente. A decisão de registro final pertence à Ella.

## Sistemas que voltam continuamente

| Sistema | Contexto de leitura | Recursos de referência |
|---|---|---|
| Ações e AP | Custos, condições, decisões disponíveis e consequências | `Config/text.csv`, `pedia.csv` → `Link.ap` |
| Administração, guerra, diplomacia, segurança e tecnologia | Áreas da casa, cargos, tarefas e efeitos passivos | `roles.csv`, `skills.csv`, `pedia.csv` → `Link.houseareas` |
| Opinião, aprovação, reputação e justiça | Reações às ações, obrigações e queixas | `moralacts.csv`, `moralrules.csv`, `emotions.csv`, `status.csv` |
| Frotas e combate | Composição, atribuição, ataque, defesa e táticas | `tactics.csv`, `updatesExtra.csv`, `pedia.csv` → `Link.combat` |
| Espionagem e segredos | Redes, agentes, coerção e informação | `Core/Intrigue.*.csv`, verbete `Link.secret` |
| Crises | Problemas de administração, medicina, segurança e outros serviços | `Core/Crisis*.csv` |
| Expedições | Artefatos e instalações com resultados próprios | `Core/Expeditions.*.csv` |
| Parentesco e casamento | Relações familiares e autoridade sobre uniões | `kinterms.csv`, verbetes `Link.marriage`, `Link.marriageauthority` |
| Herança e sucessão | Continuidade da casa e escolha do sucessor | `BloodlinesDLC/Inheritance.csv`, `Heir.csv`, verbete `Link.succession` |

Há diferenças históricas de nomenclatura nos arquivos. `roles.csv` usa `Role.Technology`; `skills.csv` inclui `Skill.Medical` e `Skill.Mentoring`. Isso não autoriza renomear IDs ou afirmar que esses conceitos são sempre equivalentes. O texto visível e o sistema correspondente devem ser conferidos no contexto da versão analisada.

## Bloodlines: continuidade da dinastia

A página oficial apresenta o desenho da família inicial, influência sobre o desenvolvimento dos filhos, controle ampliado de sucessão e melhorias que beneficiam a dinastia ao longo das gerações. O catálogo local confirma 16 CSVs dedicados a esse conteúdo.

`ChildUpbringing.csv`, `WardTraits.csv` e `childTraitsBloodlinesDLC.csv` orientam a leitura de criação e tutela. `Inheritance.csv` e `Heir.csv` trazem escolhas sobre continuidade. `CoreBloodlineUpgrades.csv`, `CoreBloodlineUltimates.csv` e `CoreBloodlineSupport.csv` organizam os bônus e suas condições. `Rivals*.csv` e as novas `Expeditions.*.csv` ampliam os eventos relacionados à família.

**Limite de verificação:** os arquivos do DLC existem e há metadado GOG correspondente. O log consultado registra uma verificação de licença do DLC como falsa em uma execução. Isso não permite concluir o estado atual da conta nem que o conteúdo tenha sido efetivamente testado. Traduzir os arquivos não desbloqueia a expansão.

## Desafios concretos para PT-BR

1. **Referências dinâmicas.** `{TargetCharacter}`, `{Actor}`, `{spouseOf(TargetCharacter)}` e outras expressões não são palavras para traduzir. Elas são avaliadas pelo motor. Mesmo duas entradas em inglês idênticas podem ter sujeitos e contextos diferentes.
2. **Pronomes e verbos no código.** A inspeção estática confirmou que `ParsingHelper.he` contém `you/he/she/they`, e que outras funções contêm possessivos ou verbos ingleses. Não basta preservar a expressão e traduzir seu entorno. O adaptador agora oferece 100 unidades próprias para essa gramática, ainda pendentes de tradução; leia [gramatica-dinamica.md](gramatica-dinamica.md). A Ella não deve tentar contornar isso com nomes de funções inventados.
3. **Maiúsculas têm função.** `he` e `He`, `d` e `D` são funções diferentes. Não normalizar a caixa das expressões.
4. **Gênero e perspectiva.** Uma função pode produzir uma referência à personagem do jogador ou a outra pessoa. O trecho precisa funcionar na perspectiva correta e com sujeitos de gêneros diferentes. A tradução automática de artigos e pronomes isolados não resolve esse problema.
5. **Parentesco como composição.** `kinterms.csv` usa padrões e substituições como `$1` e `$2`; isso não é texto livre nem marcação descartável. A gramática de combinações precisa de revisão própria.
6. **Termos políticos próximos.** `ruler`, `head`, `duke`, `baron`, `archon`, `vassal`, `house`, `faction` e `league` referem-se a posições ou estruturas diferentes. Registrar decisões no glossário com contexto e exemplos, sem deduzir equivalência pela tradução comum de dicionário.
7. **Texto curto versus descrição longa.** `Title`, `Short`, `Summary`, `Description` e `Help` atendem a superfícies distintas. A ausência de uma variante no original deve continuar ausente; não preencher células originalmente vazias para aparentar cobertura.
8. **Tags e referências.** `<b>`, `<i>` e `<link="collapse">` pertencem à apresentação e à navegação. Existem tags malformadas nos originais da enciclopédia; o toolkit mantém os tokens existentes e não faz reparos silenciosos.
9. **Integridade do arquivo.** CSVs possuem células multilinha, aspas duplicadas, BOM em muitos arquivos e linhas vazias ao final. Traduzir por linha física ou salvar tudo em uma planilha sem cuidado pode danificar o formato.
10. **Um arquivo incompleto de termos.** `Config/terms.csv` contém cinco linhas com texto e sem chave. O adaptador registra esses locais por posição fixa e bloqueia atualizações desse arquivo até revisão. Isso não é uma identidade semântica confiável entre versões.

## Uso do briefing e questões abertas

Antes de traduzir, ler [formato-localizacao.md](./formato-localizacao.md), [analise-do-motor.md](./analise-do-motor.md) e o relatório de fontes. O briefing fornece contexto factual; a Ella cria e mantém o [glossário](./glossario-ptbr.md) e as [diretrizes](./diretrizes-de-traducao.md).

Questões a resolver com evidência: revisão linguística dos pronomes e verbos adaptados do motor; cobertura de textos fora dos CSVs; tratamento de parentesco em PT-BR; cortes e acentos na interface; compatibilidade com saves e com a distribuição Steam; ativação e testes dos eventos de Bloodlines. A adaptação de engenharia foi documentada e testada isoladamente; as decisões linguísticas precisam ser consistentes entre lotes e confirmadas no jogo.

Este documento evita revelar os desfechos das expedições e os resultados detalhados das escolhas. Ao ampliar a pesquisa com eventos específicos, marcar spoilers e limitar a descrição ao necessário para entender a fala ou a decisão.
