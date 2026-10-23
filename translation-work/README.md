# Toolkit de localização — Star Dynasties

Workspace de engenharia e tradução manual, dentro do mesmo repositório público. **Sayuri prepara a infraestrutura; Ella decide a linguagem e traduz.** O README da raiz é destinado aos jogadores; este documento é o guia técnico.

## Estado da entrega

- Base examinada: GOG Windows `1.0.4.0-gog`, recursos do jogo base e Bloodlines.
- 105 CSVs e uma DLL em `EN/`; 19.147 unidades em 39 JSONLs: 38 lotes de 500 e um de 147.
- Todas as traduções estão pendentes. Não houve tradução automática, aprovação fictícia ou execução de carga linguística.
- O **briefing inicial já foi pesquisado e escrito pela desenvolvedora** em [docs/briefing-do-jogo.md](docs/briefing-do-jogo.md). Ella não precisa criá-lo do zero.
- **Adaptação de gramática implementada:** 100 unidades em 28 métodos, com testes isolados do motor. Todas continuam pendentes para a Ella. Evidência em [docs/analise-do-motor.md](docs/analise-do-motor.md); perfil verificável em [runtime-support.json](runtime-support.json).
- Não existe `PTBR/` neste estado incompleto. Não existe Release publicada pelo toolkit. O fluxo de Release está implementado e é exercitado com fixtures; não foi executado no GitHub.

O toolkit permite traduzir os recursos catalogados e a gramática mapeada. **A tradução permanece incompleta.** A próxima etapa é a revisão linguística pela Ella e, após a conclusão, teste visual e de campanha em ambiente autorizado. O escopo não comprova cobertura de todo texto embutido na interface. Leia [docs/gramatica-dinamica.md](docs/gramatica-dinamica.md).

## Preparação

Use Python **3.10+** e Git. A leitura/reconstrução da DLL exige .NET Framework 4.x no Windows ou Mono com System.Web.Extensions. O auxiliar e Mono.Cecil 0.11.6 estão incluídos offline com seus hashes e licença MIT. A verificação rápida da Release exige apenas Python; não compila nem executa CLR. O desenvolvimento foi testado com Python 3.14 no Windows; o workflow usa Python 3.14. Não há dependências de tradução, clientes de modelos, serviços de inferência ou chaves de API. A publicação usa apenas o token temporário do GitHub Actions.

Execute os comandos da raiz do repo:

```powershell
python translation-work/toolkit.py status
python translation-work/toolkit.py check
python -m unittest discover -s translation-work/tests -v
```

A suíte usa diretórios temporários para aplicar valores sintéticos, criar commits/tags de fixture e simular publicação. **Ela não traduz, faz commits ou instala arquivos no projeto real nem na instalação do jogo.** Os testes leem os originais, comprovam round-trip e estado pendente e executam a gramática em cópia temporária com ambiente controlado. As 111 verificações isoladas não substituem um teste completo no Unity. O harness de execução exige Windows, o compilador C# do .NET Framework e a instalação original verificada por `update-sources`, registrada em `.state/local-install.json`: suas dependências são lidas, sem alteração, e não são redistribuídas pelo toolkit. O editor de metadados de produção usa somente a dependência incluída em `vendor/`.

## Organização e propriedade

