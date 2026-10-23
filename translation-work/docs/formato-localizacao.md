# Formato e invariantes do adaptador

## Perfil real

Instalação GOG Windows `1.0.4.0-gog`, jogo base e recursos de Bloodlines. Engine Unity/Mono. Fontes canônicas são os **105 CSVs ingleses e a DLL original do motor** de `EN/`, com caminhos preservados:

- `Config/`: 14 CSVs com colunas de apresentação explicitamente selecionadas no código.
- `Core/`: 75 CSVs `Key,Text`, associados a pacotes de eventos nativos.
- `BloodlinesDLC/`: 16 CSVs `Key,Text`.
- `StarDynasties_Data/Managed/Pawley.StarDynasties.Engine.dll`: 100 unidades de gramática em 28 métodos, via editor de metadados CLR.

A seleção de colunas está em `native.CONFIG`. Não basta uma coluna conter palavras: IDs, efeitos de táticas, dependências, imagens, categorias, referências, intensidades e números são dados de funcionamento. O parser só oferece à tradução campos de apresentação conhecidos.

Não são fontes deste adaptador: `Config/ai.csv`, `colors.csv`, `general.csv`, `emotion_params.csv`, `moralapplication.csv`, `de_kinterms.csv`, `Config/Localization/de.csv`, TXT de nomes/créditos/notas, XMLs, assets e outras DLLs. O alemão foi examinado como evidência da localização nativa; não é fonte EN e não é instalado como PT-BR. Campos não abrangidos e textos embutidos são uma limitação de cobertura, não entradas concluídas.

Arquivos de eventos XML usam atributos `TextKey` para localizar texto; a inspeção contou 7.562 referências no Core e 3.180 em Bloodlines. Não há motivo comprovado para incluir esses arquivos de lógica como companheiros do pacote CSV. O fato de um pack ter “Test” no nome não justifica eliminá-lo por palpite: os 75 CSVs presentes são catalogados, com o contexto do arquivo preservado.

## Serialização nativa

Todos os CSVs selecionados foram decodificados estritamente como UTF-8. Muitos usam BOM UTF-8 e CRLF; as escolhas são preservadas por arquivo. Há células com aspas, vírgulas e múltiplas linhas, além de muitas linhas vazias e delimitadas no final.

O parser lê a semântica com `csv.reader(..., strict=True)` e mantém, em paralelo, os intervalos exatos de cada célula no texto original. A reconstrução substitui apenas os intervalos traduzidos, em ordem inversa de offset. Campos alterados recebem escape CSV adequado; o restante não é reserializado. O BOM, ordem, campos vazios, aspas não alteradas, quebras internas e linhas finais sobrevivem. Round-trip sem tradução é **idêntico byte a byte** nos 105 recursos reais.

Depois da reconstrução, o resultado é reaberto pelo parser. Cabeçalhos, contagem de linhas, chaves e dados não traduzíveis precisam permanecer iguais. O build também confere os textos reconstruídos contra os valores PTBR aceitos. Isso prova integridade do recurso CSV, não funcionamento visual ou gramatical no runtime.

## Identidade e atualização

Uma unidade tem ID formado por **caminho relativo + chave nativa codificada para URL + coluna**. Exemplo de forma: `Core/Romance.csv#Romance.LoveInterest.Default.Update.Title:Text`.

O índice `row` é somente o local atual de reconstrução. Não é identidade de uma unidade com chave válida. Duas entradas com o mesmo inglês e chaves diferentes continuam distintas. Chaves duplicadas dentro de um arquivo são erro: não se acrescenta um número de ocorrência para disfarçar uma colisão.

`source_sha256` inclui caminho, chave, localizador, coluna, EN e contexto não textual relevante. A linha física fica fora desse fingerprint, permitindo preservar PTBR em reordenações. SHA do arquivo detecta alteração de recurso; o merge por ID/fingerprint decide quais unidades realmente precisam de revisão.

**Exceção documentada:** `Config/terms.csv` possui cinco linhas de texto sem chave. Só o snapshot inicial possui um localizador demonstrável: o slot fixo da linha. Esses registros preservam `key=""`; o ID explicita `@fixed-slot:n`, sem inventar uma chave do jogo. Qualquer alteração de bytes nesse arquivo exige revisão do parser e bloqueia sync; não se presume que posição ou inglês idêntico prove identidade em uma atualização. Reordenar/mudar esse arquivo não é suportado automaticamente.

