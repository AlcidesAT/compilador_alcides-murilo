# Relatório — Analisador Léxico

**Disciplina:** Compiladores — Aula 4: Análise Léxica
**Autor:** Alcides
**Repositório:** `compilador_alcides-murilo`

## 1. Objetivo

Implementar, em Python, um analisador léxico completo para uma linguagem
fictícia de tipagem estática e sintaxe no estilo C/Java, capaz de:

- reconhecer todos os tokens exigidos por meio de expressões regulares
  (obrigatório — nenhuma comparação direta de string é usada para
  classificar tokens);
- reportar erros léxicos com mensagens claras, sem interromper a análise;
- servir de primeira fase para as próximas etapas do compilador (análise
  sintática, semântica, geração de código).

## 2. Especificação da linguagem

**Escolha de projeto: vocabulário próprio em português.** O enunciado
sugere palavras em inglês (`if`, `while`, `return`, `print`, `int`,
`float`, `string`, `true`, `false`) como exemplo de tokens a reconhecer.
Optei por usar um vocabulário próprio no lugar dessas palavras específicas,
mantendo exatamente a mesma estrutura exigida — 5 palavras-chave de
controle, 5 tipos (incluindo `void` para função sem retorno), 2 literais
booleanos, os mesmos operadores, pontuação e regras de identificador. Ou
seja: a *forma* dos requisitos (quantidade e papel de cada categoria de
token) é seguida à risca; o *nome* de cada palavra reservada é uma escolha
de estilo.

| Categoria       | Palavras da linguagem                                          | Equivalente sugerido no enunciado |
|------------------|-------------------------------------------------------------------|--------------------------------------|
| Palavras-chave   | `caso_isso`, `se_nao_isso`, `loop`, `retorna`, `mostrar`/`fala`   | `if`, `else`, `while`, `return`, `print` |
| Tipos            | `num`, `decim`, `texto`, `bool`, `void`                           | `int`, `float`, `string`, `bool`, `void` |
| Booleanos        | `sim`, `nao`                                                       | `true`, `false`                      |
| Identificadores  | `x`, `contador1`, `soma`                                          | (igual)                              |
| Literal inteiro  | `42`, `0`, `1000`                                                  | (igual)                              |
| Literal float    | `3.14`, `9.99`                                                     | (igual)                              |
| Literal string   | `"Ana"`, `"Ola, mundo"`                                            | (igual)                              |
| Operadores       | `+ - * / = == != < > <= >=`                                        | (igual)                              |
| Pontuação        | `; , ( ) { }`                                                      | (igual)                              |
| Comentários      | `// até o fim da linha`                                            | (igual)                              |

Blocos são delimitados por chaves (`{ }`), variáveis são declaradas com tipo
explícito (`num x = 10;`), funções têm tipo de retorno, nome e parâmetros
tipados (`num soma(num a, num b) { retorna a + b; }`), e instruções terminam
com `;`. Ver `examples/valido.mini` para um programa completo que exercita
todos esses recursos.

**Extra informal.** Por cima de tudo isso, a linguagem também aceita `~>`
como forma descontraída de comentário, além do `//` formal — pura
decoração, não substitui nada. Ver `examples/informal.mini`.

## 3. Arquitetura

```
analisador_lexico.py    dicionário `tokens`, função tokenize() e a CLI (main())
examples/                seis programas de exemplo (ver secao 6)
```

Toda a implementação cabe em um único script, seguindo de perto a estrutura
do gabarito distribuído em aula (`tokens = {...}` + uma função `tokenize`),
em vez de dividida em módulos/classes separados para cada conceito. Não há
nenhuma dependência externa — só `re`, `sys` e `pathlib` da biblioteca
padrão do Python — então rodar o projeto é só `python analisador_lexico.py`,
sem instalar nada.

## 4. Escolhas de implementação

### 4.1. Um dicionário de padrões, casados por posição (não por `split()`)

O ponto de partida foi o gabarito da aula: um dicionário `tokens` mapeia
cada categoria léxica à sua expressão regular, e a regra enunciada no
próprio comentário do gabarito — "a ordem importa: o primeiro tipo que
casar é o escolhido" — foi mantida à risca (inclusive o nome da variável).
A diferença central está em como o código é percorrido.

O gabarito usa `codigo.split()` e testa cada *palavra* (separada por
espaço) contra os padrões com `re.fullmatch`. Isso quebra para qualquer
símbolo colado a um identificador — `x==10` chega como uma palavra só,
`soma(a,b);` também — porque não há espaço nenhum entre eles. Como o
próprio slide de "Saída Esperada do Tokenizador" reconhece, esse é
exatamente o motivo de `==` sair como `UNKNOWN` no exemplo do professor.

A correção foi trocar `split()` + `fullmatch` por varredura posicional:
todas as expressões do dicionário são combinadas em um único padrão via
alternância nomeada (`|`), e a cada passo casa-se a partir da posição atual
do texto com `re.match(codigo, pos)`, avançando `pos` para o fim do lexema
reconhecido:

