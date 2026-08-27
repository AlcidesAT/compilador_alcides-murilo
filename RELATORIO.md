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
| Tipos            | `num`, `decim`, `texto`, `bool`, `void`                  |
| Booleanos        | `sim`, `nao`                                             |
| Identificadores  | `x`, `contador1`, `soma`                                 |
| Números inteiros | `42`, `0`, `1000`                                        |
| Números decimais | `3.14`, `9.99`                                           |
| Strings          | `"Ana"`, `"Ola, mundo"`                                  |
| Operadores       | `+ - * / = == != < > <= >=`                              |
| Símbolos         | `; , ( ) { }`                                            |
| Comentários      | `// comentário`                                          |

As variáveis possuem um tipo definido, como `num x = 10;`, e as funções também possuem tipo de retorno e parâmetros.

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

Para executar todos os exemplos:

```bash
python analisador_lexico.py
```

Para analisar apenas um arquivo:

```bash
python analisador_lexico.py examples/valido.mini
```