## Contrato JSONL

Cada linha física é um objeto UTF-8; quebras do texto são escapes JSON. Campos:

| Campo | Responsabilidade |
|---|---|
| `id` | Identidade estável da unidade, com ressalva de slots fixos |
| `source_file`, `key`, `locator`, `row`, `column` | Mapeamento para o recurso nativo |
| `EN` | Original imutável; nos templates CLR, a composição nativa dos literais |
| `context` | Dados da linha necessários para detectar mudança de contexto |
| `source_sha256` | Fingerprint semântico de origem |
| `PTBR` | Único campo de texto preenchido pela Ella; vazio significa pendente |
| `history` | Até três estados anteriores, conservados pelo toolkit |

O manifesto registra esquema, idioma, versão informada, geração aceita, inventário/fingerprints, encoding, contagens, tamanho de lote e hashes de conteúdo/original por batch. O catálogo versionado conserva os campos originais e um snapshot nativo codificado em base64, com SHA por recurso. Isso permite detectar mudanças mesmo se o usuário sobrescrever EN antes de sync e restaurar os originais aceitos em rollback. Base64 é armazenamento, não criptografia nem alegação de licença sobre esses textos.

Criação inicial: 38 lotes de 500 e o último com 47. A inclusão das 100 unidades de gramática ampliou somente o último lote para 147, totalizando 19.147 unidades. Updates preservam os lotes de registros existentes, inclusive buracos deixados por remoções. Novas unidades são anexadas ao último lote elegível ou a novos lotes; não há reorganização global para preencher espaços antigos.

Não editar batches/manifesto/catalogo para evitar os controles. Usar `apply` e `sync`; alterações externas corrompidas ou hashes divergentes são recusados.

## Expressões, tags e limitações

Tokens protegidos incluem a estrutura das expressões entre chaves, com caixa preservada; tags `<...>`; referências `$1`, `$2` etc.; e formatos printf reconhecidos. A validação exige a mesma multiplicidade desses tokens. Reordenar tokens é permitido; apagar, acrescentar ou renomear uma expressão não é. Somente os argumentos literais de apresentação conhecidos podem ser traduzidos, conforme [gramatica-dinamica.md](gramatica-dinamica.md). Controle NUL e Unicode que não codifica em UTF-8 são rejeitados.

O validador preserva até tokens malformados herdados do original, em vez de reparar gramática ou tags silenciosamente. Ele não afirma validar todos os comportamentos de Unity ou a qualidade linguística. Acertos de concordância e extensão de textos exigem revisão; a adaptação de gramática implementada está descrita em [analise-do-motor.md](analise-do-motor.md).

## Publicação e confiança

`PTBR/` só é promovido por `build` completo e habilitado no perfil do motor. Check, apply, sync, update-sources, resume e diff não modificam a saída. Um build interrompido pode ser restaurado por recover; essa restauração não é uma nova geração de pacote.

O build manifest, externo à pasta instalável, liga fontes, catálogo, batches, perfil técnico e hashes nativos. `verify-output` checa essas relações e a completude, sem reconstrução nativa. É uma prova de consistência e detecção de alterações acidentais, **não uma assinatura criptográfica de autoria**: alguém com poder de reescrever todos os dados versionados também pode reconstruir hashes. A CI confia no código/revisão da branch canônica e recusa forks ou SHA arbitrário.

O conjunto completo de EN e PTBR é exclusivo do perfil. Caminhos com travessia, absolutos, nomes reservados, colisões de caixa ou links/junctions são recusados. A instalação original não é destino de escrita de nenhuma operação.

## Unidades CLR

A identidade usa assinatura nativa do método e papel lógico. Os contextos incluem o fingerprint da estrutura IL, sem os textos. A reconstrução sem tradução devolve os bytes originais; uma reconstrução alterada passa por verificação semântica de metadados e IL fora do escopo e reabertura dos 100 valores. Templates possuem exatamente um `{0}`. `[[EMPTY]]` aprova saída vazia apenas nos quatro sufixos autorizados; PTBR vazio continua pendente. Ver o guia de gramática.