```python
tokens = {
    "COMENTARIO": r"//[^\n]*|~>[^\n]*",
    "QUEBRA_DE_LINHA": r"\n",
    "ESPACO": r"[ \t\r]+",
    "IDENTIFICADOR_INVALIDO": r"\d+[A-Za-z_]\w*",
    "STRING": r'"[^"\n]*"',
    "STRING_INVALIDA": r'"[^"\n]*',
    "NUMERO_INVALIDO": r"\d+\.(?!\d)|\.\d+",
    "FLOAT": r"\d+\.\d+",
    "NUMERO": r"\d+",
    "IDENTIFICADOR": r"[a-zA-Z_][a-zA-Z0-9_]*",
    "OPERADOR": r"==|!=|<=|>=|=|<|>|\+|-|\*|/",
    "SIMBOLO": r"[(){};,]",
}
_PADRAO = re.compile(
    "|".join(f"(?P<{tipo}>{regex})" for tipo, regex in tokens.items())
)
```

Isso resolve o problema do `==` colado sem abandonar a estrutura do
gabarito: continua sendo "um dicionário de expressões regulares, a ordem
decide o vencedor" — só que aplicado caractere a caractere, como o slide
"Passos da Análise Léxica" descreve (leitura do código-fonte, identificação
de padrões via AFD, reconhecimento de tokens), em vez de palavra a palavra.

O motor de expressões regulares do Python, ao compilar essa alternância,
constrói internamente uma máquina equivalente a um autômato finito que tenta
casar cada alternativa na posição atual do buffer — exatamente o papel que,
em um compilador construído "na mão", seria feito por um AFD combinado (a
união dos AFDs de cada categoria de token, obtida via construção de
subconjuntos a partir dos NFAs de Thompson). Usar `re` aqui não é atalho: é
a mesma técnica usada por geradores de analisador léxico como o `lex`/`flex`,
apenas com o autômato construído em tempo de importação do módulo pelo
próprio interpretador Python.

A cada iteração do laço principal, `_PADRAO.match(codigo, pos)` é chamado a
partir da posição atual; o grupo nomeado que casou (`casamento.lastgroup`)
determina o tratamento do lexema, e `pos` avança para `casamento.end()`.

### 4.2. Ordem dos padrões é significativa

A alternância do `re` escolhe a **primeira** alternativa que casa na posição
atual — não a mais longa (diferente da convenção *leftmost-longest* usada
por `lex`). Isso teve consequências diretas de projeto, todas visíveis na
ordem do dicionário `tokens`:

- `IDENTIFICADOR_INVALIDO` (`\d+[A-Za-z_]\w*`) precisa vir **antes** de
  `FLOAT`/`NUMERO`. Sem isso, a entrada `1abc` seria fatiada em dois tokens
  válidos (`NUMERO("1")` + `IDENTIFICADOR("abc")`) em vez de ser reportada
  como um único erro léxico — que é justamente o comportamento exigido pelo
  slide "Tratamento de Erros Léxicos" ("Identificadores Malformados").
- `STRING` (fechada) precisa vir **antes** de `STRING_INVALIDA`. Caso
  contrário, mesmo uma string bem formada como `"ok"` seria capturada pelo
  padrão mais permissivo (que não exige aspas de fechamento), gerando um
  falso erro.
- `NUMERO_INVALIDO` (`\d+\.(?!\d)|\.\d+`) precisa vir **antes** de `FLOAT`.
  Pega `3.` (ponto sem dígito depois) e `.5` (ponto sem dígito antes) como
  um único erro léxico. Como esse padrão só casa quando falta dígito de um
  dos lados do ponto, ele nunca compete com `FLOAT` por um número
  realmente válido como `3.14`.
- Operadores de dois caracteres (`==`, `!=`, `<=`, `>=`) precisam vir antes
  dos de um caractere (`=`, `<`, `>`), senão `==` seria reconhecido como dois
  tokens `=` `=` em vez de um único `OPERADOR("==")` — o mesmo problema que
  o gabarito original tem, só que por um motivo diferente (lá é o
  `code.split()` que nunca separa `==` do resto).

### 4.3. Palavras-chave por reclassificação, não por regex própria

Palavras-chave, tipos e booleanos **não** têm um padrão regex dedicado no
dicionário `tokens`. Todos casam primeiro com `IDENTIFICADOR`
(`[A-Za-z_][A-Za-z0-9_]*`) e só depois são reclassificados pela função
`classificar_identificador`, que consulta os conjuntos `PALAVRAS_CHAVE`, `TIPOS` e
`BOOLEANOS`. Essa é a mesma orientação do slide "Pseudocódigo: Identificação
de Tokens" ("a distinção é feita consultando a tabela de palavras reservadas
após o reconhecimento inicial") e evita um problema sutil: se `loop` fosse
casado por um padrão regex próprio colocado antes de `IDENTIFICADOR`, a
entrada `loopado` poderia ser incorretamente fatiada em `loop` + `ado`.
Como o reconhecimento de identificador é sempre "guloso" e ocorre antes da
checagem de palavra-chave, `loopado` é corretamente reconhecido como um
único `IDENTIFICADOR("loopado")`, e não como o token `loop` seguido de
`ado`.

