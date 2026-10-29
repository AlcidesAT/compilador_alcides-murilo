Claro. Vou deixar mais simples, direto e com uma linguagem mais natural, mas mantendo as informações importantes do relatório. 

## 1. Objetivo

O objetivo do projeto é criar, em Python, um analisador léxico para uma linguagem fictícia parecida com C/Java.

Ele deve:

* reconhecer os tokens usando expressões regulares;
* identificar e informar erros léxicos sem parar o programa;
* servir como primeira etapa do compilador, antes da análise sintática e semântica.

## 2. Linguagem utilizada

Foi escolhida uma linguagem própria em português. Ela mantém a mesma quantidade e função dos tokens pedidos no trabalho, mas usa palavras diferentes.

| Categoria        | Palavras                                                 |
| ---------------- | -------------------------------------------------------- |
| Palavras-chave   | `caso_isso`, `se_nao_isso`, `loop`, `retorna`, `mostrar` |
| Tipos            | `int`, `decim`, `texto`, `bool`, `void`                  |
| Booleanos        | `sim`, `nao`                                             |
| Identificadores  | `x`, `contador1`, `soma`                                 |
| Números inteiros | `42`, `0`, `1000`                                        |
| Números decimais | `3.14`, `9.99`                                           |
| Strings          | `"Ana"`, `"Ola, mundo"`                                  |
| Operadores       | `+ - * / ^ = == != < > <= >=`                            |
| Símbolos         | `; , ( ) { }`                                            |
| Comentários      | `// comentário`                                          |

As variáveis possuem um tipo definido, como `int x = 10;`, e as funções também possuem tipo de retorno e parâmetros.

## 3. Estrutura do projeto

O projeto é simples e possui principalmente:

* `analisador_lexico.py` — código principal do analisador;
* `examples/` — arquivos usados para testar o programa.

Foi usado apenas o Python e bibliotecas que já vêm com ele, como `re`, `sys` e `pathlib`. 

## 4. Como o analisador funciona

O analisador utiliza um dicionário com expressões regulares para reconhecer cada tipo de token.

Em vez de separar o código apenas pelos espaços, ele percorre o texto posição por posição. Isso é importante porque símbolos podem estar juntos, como em:

`x==10`

ou:

`soma(a,b);`

Dessa forma, o programa consegue reconhecer corretamente os operadores e símbolos mesmo quando não existe espaço entre eles. 

### Ordem dos padrões

A ordem das expressões regulares é importante. Por exemplo:

* `1abc` precisa ser identificado como um identificador inválido;
* uma string fechada deve ser reconhecida antes de uma string inválida;
* `==` precisa ser reconhecido antes de `=`, para não virar dois tokens separados.

### Palavras reservadas

Palavras como `loop`, `retorna` e `mostrar` primeiro são reconhecidas como identificadores. Depois, o programa verifica se elas pertencem à lista de palavras reservadas.

Isso evita problemas como reconhecer `loopado` como `loop` + `ado`. 

### Número da linha

O programa conta as quebras de linha. Assim, quando encontra um erro, consegue informar em qual linha ele aconteceu. 

### Erros

Os erros são armazenados em uma lista e a análise continua normalmente. Assim, o programa consegue mostrar vários erros de uma vez, em vez de parar no primeiro. 

## 5. Erros tratados

O analisador identifica três principais tipos de erros:

* **Caractere inválido:** como `@`, `#` ou um `.` sozinho.
* **String não terminada:** quando falta a segunda aspas.
* **Identificador inválido:** como `1abc`, que começa com número.

Depois de encontrar um erro, o programa continua analisando o restante do código. 

## 6. Testes

Foram criados cinco arquivos para testar o analisador:

* `variaveis.mini` — testa declaração de variáveis;
* `funcoes.mini` — testa funções;
* `controle.mini` — testa estruturas de controle;
* `valido.mini` — testa um programa completo;
* `com_erros.mini` — testa os três tipos de erros.

O esperado é que os quatro primeiros não apresentem erros e que `com_erros.mini` mostre os erros de propósito. 

## 7. Principais dificuldades

As principais dificuldades foram:

* o `split()` não conseguia separar símbolos que estavam juntos ao código;
* a ordem das expressões regulares podia fazer um token ser reconhecido de forma errada;
* strings sem fechamento podiam acabar consumindo linhas seguintes.

Esses problemas foram resolvidos usando uma leitura posição por posição, ajustando a ordem dos padrões e fazendo a string inválida parar na quebra de linha. 

