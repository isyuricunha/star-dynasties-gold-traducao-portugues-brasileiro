# Adaptação da gramática do motor

## Problema e solução implementada

A inspeção da instalação GOG Windows `1.0.4.0-gog` confirmou palavras inglesas em `Pawley.StarDynasties.Engine.dll`, além dos CSVs. Por exemplo, `{he(Actor)}` seleciona `you/he/she/they`. Traduzir apenas a frase ao redor deixaria partes em inglês.

O toolkit agora cataloga **100 unidades de gramática em 28 métodos**. O original permanece em `EN/StarDynasties_Data/Managed/Pawley.StarDynasties.Engine.dll`. A reconstrução acontece em memória a partir desse original; só um build completo pode produzir a DLL de saída em PTBR. Nenhum comando instala arquivos no jogo.

O suporte inclui pronomes, reflexivos, possessivos, conjunção de listas, sufixos `s/es`, frases com verbos e referências a personagens, além das construções de parentesco mapeadas. As frases possuem formas independentes para jogador, masculino, feminino e referência desconhecida, conforme o contrato de cada método. Templates usam exatamente um `{0}` para inserir a referência nativa, conservando o contexto do vínculo clicável.

## Integridade e dependências

O editor offline usa Mono.Cecil 0.11.6, com licença MIT preservada em `../vendor/`. Código C# e executável auxiliar estão em `../managed/`; fingerprints verificam sua correspondência e a dependência fixada. Para ler/reconstruir assemblies, exige .NET Framework 4.x no Windows ou Mono com System.Web.Extensions. A DLL gerada conserva o runtime CLR e as referências do original. Nenhuma dependência do auxiliar é acrescentada ao jogo. O carregamento privado do Mono.Cecil e a canonização LF dos fingerprints foram corrigidos e testados em Linux ARM64, conforme [compatibilidade-do-toolkit.md](compatibilidade-do-toolkit.md).

A estrutura dos métodos originais é conferida contra `engine-shapes.json`. Uma alteração estrutural desconhecida exige revisão; uma mudança isolada de texto invalida apenas a unidade afetada. Assemblies assinados ou já localizados não são aceitos como novos originais.

A reconstrução é determinística. Sem alterações de texto, retorna os bytes originais. Com alterações, compara identidade do assembly, runtime, referências, tipos, campos, propriedades, eventos, assinaturas, recursos embutidos e corpos dos métodos fora do escopo. O resultado é reaberto e os 100 valores são comparados com os aprovados. Não se promete igualdade de todos os bytes de uma DLL reserializada.

## Texto dentro das expressões

O validador permite traduzir argumentos textuais de apresentação conhecidos dentro das expressões dos CSVs. Preserva funções, condições, variáveis, ordem e quantidade de argumentos, IDs e strings de lógica. Sintaxe desconhecida continua protegida integralmente. O contrato está em [gramatica-dinamica.md](gramatica-dinamica.md).

## Validação e limites

O teste isolado executou **111 verificações** nos métodos reais de gramática, LazyText, referências e expressões compiladas. Usou uma cópia temporária da DLL com substituições de ambiente apenas no harness: jogador, visibilidade e acesso à interface. Essas substituições não fazem parte da reconstrução de produção. Confirmou acentos, casos nulos, conjunção de listas, parentesco e identidade do objeto nos elementos clicáveis.

Um [teste manual posterior do menu](teste-menu-ptbr.md), confirmado por captura fornecida por Yuri, validou os glifos Á, É, Ã, Õ e Ç nos oito botões visíveis, sem cortes aparentes e sem modificação das fontes. Esse teste usou somente alterações em `Config/text.csv`; não exercitou a DLL adaptada.

A execução completa da tradução no Unity permanece pendente. Ainda são necessários revisão linguística, inspeção visual de outros glifos e telas, concordância da gramática dinâmica em partida, campanhas salvas, eventos de Bloodlines e compatibilidade com outras distribuições. O suporte não afirma catalogar todos os textos embutidos em toda a interface.

O perfil [runtime-support.json](../runtime-support.json) registra o escopo e hashes do adaptador. Alterações nesses arquivos exigem revalidação antes de um novo build. A DLL de gramática é uma fonte obrigatória do perfil; excluí-la do catálogo não libera um pacote somente de CSVs. A autorização técnica não aprova traduções: todas as 19.147 unidades continuam pendentes e impedem build/publicação. As decisões de português pertencem à Ella.
