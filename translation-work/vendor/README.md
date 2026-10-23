# Dependência de engenharia: Mono.Cecil

O adaptador de gramática usa **Mono.Cecil 0.11.6**, distribuição `net40`, sob sua licença **MIT**. A biblioteca inspeciona e regrava metadados/IL sem executar o jogo. Ela é usada na máquina de preparação e não integra a DLL do jogo nem o pacote PTBR.zip.

- Origem oficial: https://www.nuget.org/packages/Mono.Cecil/0.11.6
- Pacote: https://api.nuget.org/v3-flatcontainer/mono.cecil/0.11.6/mono.cecil.0.11.6.nupkg
- Projeto: https://github.com/jbevain/cecil
- Documentação: https://www.mono-project.com/docs/tools%2Blibraries/libraries/Mono.Cecil/
- Texto MIT original: [mono-cecil-0.11.6/LICENSE.txt](mono-cecil-0.11.6/LICENSE.txt), obtido de https://raw.githubusercontent.com/jbevain/cecil/0.11.6/LICENSE.txt
- Metadado original do pacote: [Mono.Cecil.nuspec](mono-cecil-0.11.6/Mono.Cecil.nuspec).
- SHA-256 do `.nupkg`: `d2a23832aaa948ba9a01acc42b5726e34c5f995958f1b30d45c0e7c70b3a72d5`.
- SHA-256 de `lib/net40/Mono.Cecil.dll`: `c41bdb9ffd3c5f6e17d2382c1012d73703e035e3f1100245fdd4e08c8dc6eb5b`.

A licença pública CC do repositório não substitui a licença MIT desta dependência nem os direitos sobre o jogo. Não há downloads em `extract`, `sync`, `build`, `check` ou CI. O binário, os fontes do adaptador e seus hashes estão incluídos para uso offline.

O utilitário próprio está em `translation-work/managed/GrammarTool.exe`, com fontes C# ao lado e [recompilador offline para Windows/Linux](../managed/build-helper.py). No Windows, usa .NET Framework 4.x; em outro sistema, a execução do utilitário exige Mono com System.Web.Extensions. A verificação rápida e o empacotamento de uma Release já construída continuam em Python, sem executar CLR.