## 8. Como executar

O projeto usa o `uv`, e cada etapa do compilador virou um comando
(definido em `pyproject.toml`). Para executar todos os exemplos:

```bash
uv run lexico
uv run sintatico
uv run semantico
```

Para analisar apenas um arquivo:

```bash
uv run lexico examples/valido.mini
```

## 9. Aula 5 — Análise sintática

Depois do léxico, o passo seguinte do compilador é o analisador sintático
(`analisador_sintatico.py`), que verifica se a sequência de tokens forma um
programa válido segundo a gramática da linguagem, e monta a árvore
sintática correspondente. Ele foi feito propositalmente simples: o mínimo
necessário para reconhecer a gramática da linguagem do projeto.

### Técnica usada

Foi usada descida recursiva (recursive descent): cada regra da gramática
vira uma função Python, e uma função chama a outra na mesma ordem em que
uma regra aparece dentro da outra (`programa()` chama `declaracao()`, que
chama `bloco()`/`comando()`, que chama `expressao()`, etc). É a forma mais
direta de escrever um parser à mão, e a gramática completa (em BNF) está
comentada no topo do arquivo.

O código não usa classes, só funções. Duas variáveis no topo do arquivo
guardam onde o parser está: `lista_tokens` (os tokens vindos do léxico) e
`posicao` (o índice do token que está sendo lido). Funções pequenas leem o
token atual (`tipo_atual()`, `valor_atual()`, `linha_atual()`), passam para
o próximo (`avancar()`) ou exigem um token específico (`esperar_valor(";")`,
`esperar_tipo("IDENTIFICADOR")`).

### Precedência de operadores

As expressões respeitam a prioridade das operações da matemática. Para
isso, cada nível de prioridade virou uma função, e cada uma chama a do
nível mais forte para ler os lados da conta:

| Função        | Operadores              | Associatividade |
| ------------- | ----------------------- | --------------- |
| `expressao()` | `== != < > <= >=` (mais fraca) | esquerda |
| `soma()`      | `+` `-`                 | esquerda        |
| `produto()`   | `*` `/`                 | esquerda        |
| `unario()`    | `-` unário (ex.: `-x`)  | direita         |
| `potencia()`  | `^` (potenciação)       | direita         |
| `termo()`     | número, nome, `( )` (mais forte) | —      |

Como `soma()` chama `produto()` para ler cada lado, a multiplicação entra
inteira dentro da soma: `2 + 3 * 4` vira `2 + (3 * 4)`. Ou seja, o operador
de maior prioridade fica mais fundo na árvore e é calculado primeiro.

O `while` dentro de `expressao()`, `soma()` e `produto()` junta várias contas
do mesmo nível da esquerda para a direita (`10 - 4 - 3` = `(10 - 4) - 3`).
A potenciação é associativa à direita, como na matemática
(`2 ^ 3 ^ 2` = `2 ^ (3 ^ 2)`): em `potencia()` o lado direito chama
`unario()` de novo, e é lá que entra a próxima potência. Ela também tem
prioridade sobre o menos unário (`-2 ^ 2` = `-(2 ^ 2)`).

### Árvore sintática

Cada função devolve um nó: um dicionário com `tipo`, `valor`, `filhos` e
`linha`, criado pela função `novo_no()`.
Ao final, a árvore inteira é impressa de forma indentada — é a mesma ideia
das árvores de expressão/comando mostradas nos slides da Aula 5 (operador
como nó, operandos como filhos), só que aplicada à gramática real da
linguagem do projeto, e não a um exemplo abstrato.

### Tratamento de erros

Diferente do léxico, o parser para na primeira regra que não reconhecer:
assim que um token não bate com o esperado, `erro_sintatico()` faz um
`raise SyntaxError(...)` com a linha, e a análise é interrompida e volta
direto para o `except` da função `analisar()`. Essa é a parte mais simples de
implementar (não precisa de lógica de recuperação/sincronização) e é
suficiente para o nível deste exercício.

### Testes

Foi criado mais um arquivo de exemplo, `erros_sintaticos.mini`: um programa
lexicamente válido, mas com um erro de sintaxe proposital (`decim total =
;`, faltando o valor depois do `=`). Os outros quatro exemplos da Aula 4
continuam sendo usados como teste de regressão: devem gerar árvore
sintática completa e nenhum erro.

Também foi criado `precedencia.mini`, com expressões que misturam
operadores de prioridades diferentes; a árvore impressa mostra a ordem em
que cada operação seria calculada.

