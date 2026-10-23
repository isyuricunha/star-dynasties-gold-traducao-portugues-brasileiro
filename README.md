<div align="center">
  <a href="https://store.steampowered.com/app/1194590/Star_Dynasties/">
    <img src="https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1194590/header.jpg?t=1772458991" alt="Arte oficial de Star Dynasties: uma dinastia humana entre as estrelas" width="650">
  </a>
  <h1>Star Dynasties</h1>
  <p><strong>🇧🇷 Tradução para Português Brasileiro</strong><br>Jogo base + recursos de Bloodlines</p>
  <p><em>A Terra se perdeu. O futuro ainda carrega o nome da sua família.</em></p>
  <p>
    <a href="https://traducao.yuricunha.com/">🌐 Portal de Traduções</a> ·
    <a href="https://github.com/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/releases">📦 Releases — futuras versões</a> ·
    <a href="https://store.steampowered.com/app/1194590/Star_Dynasties/">🎮 Steam</a>
  </p>
</div>

---

## 🚧 Situação do projeto

**Em preparação técnica. Ainda não há tradução disponível para instalar.**

Os recursos de texto foram catalogados, mas a tradução linguística ainda não começou: **0 de 19.047 entradas concluídas**. Há também uma pendência no motor: parte dos pronomes e verbos é produzida em inglês pelo código do jogo. Essa parte precisa de uma adaptação própria antes que o projeto possa gerar e publicar um pacote completo.

Por isso, **a geração do pacote e a publicação estão bloqueadas**. A existência deste repositório e de um fluxo de Releases não significa que uma tradução já esteja pronta. Nenhum teste desta tradução dentro do jogo foi realizado.

## ✨ Sobre a tradução

Em Star Dynasties, uma promessa quebrada pode ser tão perigosa quanto uma frota inimiga. Sua casa cresce, seus parentes se casam, seus aliados cobram favores e seus herdeiros recebem as consequências das decisões de hoje. Entender o que cada personagem pede — e o que está em jogo ao responder — faz parte da experiência.

Este projeto pretende levar os textos acessíveis do jogo ao português brasileiro, preservando a clareza das regras e o tom dos dramas familiares. O escopo técnico inicial reúne **105 arquivos CSV**, com interface, tutorial, enciclopédia, notificações e eventos do jogo base e de **Bloodlines**.

Os números descrevem os textos identificados, não uma porcentagem de toda a interface do jogo. Elementos embutidos no executável, nas bibliotecas ou nas imagens precisam de investigação adicional. Não há dublagem ou substituição de áudio prevista neste pacote.

## 🧭 O que está no escopo?

| Conteúdo identificado | Recursos | Situação |
|---|---|---|
| Ações, mensagens e parte da interface | `Config/text.csv` | Catalogado; tradução pendente |
| Tutorial interativo | `Config/tutorial.csv` | Catalogado; tradução pendente |
| Enciclopédia, história e regras | `Config/pedia.csv` | Catalogado; tradução pendente |
| Cargos, habilidades, táticas, emoções e relações | Demais CSVs selecionados de `Config/` | Catalogados; tradução pendente |
| Intrigas, romances, crises e expedições | 75 CSVs em `Core/` | Catalogados; tradução pendente |
| Herança, criação dos filhos e evolução da dinastia | 16 CSVs em `BloodlinesDLC/` | Catalogados; tradução pendente |
| Pronomes e construções gerados pelo código | Biblioteca do motor | **Adaptação pendente; bloqueia o pacote** |

Ficam fora do pacote atual: executáveis e bibliotecas modificadas, imagens, áudio, listas de nomes próprios, textos de mods e o editor Creator. Os arquivos XML de eventos contêm regras e referências; não serão substituídos pelo adaptador CSV.

## 🌌 Depois da Terra

A humanidade começou a ocupar outros sistemas, mas ainda dependia da Terra e de Sol quando uma catástrofe rompeu essa ligação. A enciclopédia situa a destruição da Terra no século XXII. A causa permanece incerta: o próprio jogo apresenta a hipótese de um experimento descontrolado como uma crença, não como uma verdade revelada.

Séculos depois, as colônias sobrevivem entre máquinas que sabem usar, mas já não compreendem inteiramente. O poder passou às famílias capazes de controlar espaço, recursos e proteção. Essa mistura de tecnologia antiga e obrigações feudais dá ao universo seu caráter: o mapa é espacial, mas a política é pessoal.

### 👑 Uma casa, muitas obrigações

A casa é o centro da vida política. Parentes e conselheiros compartilham interesses, ambições e ressentimentos. Casamentos podem aproximar governantes; disputas por justiça podem afastá-los. Um vassalo espera proteção e autonomia, enquanto seu superior espera tributos e apoio militar.

Colônias formam facções; facções podem integrar ligas. As relações entre esses níveis importam tanto quanto as fronteiras. A narrativa se desenvolve conforme os personagens agem, envelhecem e deixam sucessores. Este projeto não apresenta uma lista fixa de protagonistas ou facções como se toda partida tivesse a mesma história.

