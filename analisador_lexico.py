"""
Analisador Lexico - Trabalho Pratico (Aula 4: Analise Lexica)

Baseado no gabarito da aula, mas varrendo o codigo caractere a caractere
(re.match a partir de uma posicao) em vez de codigo.split() + fullmatch -
o gabarito original nao separa simbolos colados a identificadores (ex:
"x==10" vira uma unica "palavra" e "==" sai como UNKNOWN, como o proprio
slide "Saida Esperada do Tokenizador" mostra). A ideia central - "um
dicionario de regex em que a ordem decide o vencedor" - continua igual.

Trata os 4 erros lexicos exigidos: caractere invalido, string nao
terminada, identificador malformado e numero mal formatado.

A linguagem usa vocabulario proprio em portugues (caso_isso, loop,
retorna, num, decim, texto, sim, nao...) no lugar das palavras em ingles
do enunciado - ver PALAVRAS_CHAVE/TIPOS/BOOLEANOS abaixo. "~>" e uma
forma informal extra de comentario, alem do "//" formal (examples/informal.mini).

Sem argumento, roda o analisador sobre todos os exemplos de examples/
(rodar_exemplos()) - a forma de "teste" deste projeto: cada exemplo
mostra visualmente se o resultado bate com o esperado.
"""

import re
import sys
from pathlib import Path

# A ordem importa: o modulo re escolhe a primeira alternativa que casa,
# nao a mais longa. Por isso os padroes mais especificos vem antes dos
# genericos:
#   - IDENTIFICADOR_INVALIDO antes de FLOAT/NUMERO -> "1abc" vira um
#     unico erro, em vez de NUMERO("1") + IDENTIFICADOR("abc").
#   - STRING (fechada) antes de STRING_INVALIDA -> prefere o caso valido.
#   - NUMERO_INVALIDO antes de FLOAT/NUMERO -> "3." e ".5" viram um
#     unico erro, em vez de numero incompleto + caractere solto.
#   - Operadores de 2 caracteres (==, !=, <=, >=) antes dos de 1
#     caractere, senao "==" viraria dois tokens "=" separados.
tokens = {
    # "//" e a forma formal de comentario (exigida no enunciado); "~>" e
    # uma forma informal a mais, tipo um bilhetinho no meio do codigo.
    "COMENTARIO":              r"//[^\n]*|~>[^\n]*",
    "QUEBRA_DE_LINHA":         r"\n",
    "ESPACO":                  r"[ \t\r]+",
    "IDENTIFICADOR_INVALIDO":  r"\d+[A-Za-z_]\w*",      # 1abc  2x  (comeca com digito)
    "STRING":                  r'"[^"\n]*"',            # "Ana"   "Ola, mundo"
    "STRING_INVALIDA":         r'"[^"\n]*',             # "texto sem fechar
    "NUMERO_INVALIDO":         r"\d+\.(?!\d)|\.\d+",    # 3.   .5  (ponto sem digito de um dos lados)
    "FLOAT":                   r"\d+\.\d+",             # 3.14   9.99
    "NUMERO":                  r"\d+",                  # 0   42   1000
    "IDENTIFICADOR":           r"[a-zA-Z_][a-zA-Z0-9_]*",  # x   soma   valor1
    "OPERADOR":                r"==|!=|<=|>=|=|<|>|\+|-|\*|/",
    "SIMBOLO":                 r"[(){};,]",             # bloco { } e chamada de funcao ( , )
}

# Palavras reservadas: nao podem virar nome de variavel/funcao. So sao
# reconhecidas DEPOIS do lexema casar como IDENTIFICADOR (nunca com
# regex propria), senao "loopado" seria fatiado em "loop" + "ado".
#
# Vocabulario proprio em portugues, no lugar do sugerido no enunciado
# (mesma estrutura: 5 palavras-chave, 5 tipos com void, 2 booleanos):
#   if/else/while/return  -> caso_isso/se_nao_isso/loop/retorna
#   print                 -> mostrar / fala
#   int/float/string/bool -> num/decim/texto/bool  (void continua void)
#   true/false            -> sim/nao
PALAVRAS_CHAVE = {"caso_isso", "se_nao_isso", "loop", "retorna", "mostrar", "fala"}
TIPOS = {"num", "decim", "texto", "bool", "void"}
BOOLEANOS = {"sim", "nao"}

_IGNORADOS = {"ESPACO", "COMENTARIO"}
_PADRAO = re.compile("|".join(f"(?P<{tipo}>{regex})" for tipo, regex in tokens.items()))


def classificar_identificador(lexema):
    """Reclassifica um IDENTIFICADOR em palavra-chave/tipo/booleano, se for o caso."""
    if lexema in PALAVRAS_CHAVE:
        return "PALAVRA_CHAVE"
    if lexema in TIPOS:
        return "TIPO"
    if lexema in BOOLEANOS:
        return "BOOLEANO"
    return "IDENTIFICADOR"