```text
.github/workflows/release.yml        publicação futura, restrita a main/PTBR
EN/Config/                          originais gerenciados, mesmos caminhos do jogo
EN/Core/
EN/BloodlinesDLC/
EN/StarDynasties_Data/Managed/        DLL original do motor
translation-work/toolkit.py          CLI
translation-work/native.py           parser e reconstrução por células
translation-work/managed_codec.py    contrato das 100 unidades de gramática
translation-work/managed/            editor C# offline, perfil e fingerprints
translation-work/vendor/             Mono.Cecil e licença MIT
translation-work/storage.py          lock, journal, recuperação, retenção
translation-work/release.py          ZIP, SemVer, changelog e GitHub Release
translation-work/trusted-distributions.json
translation-work/runtime-support.json
translation-work/source-catalog.json catálogo aceito + snapshot nativo verificável
translation-work/translations/       manifest.json e batches JSONL
translation-work/docs/               briefing, formato e passagem à Ella
translation-work/tests/              fixtures e regressões
translation-work/reports/            último diff, checkpoint e futuro build manifest
translation-work/.state/             ignorado: máquina local e recuperação
translation-work/dist/               ignorado: ZIPs gerados
PTBR/                               só passa a existir após build completo habilitado
LICENSE                             texto oficial completo, fora do ZIP
README.md                           apresentação e instruções para jogadores
```

`EN/` e `PTBR/` espelham `Config/`, `Core/`, `BloodlinesDLC/` e a DLL do motor em `StarDynasties_Data/Managed/` da raiz que contém `StarDynasties.exe`. O adaptador atual não cria um idioma novo: a proposta de implantação substitui recursos usados com **English**. XMLs, executáveis, outras bibliotecas, assets, listas de nomes e alemão não são copiados para a saída.

As regras de `.gitattributes` impedem normalização de fim de linha em `EN/`, `PTBR/` e `LICENSE`. Preservá-las é necessário, especialmente em máquinas com `core.autocrlf=true`.

## Importar ou atualizar os originais

```powershell
# Autodetecção limitada, seguida de verificação do original
python translation-work/toolkit.py update-sources

# Caminho explícito, inclusive com espaços
python translation-work/toolkit.py update-sources --game-root "D:\GOG Games\Star Dynasties"

# Inspecionar sem escrever em EN, JSONL, PTBR ou estado local
python translation-work/toolkit.py update-sources --game-root "D:\GOG Games\Star Dynasties" --dry-run
```

A prioridade é: `--game-root`, se informado; caso contrário, caminho local anteriormente verificado e candidatos limitados do registro GOG, metadados Steam e duas localizações GOG conhecidas. Todos os candidatos precisam passar na verificação; mais de um original distinto é ambiguidade. Não há varredura de discos nem acesso mágico a uma máquina remota.

**Verificação de originalidade:** `trusted-distributions.json` contém hashes dos CSVs e metadados/DLLs de identidade da instalação fornecida por Yuri. É uma baseline local revisada, não uma assinatura independente da distribuidora. Uma cópia traduzida, incompleta ou alterada é recusada. Steam é detectável por seu AppID, mas seus recursos não foram aprovados como equivalentes aos da GOG.

Uma versão nova, desconhecida, **não é aprovada automaticamente por se parecer com o jogo**. Use a inspeção somente leitura:

```powershell
python translation-work/toolkit.py inspect-source --game-root "CAMINHO_DO_ORIGINAL"
```

Após confirmar origem, versão, conjunto de arquivos e formatos, a manutenção revisa e registra uma distribuição adicional em `trusted-distributions.json`, preservando as anteriores. Não copie hashes de uma instalação modificada para fazê-la parecer original. O toolkit não promove a saída de `inspect-source` a um perfil de confiança sozinho.

Em um servidor Linux sem o jogo, use originais obtidos pelo responsável e `sync --input`; ou execute `update-sources --game-root` na máquina que realmente tem acesso à instalação.

## Sincronizar fontes já copiadas

```powershell
# EN foi atualizado manualmente
python translation-work/toolkit.py diff
python translation-work/toolkit.py sync

# Árvore completa externa: caminhos Config/, Core/, BloodlinesDLC/
python translation-work/toolkit.py sync --input "D:\fontes originais revisadas"

# Um arquivo isolado: destino nativo obrigatório
python translation-work/toolkit.py sync --input "D:\entrada\Events.csv" --source-file "Core/Events.csv"

# Somente para exclusão intencional e revisada; repetir a flag para cada arquivo
python translation-work/toolkit.py sync --allow-remove "Core/ArquivoRemovido.csv"
```

