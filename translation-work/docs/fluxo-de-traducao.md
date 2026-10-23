# Passagem para Ella

O briefing inicial do jogo **já foi pesquisado e escrito pela desenvolvedora do toolkit**. A responsabilidade da Ella é ler, conferir contexto, definir a linguagem e traduzir manualmente. Expandir o briefing com fatos novos é bem-vindo; sua autoria inicial não foi deixada como tarefa pendente.

1. Ler [briefing-do-jogo.md](briefing-do-jogo.md), [analise-do-motor.md](analise-do-motor.md), [formato-localizacao.md](formato-localizacao.md) e o [guia técnico](../README.md).
2. Ler [gramatica-dinamica.md](gramatica-dinamica.md): traduzir também as 100 unidades do motor. Não prometer pacote jogável antes da revisão e dos testes no jogo.
3. Criar e manter [diretrizes-de-traducao.md](diretrizes-de-traducao.md) e [glossario-ptbr.md](glossario-ptbr.md) com decisões próprias, fontes e contexto. Ambos começam sem decisões aprovadas.
4. Executar `python translation-work/toolkit.py status` e `check`; ler o manifesto e o último diff de fontes.
5. Ler um batch JSONL, incluindo caminho, chave, contexto e história. Consultar entradas relacionadas e os verbetes da enciclopédia. Cada lote de 500 pode ser trabalhado em quantos grupos menores forem necessários.
6. Escrever os valores PTBR manualmente. Não substituir a tarefa por uma API, worker ou preenchimento automático. Inglês preservado intencionalmente precisa constar explicitamente no campo PTBR.
7. Aplicar um payload com `generation`, `expected_count` e entradas `{batch,id,source_sha256,PTBR}`. Os exemplos e as flags estão no guia técnico. Não alterar EN ou metadados originais.
8. Rever rejeições, corrigir somente as pendências, executar `check` e `checkpoint`. `resume` mostra o estado atual. Para trocar uma tradução já aceita, revisar e usar `--replace`.
9. Fazer commits de progresso quando autorizado. Eles devem conter o manifesto atualizado e os batches realmente alterados. Não gerar PTBR parcial para mostrar andamento.
10. Em atualização do jogo, preferir `update-sources` numa instalação original verificada; usar `--game-root` quando necessário. `sync` atende originais já copiados em EN. Conferir o diff por ID e aproveitar o histórico apenas como contexto de revisão.
11. Depois de concluídas e revisadas todas as traduções, incluindo a gramática, executar `check --complete` e `build` explicitamente. Conferir a saída e testar no jogo somente em ambiente autorizado.
12. Um build completo versionado e enviado à branch de publicação acionará o workflow. Não disparar manualmente uma Release sem instrução do responsável. Após a publicação real, atualizar o README público sem perder sua apresentação e registrar apenas compatibilidade comprovada.

Nenhum comando do toolkit autoriza modificar a instalação original. Nenhum glossário inicial foi aprovado pela desenvolvedora em nome da Ella.
