# compilador_alcides-murilo

Compilador didático desenvolvido para a disciplina de Compiladores.

**Aula 4 — Análise Léxica**: implementação de um analisador léxico (scanner)
completo, escrito em Python puro (só a biblioteca padrão), para uma
linguagem fictícia de tipagem estática com sintaxe no estilo C/Java.

**Aula 5 — Análise Sintática**: implementação de um analisador sintático
(parser) simples, de descida recursiva, que consome os tokens produzidos
pelo analisador léxico e monta a árvore sintática do programa, parando no
primeiro erro de sintaxe encontrado.

**Aula 9 — Análise Semântica**: implementação de um analisador semântico
que percorre a árvore sintática, monta a tabela de símbolos (pilha de
escopos) e verifica declarações, escopos e tipos.

O relatório com as decisões de projeto está em [`RELATORIO.md`](RELATORIO.md).

## Requisitos

- [uv](https://docs.astral.sh/uv/). Ele baixa sozinho o Python certo (versão
  em `.python-version`) e prepara o ambiente na primeira execução — não
  precisa instalar mais nada.
- Nenhuma dependência externa — só `re`, `sys` e `pathlib`, todas da
  biblioteca padrão.

## Uso

Cada etapa do compilador é um comando do uv. Sem argumento, ele roda sobre
**todos** os programas de exemplo em `examples/`, um atrás do outro — é a
forma de demonstração/teste deste projeto:

```bash
uv run lexico
uv run sintatico
uv run semantico
```

Para analisar um arquivo específico:

```bash
uv run semantico examples/semantica.mini
```

Cada etapa roda as anteriores internamente: o sintático roda o léxico, e o
semântico roda o léxico + sintático. A análise semântica só acontece se o
arquivo não tiver erro léxico nem sintático.

Os programas encerram com código de saída `0` quando não há erro em
nenhum arquivo analisado, e `1` quando há pelo menos um erro em algum deles
(a lista completa de erros é sempre impressa).

## Estrutura do projeto

```
analisador_lexico.py     dicionário `tokens`, função tokenize() e a CLI (main())
analisador_sintatico.py  gramática (BNF em comentário), uma função por regra
                          (descida recursiva), nós da árvore como dicionários
                          e a CLI (main())
analisador_semantico.py  tabela de símbolos (pilha de escopos), verificação
                          de tipos e a CLI (main())
pyproject.toml           projeto do uv: define os comandos lexico, sintatico e semantico
.python-version          versão do Python que o uv usa
uv.lock                  arquivo gerado pelo uv (não editar à mão)
examples/
  valido.mini           programa completo sem erros (todos os recursos obrigatórios)
  variaveis.mini        declaração de variáveis de todos os tipos
  funcoes.mini          declaração de funções (com/sem retorno) e chamadas
  controle.mini         estruturas de controle (caso_isso / se_nao_isso / loop)
  com_erros.mini        programa com os três tipos de erro léxico propositais
  erros_sintaticos.mini programa lexicamente válido, mas com um erro de sintaxe proposital
  precedencia.mini      expressões que mostram a precedência/associatividade dos operadores
  semantica.mini        programa válido: escopos, sombreamento, recursão, conversão int -> decim
  erros_semanticos.mini programa correto na sintaxe, mas com erros semânticos propositais
```

## A linguagem

A linguagem usa um vocabulário próprio em português, em vez das palavras em
inglês sugeridas no enunciado (mesma quantidade e papel de cada categoria:
5 palavras-chave, 5 tipos incluindo `void`, 2 booleanos). A especificação
completa está no `RELATORIO.md`. Em resumo:

| Categoria           | Palavras da linguagem                          | Equivalente no enunciado |
|----------------------|-------------------------------------------------|----------------------------|
| Palavras-chave       | `caso_isso`, `se_nao_isso`, `loop`, `retorna`, `mostrar` | `if`, `else`, `while`, `return`, `print` |
| Tipos                | `int`, `decim`, `texto`, `bool`, `void`         | `int`, `float`, `string`, `bool`, `void` |
| Booleanos            | `sim`, `nao`                                     | `true`, `false`            |

- **Identificadores**: começam com letra ou `_`, seguidos de letras, dígitos ou `_`
- **Literais**: inteiros (`42`), ponto flutuante (`3.14`), strings (`"texto"`)
- **Operadores**: `+ - * / ^ = == != < > <= >=` (`^` é potenciação)
- **Precedência** (maior → menor): `( )`, `^` (assoc. à direita), `-` unário,
  `* /`, `+ -`, comparações (`== != < > <= >=`)
- **Símbolos**: `; , ( ) { }`
- **Comentários**: de linha, iniciados por `//`
- **Blocos**: delimitados por `{` e `}` (não há indentação significativa)