`extract` é um alias de `sync` para a criação a partir de EN/árvore fornecida. `--batch-size` controla apenas a criação inicial; o padrão é 500. Não executar importações de fontes sem confirmar que são inglesas originais: `sync` é o caminho explícito para candidatos fornecidos pelo responsável e não prova sua procedência sozinho.

O algoritmo é o mesmo em `sync` e `update-sources`. Ele compara unidades com o catálogo **anteriormente aceito**, não com os bytes de EN que podem já ter sido sobrescritos. Texto ou contexto alterado invalida somente a unidade correspondente; a tradução anterior permanece em `history`. Reordenação preserva PTBR e lote. Renomear uma chave é remoção + adição, sem aproximação textual.

Arquivos ausentes não significam exclusão autorizada: o conjunto exato exige `--allow-remove`. Fontes essenciais não podem desaparecer. O arquivo `Config/terms.csv` tem identidade ambígua e não aceita atualização automática. CSV novo de eventos é descoberto; CSV desconhecido em Config exige classificação do parser.

O relatório [reports/sync-latest.json](reports/sync-latest.json) contém gerações, caminhos, IDs, lotes, contagens, textos anteriores/atuais e PTBR anterior. [reports/sync-latest.md](reports/sync-latest.md) resume a operação. A geração impressa é a referência: um erro posterior não transforma o relatório antigo em uma sincronização nova. A CLI também retorna o identificador do journal de recuperação.

## Aplicar traduções manuais

Ella lê um lote e trabalha em grupos do tamanho que conseguir revisar com precisão. **500 é o tamanho de armazenamento, não uma exigência de traduzir tudo de uma vez.** Não editar os campos de fonte nem salvar o JSONL diretamente: use `apply`, que atualiza seus hashes e protege o estado aceito.

Payload UTF-8, mantido fora de `PTBR/`, por exemplo em `translation-work/.state/payload.json`:

```json
{
  "generation": "copiar o valor exato do manifest.json",
  "expected_count": 1,
  "entries": [
    {
      "batch": "batch-0001.jsonl",
      "id": "copiar o id exato do registro",
      "source_sha256": "copiar o fingerprint exato do registro",
      "PTBR": "texto escrito e revisado por Ella"
    }
  ]
}
```

```powershell
python translation-work/toolkit.py apply translation-work/.state/payload.json
python translation-work/toolkit.py check
python translation-work/toolkit.py checkpoint
python translation-work/toolkit.py resume
```

O exemplo explica o contrato; não é um payload executável com valores reais. `PTBR=""` continua pendente. Preservar inglês intencionalmente exige escrevê-lo explicitamente em PTBR. `apply` não inventa traduções nem reutiliza textos de outros contextos.

Entradas tecnicamente inválidas são rejeitadas com o motivo e as válidas do mesmo payload podem ser aceitas. Código de saída 2 indica rejeições parciais; repetir apenas o que ficou pendente. Duplicatas, geração errada ou estrutura incorreta rejeitam a requisição inteira. Para corrigir um PTBR existente após revisão, usar `apply --replace`; os três estados anteriores mais recentes ficam no histórico da entrada. Cada item informa seu batch para que uma aplicação não precise reescrever os outros lotes.

`status` e `resume` mostram pendências, estado da saída, bloqueios do motor e armazenamento. `checkpoint` registra um resumo verificado. Fazer commits frequentes de `EN/`, JSONL, catálogo e documentação preserva o histórico durável. O toolkit **não faz commit nem push**.

## Build, validação e pacote

```powershell
python translation-work/toolkit.py check --complete
python translation-work/toolkit.py build
python translation-work/toolkit.py verify-output
python translation-work/toolkit.py package --output translation-work/dist/PTBR.zip
```

**Hoje, o build deve falhar porque todas as 19.147 traduções estão pendentes.** O adaptador de gramática está implementado; o perfil registra seus hashes validados. Não gere uma saída parcial.