### 🧬 Bloodlines: o que fica para os próximos

A expansão oficial aprofunda a continuidade da família: criação da casa inicial, educação dos filhos, escolhas de sucessão e melhorias ligadas à dinastia. Seus arquivos também trazem rivalidades familiares e novas expedições.

Os textos de Bloodlines estão incluídos no catálogo de trabalho. **A tradução não inclui a expansão e não desbloqueia conteúdo pago.** A presença dos arquivos na instalação examinada não comprova que o DLC esteja ativado na conta.

As informações sobre o universo vêm da enciclopédia do jogo e das apresentações oficiais da [Pawley Games](https://gpawley.itch.io/star-dynasties), do [jogo base](https://store.steampowered.com/app/1194590/Star_Dynasties/) e de [Bloodlines](https://store.steampowered.com/app/1852400/Star_Dynasties_Bloodlines/).

## 📦 Download e versões

O download será publicado na página de [GitHub Releases deste projeto](https://github.com/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/releases), após a resolução das pendências técnicas e a conclusão e validação dos textos.

O arquivo instalável terá o nome **`PTBR.zip`**. A primeira publicação estável será **`v1.0.0`**. Pacotes posteriores com conteúdo alterado seguirão `v1.0.1`, `v1.0.2` e assim por diante, acompanhados de um changelog com as alterações verificadas.

**Ainda não existe um `PTBR.zip` publicado.** Baixar o código deste repositório não equivale a baixar uma tradução. A pasta `EN/` contém recursos originais de referência e não deve ser instalada como tradução.

## 🛠️ Instalação — quando houver uma Release

As orientações abaixo descrevem o layout nativo já identificado. A aprovação final de funcionamento depende dos testes que ainda estão pendentes. Confira sempre as instruções e a versão compatível na Release baixada.

1. Feche o jogo.
2. Localize a pasta que contém **`StarDynasties.exe`**. Na instalação GOG examinada, ela é `D:\GOG Games\Star Dynasties`; no seu computador, o caminho pode ser diferente.
3. Guarde uma cópia das pastas **`Config`**, **`Core`** e **`BloodlinesDLC`** fora da instalação. Esse backup permite desfazer as substituições.
4. Baixe **`PTBR.zip`** de uma Release deste projeto e extraia seu conteúdo na raiz do jogo, mesclando as pastas e substituindo os arquivos correspondentes.
5. Para o adaptador de textos atualmente planejado, selecione **English** no menu de idiomas. O pacote substitui os recursos dessa opção; não cria uma opção “Português”.

O ZIP terá os arquivos diretamente nestes caminhos, **sem uma pasta `PTBR` envolvendo tudo**:

```text
Pasta que contém StarDynasties.exe/
├── Config/
│   ├── text.csv
│   ├── tutorial.csv
│   ├── pedia.csv
│   └── demais CSVs do pacote
├── Core/
│   └── CSVs de eventos
└── BloodlinesDLC/
    └── CSVs da expansão
```

Após a instalação, o teste recomendado será conferir o tutorial, abrir a enciclopédia e observar mensagens com personagens diferentes. Isso ajuda a verificar acentos, cortes de texto e concordância. Hoje, esses testes **ainda não foram executados**.

### Restaurar ou desinstalar

Com o jogo fechado, restaure os arquivos das três pastas a partir do backup da **mesma versão do jogo**. Outra opção é restaurar a instalação pelos recursos da sua loja. Não misture originais de versões diferentes. Atualizações do jogo podem substituir os CSVs traduzidos; nesse caso, aguarde um pacote compatível antes de reaplicar.

## ⚙️ Compatibilidade e dúvidas

| Ambiente | Evidência disponível |
|---|---|
| GOG para Windows, `1.0.4.0-gog` | Recursos analisados e preservados; tradução não testada em execução |
| Bloodlines | Recursos identificados; ativação do conteúdo não verificada |
| Steam | Identidade e expansão confirmadas; arquivos dessa distribuição não comparados |
| Mods e outras versões | Compatibilidade não validada |
| Linux, Proton e macOS | Instalação e funcionamento não testados |

<details>
<summary><strong>Por que ainda não há download?</strong></summary>

Os textos estão preparados para o trabalho de tradução, mas continuam pendentes. Além disso, o motor contém funções que geram palavras em inglês. O projeto bloqueia a publicação para evitar apresentar esse resultado como um pacote completo.

</details>

<details>
<summary><strong>O jogo continuará mostrando “English”?</strong></summary>

O adaptador CSV trabalha sobre os recursos do idioma inglês. Uma opção própria de português exigiria outro suporte no motor. A configuração definitiva será confirmada antes da primeira Release.

</details>

<details>
<summary><strong>A tradução exige uma campanha nova?</strong></summary>

Ainda não foi realizado teste de compatibilidade com partidas salvas. Não há fundamento para exigir uma campanha nova nem para garantir compatibilidade neste momento. Guarde seus saves e consulte as notas da futura Release.

</details>

<details>
<summary><strong>Como relatar um problema?</strong></summary>

Use as <a href="https://github.com/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/issues">Issues do repositório</a>. Informe a loja, a versão do jogo e do pacote, os mods utilizados, a tela ou evento afetado e o texto encontrado. Uma captura de tela com contexto ajuda a localizar a entrada correta. Não envie saves ou arquivos pessoais publicamente sem conferir seu conteúdo.

</details>

## 🔄 Atualizações e histórico

Cada Release trará a relação de recursos alterados e as diferenças de texto identificadas desde a versão anterior. Uma mudança técnica no arquivo não será anunciada como uma revisão de tradução se os textos permanecerem iguais.

Mudanças apenas na documentação ou no trabalho de tradução em andamento não publicam pacotes. O download público só será criado a partir de uma saída completa e validada, com os bloqueios técnicos resolvidos.

## 🌐 Comunidade e apoio

Conheça outros projetos e os canais de ajuda no [Portal de Traduções](https://traducao.yuricunha.com/). Sugestões e relatos específicos deste jogo podem ser acompanhados nas [Issues](https://github.com/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/issues).

Se quiser apoiar voluntariamente o trabalho, a chave **Pix é `pix@yuricunha.com`**. O apoio não é obrigatório para usar o material disponibilizado gratuitamente neste repositório.

## 📜 Licença

O conteúdo original deste projeto é disponibilizado ao público sob a **[Creative Commons Atribuição–NãoComercial–CompartilhaIgual 4.0 Internacional](https://creativecommons.org/licenses/by-nc-sa/4.0/)**. O texto jurídico completo está em [LICENSE](./LICENSE) e permanece inalterado.

- **BY — Atribuição:** dê crédito aos autores e indique as mudanças realizadas.
- **NC — NãoComercial:** a licença pública não autoriza reutilização para fins comerciais.
- **SA — CompartilhaIgual:** adaptações compartilhadas devem usar a mesma licença ou uma licença compatível autorizada.

A manutenção é de **Yuri Cunha**. A licença alcança a tradução original, a documentação e outros materiais sobre os quais os contribuidores possam conceder direitos. **Ela não licencia os textos originais do jogo, executáveis, imagens, marcas ou outros recursos da Pawley Games, Iceberg Interactive ou terceiros.** Arquivos nativos que incorporem material do jogo continuam sujeitos a esses direitos; incluir `LICENSE` não concede autorização para redistribuir o jogo. Avisos e licenças de terceiros devem ser preservados.

Separadamente, a [autorização adicional para integração oficial](./GAME-DEVELOPER-PERMISSION.md) permite à desenvolvedora ou titular legítima do jogo, e à editora e demais partes que atuem sob sua autorização, incorporar e adaptar a tradução em versões oficiais do mesmo jogo, **inclusive comerciais, gratuitamente, de forma não exclusiva e sem royalties adicionais, com créditos adequados**. Ela abrange somente o conteúdo cujos titulares tenham concedido expressamente os direitos necessários.

Essa autorização não modifica a licença Creative Commons nem estende a permissão comercial ao público em geral. No seu escopo específico de integração oficial, os direitos adicionais não ficam limitados pelas condições NãoComercial e CompartilhaIgual da licença pública. A titularidade das contribuições permanece com seus autores; direitos de terceiros e direitos morais que não possam ser legalmente renunciados são preservados.

## 🤝 Contribuições

Relatos de problemas, sugestões e revisões são bem-vindos. O [guia de contribuições](./CONTRIBUTING.md) explica como participar e diferencia essas formas de ajuda das contribuições com novos textos autorais.

Para incorporar conteúdo autoral, o projeto exige consentimento afirmativo e registrável para uso e adaptação, distribuição pública sob CC BY-NC-SA 4.0 e concessão dos direitos adicionais de integração oficial descritos acima. A confirmação do modelo de PR começa desmarcada e precisa ser conferida e preservada no histórico antes da incorporação. Enviar uma contribuição não implica aceitação automática, e autorizações anteriores não comprovadas não serão presumidas.

## ✦ Créditos

**Projeto de tradução e manutenção:** Yuri Cunha. A tradução linguística está em preparação; não há conteúdo traduzido concluído para creditar nesta versão.

As contribuições autorais futuras serão creditadas conforme a autoria, o escopo e a atribuição registrados nos respectivos PRs. A inclusão de um crédito, por si só, não comprova autorização para integração oficial comercial; essa permissão exige o consentimento descrito em [CONTRIBUTING.md](./CONTRIBUTING.md).

**Star Dynasties:** desenvolvido pela **Pawley Games**, publicado pela **Iceberg Interactive**. Jogo base lançado em 1º de setembro de 2021; Bloodlines em 9 de março de 2022. Arte do cabeçalho vinculada à página oficial na Steam.

Este é um projeto independente de fãs, sem vínculo oficial com os titulares do jogo. Star Dynasties e os demais nomes e marcas pertencem aos seus respectivos titulares.

---

<div align="center">
  <p>🌌 <em>Entre colônias distantes, cada palavra pode mudar uma aliança.</em></p>
  <p><a href="https://traducao.yuricunha.com/">Mais histórias em português brasileiro</a></p>
</div>
