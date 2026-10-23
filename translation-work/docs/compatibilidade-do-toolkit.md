# Compatibilidade do toolkit: Windows e Linux ARM64

## Ambiente validado

O adaptador de metadados e gramática foi executado em Windows com Python 3.14 / .NET Framework 4.x e em Linux **aarch64 (ARM64)** com Python 3.12.3 / Mono 6.8.0.105. Nos dois ambientes, a leitura da DLL original reconheceu as 100 unidades de gramática, o CSV e os JSONLs passaram pelo `check` e as 111 verificações isoladas do motor passaram com dependências originais autorizadas.

A mesma tradução sintética produziu uma DLL de 4.276.224 bytes, SHA-256 `f8e32175a1096ca1a140f781b4384155b383ce2bed930f7de2f17f2ce59df034`, em ambos os ambientes. Essa amostra existe apenas para testes; não é uma tradução aprovada. O compilador `mcs` também recompilou e executou o auxiliar offline no ARM64.

Essa validação cobre a preparação dos arquivos. Os testes visuais de jogo continuam limitados ao [menu já documentado](teste-menu-ptbr.md); a campanha e a gramática adaptada em partida permanecem pendentes.

## Dependências e uso

Use Python 3.10+ e Git. No Windows, o auxiliar usa .NET Framework 4.x. No Linux, precisa de Mono e System.Web.Extensions; a recompilação e os testes que compilam o harness também precisam de `mcs` (incluído em `mono-devel`). Instalar pacotes é uma ação explícita do responsável pelo ambiente. Nenhum comando do toolkit instala dependências ou acessa APIs de tradução.

Execute na raiz do repositório:

```sh
python3 translation-work/toolkit.py status
python3 translation-work/toolkit.py check
python3 translation-work/toolkit.py resume
python3 -m unittest discover -s translation-work/tests -v
```

O auxiliar incluído é AnyCPU. Ele carrega o Mono.Cecil do caminho privado em `vendor/` antes de invocar por reflexão o código que depende dessa biblioteca. Não requer `MONO_PATH`, instalação no GAC ou cópia extra da dependência ao lado do executável. A execução a partir de outro diretório também foi testada. A separação segue os contratos de [carregamento de assemblies e AssemblyResolve do .NET](https://learn.microsoft.com/en-us/dotnet/standard/assembly/resolve-loads).

`verify-output` e o empacotamento de uma saída já construída continuam sem executar CLR. O teste de execução real do motor exige as dependências originais, lidas a partir de `.state/local-install.json`. Num checkout sem essas dependências, esse teste informa explicitamente que foi ignorado; os testes de metadados usam a DLL canônica já presente em EN.

## Falhas corrigidas

1. **Fingerprints de CRLF após checkout LF.** `engine-shapes.json` e `toolchain.json` tinham sido gravados com CRLF, mas o Git versionava LF. Agora os arquivos de engenharia são gravados em LF antes do cálculo dos hashes. A verificação continua exigindo igualdade exata dos bytes. Uma regressão verifica o conteúdo no índice Git e numa exportação nova, com `core.autocrlf=true`, incluindo a preservação dos bytes do CSV nativo.
2. **Carregamento do Mono.Cecil.** O launcher anterior referenciava diretamente o código dependente de Cecil, permitindo que a resolução ocorresse antes da instalação do handler no Mono. O bootstrap agora carrega a biblioteca privada e adia a entrada dependente para uma chamada por reflexão.
3. **Sonda com entrada vazia.** `inspect-stdin` exige a DLL em base64. Uma linha vazia não é um assembly e agora recebe um erro explícito de payload vazio. Essa sonda não serve para diagnosticar incompatibilidade de arquitetura. O teste positivo usa a DLL real.

Os originais em EN, os bytes de PTBR e as dependências binárias mantêm suas regras de preservação; não aplique conversão global de fim de linha a recursos do jogo.

## Recompilação e recuperação

O auxiliar já está incluído e não precisa ser recompilado para traduzir. Depois de uma alteração de engenharia autorizada:

```sh
python3 translation-work/managed/build-helper.py
```

No Windows, use `python` no lugar de `python3`; `build-helper.ps1` também encaminha ao mesmo comando. O build é offline, usa `csc` no Windows ou `mcs` no Linux e grava `toolchain.json` com LF. Se os arquivos já correspondem aos hashes, não recompila nem modifica nada. Entradas de engenharia com CR são recusadas para impedir novos fingerprints incompatíveis com o Git.

Após recompilar, execute os testes e revise os fingerprints de `runtime-support.json`, incluindo o hash atualizado do próprio `toolchain.json`. O recompilador não aprova esse perfil automaticamente. Não corrija um erro apenas removendo guards, exportando `MONO_PATH` ou substituindo hashes sem conferir os bytes.

Para atualizar um checkout antigo com correções locais de diagnóstico, preserve essas alterações antes de aplicar a revisão corrigida. O registro da validação está em [portability-validation.json](../reports/portability-validation.json).
