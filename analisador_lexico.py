"""
Analisador Lexico - Trabalho Pratico (Aula 4: Analise Lexica)

Este programa faz a primeira etapa de um compilador: pega um codigo-fonte
(um texto) e separa em pedacos menores chamados "tokens" - palavras-
chave, nomes de variavel, numeros, simbolos etc. Ele nao entende o
significado do codigo, so identifica e classifica cada pedaco.

A linguagem usa palavras em portugues (caso_isso, loop, retorna, num,
decim, texto, sim, nao...) no lugar das palavras em ingles do enunciado
(if, while, return, int...) - ver os conjuntos PALAVRAS_CHAVE/TIPOS/
BOOLEANOS mais abaixo para a lista completa.

O programa tambem detecta 4 tipos de erro: caractere invalido, string
sem fechar, identificador comecando com numero, e numero mal escrito.

Para testar: sem nenhum argumento, ele roda automaticamente sobre todos
os arquivos de exemplo da pasta examples/ (funcao rodar_exemplos()).
"""

import re
import sys
from pathlib import Path

# A ordem desta lista importa! O programa testa os padroes na ordem em
# que estao aqui, e usa o PRIMEIRO que encontrar - mesmo que outro mais
# abaixo tambem desse certo. Por isso os casos mais especificos vem
# antes dos mais gerais:
#   - IDENTIFICADOR_INVALIDO antes de NUMERO -> "1abc" vira UM erro so,
#     em vez de virar o numero "1" seguido do nome "abc".
#   - STRING (fechada certinho) antes de STRING_INVALIDA -> uma string
#     correta e reconhecida como valida, nao como erro.
#   - NUMERO_INVALIDO antes de FLOAT/NUMERO -> "3." ou ".5" viram um
#     erro so, em vez de numero incompleto + sobra solta.
#   - Operadores de 2 caracteres (==, !=, <=, >=) antes dos de 1
#     caractere, senao "==" virava dois sinais de "=" separados.
tokens = {
    # "//" e o jeito formal de comentario (pedido no enunciado); "~>" e
    # um jeito extra, mais informal, que tambem funciona.
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

# Estas palavras nao podem virar nome de variavel ou funcao. O programa
# so verifica se um pedaco reconhecido e uma dessas palavras DEPOIS de
# identifica-lo como um nome comum (nunca antes) - assim "loopado"
# continua sendo reconhecido inteiro, e nao cortado em "loop" + "ado".
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
    """Verifica se um nome reconhecido e na verdade uma palavra reservada
    (palavra-chave, tipo ou booleano). Se nao for nenhuma delas, e so um
    nome comum de variavel/funcao."""
    if lexema in PALAVRAS_CHAVE:
        return "PALAVRA_CHAVE"
    if lexema in TIPOS:
        return "TIPO"
    if lexema in BOOLEANOS:
        return "BOOLEANO"
    return "IDENTIFICADOR"


def tokenize(codigo):
    """Le o codigo inteiro e devolve a lista de tokens encontrados, junto
    com a lista de erros.

    Quando encontra um erro, o programa anota a mensagem e continua lendo
    o resto do codigo, em vez de parar tudo no primeiro problema - assim,
    no final, aparecem todos os erros de uma vez.
    """
    resultado = []   # tokens reconhecidos: (tipo, lexema, linha)
    erros = []        # mensagens de erro encontradas
    linha = 1
    pos = 0

    while pos < len(codigo):
        casamento = _PADRAO.match(codigo, pos)

        if casamento is None:
            # nenhum padrao bateu: esse caractere nao existe na linguagem
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
    """Mostra na tela uma tabela com os tokens encontrados e a lista de
    erros (se houver)."""
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
    """Le um arquivo, identifica os tokens e mostra o resultado na tela.

    Devolve True se nao teve nenhum erro, False se teve.
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
    """Roda o analisador em todos os arquivos de examples/, um de cada vez.

    Serve para testar visualmente: o esperado e 0 erros nos exemplos
    validos, e exatamente os erros propositais no exemplo de erros.
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
    # Rodar com um nome de arquivo: analisa so aquele arquivo.
    # Rodar sem nada: analisa todos os exemplos de examples/.
    if len(sys.argv) > 1:
        ok = analisar_arquivo(Path(sys.argv[1]))
    else:
        ok = rodar_exemplos()

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