## 10. Aula 9 — Análise semântica

A terceira etapa (`analisador_semantico.py`) recebe a árvore sintática e
verifica se o programa faz sentido. Exemplo: `int x = sim;` está certo na
gramática, mas guardar um `bool` numa variável `int` não faz sentido.

A análise semântica só roda quando o arquivo não tem erro léxico nem
sintático: com a árvore pela metade, apareceriam erros falsos.

### Percurso da árvore

O código também não usa classes, só funções. A função principal,
`analisar_semantica()`, percorre os comandos do programa de cima para
baixo, uma vez só. Para cada comando, `analisar_comando()` olha o tipo do nó
(`DECL_VAR`, `SE`, `LOOP`...) e chama a função certa — é a ideia do
*Visitor* dos slides, feita com um `if/elif`.

O tipo das expressões é descoberto de baixo para cima (pós-ordem): primeiro
o tipo dos filhos, depois o do operador. Ex.: em `x + 2.0`, `x` é `int` e
`2.0` é `decim`, então a soma é `decim`.

Como a árvore é lida uma vez só, de cima para baixo, uma variável ou função
tem que ser declarada antes de ser usada (igual ao C). A recursão funciona
porque a função entra na tabela antes de o corpo dela ser analisado.

O andamento da análise fica em quatro variáveis no topo do arquivo
(`escopos`, `tabela`, `erros`, `funcao_atual`), que são zeradas no começo
de `analisar_semantica()` para cada arquivo analisado.

### Tabela de símbolos

É uma pilha de escopos: uma lista de dicionários `{nome: símbolo}`. Ao
entrar num bloco `{ }`, empilha um dicionário novo; ao sair, desempilha.
A busca vai do topo (escopo mais de dentro) até a base (global), por isso
uma variável de dentro pode ter o mesmo nome de uma de fora (sombreamento).
Cada símbolo guarda nome, categoria (variável, parâmetro ou função), tipo,
escopo (global, local ou aninhado), linha e, nas funções, o tipo de cada
parâmetro.

Parâmetros e corpo da função ficam no mesmo escopo, então
`int f(int a) { int a = 1; }` dá erro de nome repetido.

### Regras de tipo

| Operação              | Tipos aceitos                    | Resultado                    |
| --------------------- | -------------------------------- | ---------------------------- |
| `+ - * / ^`           | `int`/`decim`                    | `decim` se algum for `decim`, senão `int` |
| `+`                   | `texto` + `texto`                | `texto`                      |
| `< > <= >=`           | `int`/`decim`                    | `bool`                       |
| `== !=`               | dois números ou dois do mesmo tipo | `bool`                     |
| `-` unário            | `int`/`decim`                    | o mesmo tipo                 |

Ao guardar um valor (declaração, atribuição, argumento ou `retorna`), o
tipo tem que ser igual. A única conversão automática é `int` → `decim`,
que não perde nada; `decim` → `int` dá erro, porque perderia a parte
decimal.

### Erros detectados

* variável ou função não declarada;
* nome repetido no mesmo escopo (variável, parâmetro ou função);
* tipos incompatíveis em contas, comparações, declarações e atribuições;
* variável ou parâmetro do tipo `void`;
* chamada com quantidade ou tipo de argumento errado;
* chamar uma variável como função, ou usar uma função sem `( )`;
* `retorna` com tipo errado, com valor numa função `void`, sem valor numa
  função que não é `void`, ou fora de função;
* função que não é `void` sem nenhum `retorna`;
* condição de `caso_isso`/`loop` que não é `bool`;
* `mostrar` de uma função `void`;
* função declarada dentro de um bloco.

Como no léxico, o analisador anota o erro e continua. Uma expressão com
erro recebe o tipo `erro`, que é aceito em qualquer lugar: assim um único
erro não gera uma cascata de erros falsos. Os erros saem ordenados pela
linha, no formato `linha 16: variavel 'z' nao declarada`.

Para ter a linha nas mensagens, o analisador sintático guarda a linha em
cada nó da árvore (`no["linha"]`).

### Testes

* `semantica.mini` — programa válido, baseado na simulação da aula
  (escopos global, local e aninhado), com sombreamento, recursão, função
  chamando outra função e conversão `int` → `decim`;
* `erros_semanticos.mini` — um erro de cada tipo, com um comentário em
  cada linha dizendo qual é o erro esperado.

Os exemplos das aulas anteriores continuam passando sem erro.

Para executar:

```bash
uv run semantico
uv run semantico examples/semantica.mini
```