Somente `build` pode promover uma árvore nativa PTBR. Antes disso, verifica todas as entradas, fontes, contexto, tokens e perfil do motor; reconstrói em memória, reabre os CSVs e a DLL e só então prepara a transação. O build manifest fica em `translation-work/reports/build-manifest.json`, fora da pasta instalável. Saída anterior válida é preservada em caso de falha e marcada como stale por comparação de fingerprints quando houver progresso novo.

`verify-output` é uma conferência de hashes, inventário, completude e tokens, sem reconstruir arquivos, interpretar novamente o CSV ou executar CLR. Confere EN, catálogo, JSONLs, perfil técnico e cada arquivo nativo. Um `complete=true` isolado não libera o pacote. O ZIP tem os caminhos nativos diretamente na raiz, sem `PTBR/`, sem LICENSE/README/ferramentas.

## Recuperação e espaço em disco

Operações de escrita usam lock de processo liberado pelo sistema quando o processo termina. Editores externos são detectados por precondições de hashes antes da promoção; não edite arquivos enquanto uma operação estiver em andamento. A CLI tenta restaurar transações interrompidas antes de uma nova escrita. Comandos de leitura recusam uma geração interrompida e apontam a recuperação.

```powershell
python translation-work/toolkit.py recover
python translation-work/toolkit.py rollback
python translation-work/toolkit.py gc --dry-run
python translation-work/toolkit.py gc
```

O journal guarda **somente arquivos modificados**: bytes anteriores, hashes e plano de promoção. Apply de uma entrada escreve o lote correspondente e o manifesto; não copia a árvore toda. Após verificação, as cópias staged são removidas. Sync guarda o catálogo nativo completo, justificadamente, porque pode mudar as fontes; os originais aceitos continuam recuperáveis mesmo quando EN foi sobrescrito antes da sincronização.

Padrão de retenção: **até 10 snapshots concluídos e 512 MiB**, com **16 MiB de espaço livre adicional** para segurança. `translation-work/storage-policy.json` pode sobrescrever `max_completed`, `max_bytes` e `min_free_bytes` com inteiros positivos. Esse arquivo só é necessário para mudar a política. Uma transação que não cabe no orçamento falha antes de promover arquivos; não há modo ilimitado implícito.

GC remove apenas snapshots concluídos elegíveis e mantém o mais recente. Receipts, hashes, caminhos e conteúdo são verificados antes da remoção. Journals ativos, staging interrompido, arquivos desconhecidos, links/junctions ou recibos corrompidos bloqueiam a limpeza. `gc --dry-run` não escreve. `status` informa quantidade, bytes, política e espaço recuperável.

`recover` restaura os bytes anteriores de uma promoção interrompida, inclusive se a interrupção ocorreu durante uma recuperação anterior. Se houver edição externa conflitante ou receipt ausente/corrompido, falha sem apagar dados e exige revisão. Uma pasta criada no instante anterior à persistência do receipt pode exigir essa revisão manual; a ferramenta não presume que diretórios sem comprovante sejam descartáveis.

`rollback` desfaz a última transação compatível enquanto ela estiver retida; recusa alterações posteriores conflitantes. Uma sincronização também restaura EN a partir do snapshot nativo anterior. Rollback de build não é automático: restaure uma revisão conhecida com Git após revisão, para não usar um comando de progresso como instalador de saída. Recuperação de um build interrompido é a exceção necessária para restaurar a saída anterior.

O journal local é recuperação de curto prazo, **não substitui Git**. As últimas três versões da entrada e o último relatório mantêm contexto imediato; exclusões e histórico mais antigo dependem de commits que o responsável efetivamente fizer. Antes de atualizar fontes ou limpar estado, registrar o progresso no Git é a prática recomendada. Nenhum snapshot completo novo é acumulado a cada tradução.

## GitHub Actions e teste de publicação

