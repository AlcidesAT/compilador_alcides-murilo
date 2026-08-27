# compilador_alcides-murilo

Compilador didático desenvolvido para a disciplina de Compiladores.

**Aula 4 — Análise Léxica**: implementação de um analisador léxico (scanner)
completo, escrito em Python puro (só a biblioteca padrão), para uma
linguagem fictícia de tipagem estática com sintaxe no estilo C/Java.

O relatório com as decisões de projeto está em [`RELATORIO.md`](RELATORIO.md).

## Requisitos

- Python 3.8 ou superior (nenhuma dependência externa — só `re`, `sys` e
  `pathlib`, todas da biblioteca padrão).

## Uso

Sem argumento, roda o analisador sobre **todos** os programas de exemplo em
`examples/`, um atrás do outro — é a forma de demonstração/teste deste
projeto:

```bash
python analisador_lexico.py
```

Para analisar um arquivo específico:

```bash
python analisador_lexico.py examples/valido.mini
```

O programa encerra com código de saída `0` quando não há erro léxico em
nenhum arquivo analisado, e `1` quando há pelo menos um erro em algum deles
(a lista completa de erros é sempre impressa).

## Estrutura do projeto

```
analisador_lexico.py    dicionário `tokens`, função tokenize() e a CLI (main())
examples/
  valido.mini      programa completo sem erros (todos os recursos obrigatórios)
  variaveis.mini   declaração de variáveis de todos os tipos
  funcoes.mini     declaração de funções (com/sem retorno) e chamadas
  controle.mini    estruturas de controle (caso_isso / se_nao_isso / loop)
  com_erros.mini   programa com os três tipos de erro léxico propositais
```

## A linguagem

A linguagem usa um vocabulário próprio em português, em vez das palavras em
inglês sugeridas no enunciado (mesma quantidade e papel de cada categoria:
5 palavras-chave, 5 tipos incluindo `void`, 2 booleanos). A especificação
completa está no `RELATORIO.md`. Em resumo:

| Categoria           | Palavras da linguagem                          | Equivalente no enunciado |
|----------------------|-------------------------------------------------|----------------------------|
| Palavras-chave       | `caso_isso`, `se_nao_isso`, `loop`, `retorna`, `mostrar` | `if`, `else`, `while`, `return`, `print` |
| Tipos                | `num`, `decim`, `texto`, `bool`, `void`         | `int`, `float`, `string`, `bool`, `void` |
| Booleanos            | `sim`, `nao`                                     | `true`, `false`            |

- **Identificadores**: começam com letra ou `_`, seguidos de letras, dígitos ou `_`
- **Literais**: inteiros (`42`), ponto flutuante (`3.14`), strings (`"texto"`)
- **Operadores**: `+ - * / = == != < > <= >=`
- **Símbolos**: `; , ( ) { }`
- **Comentários**: de linha, iniciados por `//`
- **Blocos**: delimitados por `{` e `}` (não há indentação significativa)