def tokenize(codigo):
    """Transforma o codigo-fonte em uma lista de tokens (tipo, lexema, linha).

    Erros lexicos sao contados e reportados, mas NAO interrompem a
    analise: o scanner descarta o trecho invalido e continua a partir
    do proximo caractere, assim como um compilador real reporta todos
    os erros de uma vez em vez de parar no primeiro problema.
    """
    resultado = []   # lista de tokens reconhecidos: (tipo, lexema, linha)
    erros = []        # lista de mensagens de erro
    linha = 1
    pos = 0

    while pos < len(codigo):
        casamento = _PADRAO.match(codigo, pos)

        if casamento is None:
            # nenhum padrao casou: caractere fora do alfabeto da linguagem
            erros.append(f"linha {linha}: caractere invalido {codigo[pos]!r}")
            pos += 1
            continue

        tipo = casamento.lastgroup
        lexema = casamento.group()
        pos = casamento.end()

        if tipo == "QUEBRA_DE_LINHA":
            linha += 1
        elif tipo in _IGNORADOS:
            pass
        elif tipo == "IDENTIFICADOR_INVALIDO":
            erros.append(
                f"linha {linha}: identificador malformado {lexema!r} "
                "(nao pode comecar com digito)"
            )
        elif tipo == "STRING_INVALIDA":
            erros.append(f"linha {linha}: cadeia de caracteres nao terminada {lexema!r}")
        elif tipo == "NUMERO_INVALIDO":
            erros.append(
                f"linha {linha}: numero mal formatado {lexema!r} "
                "(ponto decimal precisa de digitos dos dois lados)"
            )
        else:
            if tipo == "IDENTIFICADOR":
                tipo = classificar_identificador(lexema)
            resultado.append((tipo, lexema, linha))

    return resultado, erros


def imprimir_relatorio(nome, tokens_encontrados, erros):
    """Imprime, de forma organizada, a tabela de tokens e os erros de um arquivo."""
    largura = 64
    linha_divisoria = "-" * largura

    print(linha_divisoria)
    print(f" {nome}")
    print(linha_divisoria)

    if tokens_encontrados:
        print(f" {'LIN':<4} {'TIPO':<15} LEXEMA")
        print(f" {'-' * 4} {'-' * 15} {'-' * 20}")
        for tipo, lexema, linha in tokens_encontrados:
            print(f" {linha:<4} {tipo:<15} {lexema}")
    else:
        print(" (nenhum token reconhecido)")

    if erros:
        print(linha_divisoria)
        print(f" ERROS LEXICOS ({len(erros)}):")
        for erro in erros:
            print(f"   - {erro}")

    print(linha_divisoria)
    situacao = "OK" if not erros else "COM ERROS"
    print(f" {len(tokens_encontrados)} token(s) reconhecido(s), {len(erros)} erro(s)  [{situacao}]")
    print(linha_divisoria)


def analisar_arquivo(caminho):
    """Le, tokeniza e imprime o relatorio de um arquivo-fonte.

    Retorna True se nao houve erro lexico, False caso contrario - usado
    tanto pelo modo "um arquivo" quanto pelo modo "demonstracao".
    """
    if not caminho.is_file():
        print(f"Erro: arquivo '{caminho}' nao encontrado.")
        return False
    try:
        codigo = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Erro: '{caminho}' nao parece ser um arquivo de texto valido (UTF-8).")
        return False

    tokens_encontrados, erros = tokenize(codigo)
    imprimir_relatorio(caminho.name, tokens_encontrados, erros)
    return not erros


def rodar_exemplos():
    """Roda o analisador sobre todos os programas em examples/, em ordem.

    Serve como demonstracao/verificacao manual: cada arquivo mostra se
    o analisador reconhece exatamente o que era esperado (0 erros nos
    exemplos validos, os erros certos no exemplo de erros).
    """
    pasta = Path(__file__).parent / "examples"
    arquivos = sorted(pasta.glob("*.mini"))

    if not arquivos:
        print(f"Nenhum arquivo .mini encontrado em '{pasta}'.")
        return False

    tudo_ok = True
    for caminho in arquivos:
        if not analisar_arquivo(caminho):
            tudo_ok = False
        print()

    return tudo_ok


def main():
    # Sem argumento: roda todos os exemplos de examples/, um atras do
    # outro (serve de demonstracao). Com argumento: analisa so aquele
    # arquivo especifico.
    if len(sys.argv) > 1:
        ok = analisar_arquivo(Path(sys.argv[1]))
    else:
        ok = rodar_exemplos()

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