O workflow só aceita o repositório canônico em `main`. Push que altera `PTBR/**` e `workflow_dispatch` são os gatilhos; progresso em EN/JSONL/README não publica. O inicializador manual serve também quando um primeiro build completo já está versionado. Não foi disparado durante esta entrega.

O fluxo executa `verify-output`, cria o ZIP, confere seus membros e compara os bytes PTBR com a maior Release estável publicada. Sem Release anterior: `v1.0.0`; conteúdo diferente: incremento apenas do patch; bytes idênticos: nenhuma versão nova. Drafts e prereleases não são a base de versão. Tags não ancestrais, versões ambíguas e metadados ausentes falham. Tags existentes nunca são movidas.

A publicação reserva o tag no SHA exato, cria ou retoma um draft compatível, envia PTBR.zip, verifica tamanho e digest e só depois publica. Notas comparam IDs/textos JSONL e arquivos nativos reais. O job é serializado e consulta novamente o HEAD remoto antes de publicar; se a branch avançou, a execução antiga falha. Interrupção após reservar tag/draft é retomável no mesmo SHA. Um asset divergente não é apagado automaticamente.

**Teste real no GitHub: não realizado.** As fixtures exercitam planejamento, primeiro/segundo release, retries e API simulada; não comprovam permissões, configurações ou resposta real do GitHub. Plano para o mantenedor, quando houver build autorizado e completo:

1. Versionar o conjunto consistente: EN, catálogo, JSONL, perfil técnico, PTBR e build manifest.
2. Enviar à `main` quando autorizado, ou usar “Run workflow” na branch padrão para inicialização.
3. Conferir SHA do tag, notas, asset PTBR.zip e hashes do download.
4. Reexecutar sem alterar saída e confirmar ausência de nova versão.
5. Em uma revisão posterior completa, conferir incremento de patch e diff factual.

Nenhuma Release, mensagem externa, commit ou push foi realizado por esta entrega.

## Primeiros passos da Ella

1. Ler o **briefing já pesquisado** e a análise do motor. Ler também o guia de gramática dinâmica antes de traduzir os novos campos.
2. Consultar fontes e corrigir/ampliar fatos somente com evidência nova.
3. Criar as decisões linguísticas nos arquivos de glossário e diretrizes. Eles começam sem decisões aprovadas.
4. Executar `status` e `check`; ler o manifesto e o último diff.
5. Trabalhar nos JSONLs em grupos pequenos; aplicar pelo payload com fonte e geração exatas.
6. Validar, revisar e registrar o progresso em commits autorizados, sem tocar PTBR.
7. Nas atualizações, usar `update-sources` ou `sync`, revisar apenas unidades afetadas e consultar `history`.
8. Completar e revisar os textos e a gramática, gerar build explicitamente e testar no ambiente autorizado.

Sequência detalhada em [docs/fluxo-de-traducao.md](docs/fluxo-de-traducao.md).

## README público e licença

O README público já inclui arte oficial verificada, universo, escopo real, situação honesta, instalação/restauração, compatibilidade, suporte, portal, Pix e créditos. Depois da **primeira publicação efetiva**, atualize status, cobertura medida, compatibilidade verificada e links reais do pacote/changelog, sem reduzir a apresentação existente. Uma edição só de README não deve publicar nova Release.

`LICENSE` contém os **20.850 bytes do texto oficial CC BY-NC-SA 4.0**, obtido da [Creative Commons](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt), SHA-256 `e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd`. Não está dentro de PTBR/ZIP. Os direitos do jogo e de terceiros permanecem separados, como explica o README público. Creative Commons não recomenda suas licenças para software; nenhuma licença separada foi inventada para o toolkit. Mono.Cecil conserva sua licença MIT em `vendor/`; os direitos dessa dependência não são substituídos pela licença do projeto.

**Histórico da licença:** o arquivo foi preparado antes da tradução e integra a base de engenharia versionada do repositório. Esta implementação de gramática não faz commit ou push.