### 4.4. Rastreamento de linha

A cada token `QUEBRA_DE_LINHA` (`\n`), o contador `linha` é incrementado. Cada
token e cada mensagem de erro carregam esse número, o suficiente para
localizar o problema no arquivo-fonte sem precisar também rastrear a coluna
(que aumentaria a complexidade do laço principal sem exigência explícita no
enunciado).

### 4.5. Erros não interrompem a análise

`erros` é uma lista acumulada ao longo do laço, não uma exceção lançada no
primeiro problema encontrado. Após registrar um erro (caractere inválido,
string não terminada, identificador malformado), o scanner sempre continua
a partir do próximo caractere — assim como um compilador real deve reportar
*todos* os erros léxicos de um arquivo em uma única execução, e não parar
no primeiro. Isso é visível em `examples/com_erros.mini`, que contém quatro
erros distintos, todos reportados na mesma execução — nenhum deles faz o
programa abortar antes de terminar de ler o arquivo.

## 5. Tratamento de erros léxicos implementado

| Situação                                 | Exemplo                     | Tratamento                                             |
|-------------------------------------------|------------------------------|----------------------------------------------------------|
| Caractere fora do alfabeto da linguagem    | `@`, `#`, `$`                | Um erro por caractere; análise continua no próximo caractere |
| String literal não fechada                 | `"texto sem fechar`          | Erro reportado; o restante da linha é descartado como parte do lexema inválido |
| Identificador malformado (começa com dígito) | `1abc`                     | Toda a sequência é consumida em um único erro (evita reportar `1` e `abc` como tokens válidos) |
| Número mal formatado (ponto sem dígito de um dos lados) | `3.`, `.5`, `3.14.5` | Todo o trecho inválido é consumido em um único erro; se houver um número válido antes (como o `3.14` em `3.14.5`), ele é reconhecido normalmente e só a sobra (`.5`) vira erro |

Cada relatório de análise (`imprimir_relatorio`) mostra uma tabela alinhada
de tokens, a lista de erros (se houver) e um resumo com a contagem final —
ver `examples/com_erros.mini` ou rodar `python analisador_lexico.py` para
um exemplo da saída formatada.

## 6. Verificação por exemplos

Em vez de uma suíte de testes com asserts formais, a verificação deste
projeto é feita rodando o analisador sobre seis programas de exemplo em
`examples/` — o que `python analisador_lexico.py` (sem argumento) faz
automaticamente, um atrás do outro, via `rodar_exemplos()`:

| Arquivo             | O que verifica                                                      |
|----------------------|-----------------------------------------------------------------------|
| `variaveis.mini`    | declaração de variáveis de todos os tipos exigidos                   |
| `funcoes.mini`      | declaração de função (com e sem retorno) e chamada de função         |
| `controle.mini`     | `caso_isso` / `se_nao_isso` / `loop` com condição entre parênteses e bloco `{ }` |
| `informal.mini`     | o comentário informal `~>` e os dois nomes de `print` (`mostrar`/`fala`) |
| `valido.mini`       | programa completo, exercitando tudo de uma vez                      |
| `com_erros.mini`    | os quatro tipos de erro léxico exigidos, todos na mesma execução      |

Cada um imprime a tabela de tokens reconhecidos e a contagem de erros — o
esperado é `0` erros em todos, exceto `com_erros.mini` (que deve mostrar
exatamente os quatro erros propositais). É uma verificação visual, mais
fácil de conferir a olho e de estender (basta adicionar outro arquivo
`.mini` em `examples/`) do que uma lista grande de `assert`.

## 7. Dificuldades encontradas

- **`code.split()` não separa símbolos colados a identificadores**: essa
  era a abordagem do gabarito da aula, e o próprio slide "Saída Esperada do
  Tokenizador" reconhece a limitação (`==` sai como `UNKNOWN`). A correção
  foi trocar a varredura por palavra (`split()` + `re.fullmatch`) por
  varredura posicional (`re.match(codigo, pos)`, avançando `pos` a cada
  token reconhecido), preservando a mesma estrutura de dicionário de
  padrões.
- **Ordem de alternância vs. maior casamento**: o comportamento "primeira
  alternativa que casa" do `re` (em vez de "casamento mais longo") não é
  imediatamente óbvio, e a princípio o identificador malformado (`1abc`)
  era fatiado incorretamente em dois tokens válidos. A solução foi
  posicionar o padrão mais específico (`IDENTIFICADOR_INVALIDO`) antes dos
  padrões numéricos genéricos no dicionário `tokens`.
- **String não terminada sem "vazar" para a linha seguinte**: o padrão
  ingênuo para string não fechada (`"[^"]*`, sem excluir `\n`) consumiria
  todo o restante do arquivo em busca de uma aspa de fechamento, incluindo
  quebras de linha e código válido posterior. A correção foi excluir `\n`
  da classe de caracteres (`"[^"\n]*`), limitando o erro à linha onde a
  string começou.

## 8. Como executar

```bash
python analisador_lexico.py                     # roda todos os exemplos em examples/
python analisador_lexico.py examples/valido.mini # analisa so um arquivo especifico
```
