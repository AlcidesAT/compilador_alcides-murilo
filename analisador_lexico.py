#Analisador Lexico - Trabalho Pratico (Aula 4: Analise Lexica)

#Este programa faz a primeira etapa de um compilador: pega um codigo-fonte
#(um texto) e separa em pedacos menores chamados "tokens" - palavras-
#chave, nomes de variavel, numeros, simbolos etc. Ele nao entende o
#significado do codigo, so identifica e classifica cada pedaco.

#A linguagem usa palavras em portugues (caso_isso, loop, retorna, int,
#decim, texto, sim, nao...) no lugar das palavras em ingles do enunciado
#(if, while, return, int...) - ver os conjuntos PALAVRAS_CHAVE/TIPOS/
#BOOLEANOS mais abaixo para a lista completa.

#O programa tambem detecta os 3 tipos de erro pedidos no enunciado:
#caractere invalido, string sem fechar, e identificador comecando com numero.

#Para testar: sem nenhum argumento, ele roda automaticamente sobre todos
#os arquivos de exemplo da pasta examples/ (funcao rodar_exemplos()).

import re
import sys
from pathlib import Path

# O programa testa os padroes na ordem em  que estao aqui, e usa o PRIMEIRO que encontrar - mesmo que outro mais
# abaixo tambem desse certo. Por isso os casos mais especificos vem
# antes dos mais gerais:
#   - IDENTIFICADOR_INVALIDO antes de NUMERO -> "1abc" vira UM erro so,
#     em vez de virar o numero "1" seguido do nome "abc".
#   - STRING (fechada certinho) antes de STRING_INVALIDA -> uma string
#     correta e reconhecida como valida, nao como erro.
#   - Operadores de 2 caracteres (==, !=, <=, >=) antes dos de 1
#     caractere, senao "==" virava dois sinais de "=" separados.
#
# Legenda dos "\letra" usados nos regex abaixo (sao classes de caractere
# prontas do modulo re, nao tem nada a ver com o \n de quebra de linha do
# Python em si - aqui e o regex quem interpreta a barra):
#   \d  = um digito           equivale a [0-9]
#   \w  = um "caractere de palavra"  equivale a [A-Za-z0-9_]
#   \s  = um espaco em branco  (espaco, tab, quebra de linha etc.)
#   \n  = quebra de linha (LF).  \t = tabulacao.  \r = retorno de carro (CR)
#   \.  \+  \*  \(  \)  = a barra antes de um simbolo especial do regex
#       (. + * ( ) [ ] | ^ $ ?) serve para escapa-lo, ou seja, tratar esse
#       simbolo como caractere literal em vez de metacaractere. Ex.: "\."
#       casa um ponto de verdade, sem o escape "." casaria qualquer caractere.
#   \'  = dentro do texto do regex e so um jeito de escrever o caractere
#       aspas simples (') sem confundir com as aspas que delimitam a string
#       do Python; para o regex em si, \' e ' teriam o mesmo efeito aqui.
# Outros simbolos usados nos padroes (nao sao "barra", mas ajudam a ler):
#   [...]   = classe de caracteres: casa QUALQUER UM dos caracteres listados
#   [^...]  = classe NEGADA: casa qualquer caractere que NAO esteja listado
#   +       = 1 ou mais repeticoes do que vem antes
#   *       = 0 ou mais repeticoes do que vem antes
#   |       = alternativa ("ou") entre duas opcoes
tokens = {
    # Comentário de uma linha: // até o final da linha
    # [^\n]* = zero ou mais caracteres que nao sejam quebra de linha
    "COMENTARIO": r"//[^\n]*",

    # Quebra de linha
    "QUEBRA_DE_LINHA": r"\n",

    # Espaços, tabulações e retorno de carro
    "ESPACO": r"[ \t\r]+",

    # Identificador inválido que começa com número
    # Exemplos: 1abc, 2x
    # \d+ = um ou mais digitos, seguido de uma letra/underline e depois
    # qualquer sequencia de \w (letras, digitos ou _)
    "IDENTIFICADOR_INVALIDO": r"\d+[A-Za-z_]\w*",

    # Strings com aspas simples ou duplas: "texto" ou 'texto'.
    # As duas alternativas (separadas por |) seguem a mesma ideia: aspas de
    # abertura, [^"\n]*/[^'\n]* = qualquer coisa que nao seja a propria
    # aspas nem quebra de linha, e aspas de fechamento do mesmo tipo.
    # Isso ja contempla aspas simples normalmente - ver testes no README.
    "STRING": r'"[^"\n]*"|\'[^\'\n]*\'',

    # Strings sem a aspas de fechamento (mesma ideia da STRING, mas sem
    # exigir a aspas final - por isso tem que vir DEPOIS de STRING na
    # ordem do dicionario, senao a string valida nunca seria tentada)
    "STRING_INVALIDA": r'"[^"\n]*|\'[^\'\n]*',

    # Números decimais: 3.14, 9.99
    # \d+ (parte inteira) + \. (ponto literal, escapado) + \d+ (parte decimal)
    "FLOAT": r"\d+\.\d+",

    # Números inteiros: 0, 42, 1000
    "INTEIRO": r"\d+",

    # Nomes de variáveis e funções
    # Exemplos: x, soma, valor1
    "IDENTIFICADOR": r"[a-zA-Z_][a-zA-Z0-9_]*",

    # Operadores: ==, !=, <=, >=, =, <, >, +, -, *, /
    # \+ e \* escapados porque + e * sozinhos seriam quantificadores
    "OPERADOR": r"==|!=|<=|>=|=|<|>|\+|-|\*|/",

    # Símbolos: ( ) { } ; ,
    "SIMBOLO": r"[(){};,]"
}

# Palavras reservadas da linguagem
PALAVRAS_CHAVE = {"caso_isso","se_nao_isso","loop","retorna","mostrar"}

# Tipos disponíveis na linguagem
TIPOS = {"int","decim","texto","bool","void"}

# Valores booleanos
BOOLEANOS = {"sim","nao"}

_IGNORADOS = {"ESPACO", "COMENTARIO"}
_PADRAO = re.compile("|".join(f"(?P<{tipo}>{regex})" for tipo, regex in tokens.items()))

def classificar_identificador(lexema):
    #Verifica se um nome reconhecido e na verdade uma palavra reservada
    #(palavra-chave, tipo ou booleano). Se nao for nenhuma delas, e so um
    #nome comum de variavel/funcao
    if lexema in PALAVRAS_CHAVE:
        return "PALAVRA_CHAVE"
    if lexema in TIPOS:
        return "TIPO"
    if lexema in BOOLEANOS:
        return "BOOLEANO"
    return "IDENTIFICADOR"

def tokenize(codigo):
    #Le o codigo inteiro e devolve a lista de tokens encontrados, junto
    #com a lista de erros.
    #Quando encontra um erro, o programa anota a mensagem e continua lendo
    #o resto do codigo, em vez de parar tudo no primeiro problema - assim,
    #no final, aparecem todos os erros de uma vez.

    resultado = []   # tokens reconhecidos: (tipo, lexema, linha)
    erros = []        # mensagens de erro encontradas
    linha = 1
    pos = 0

    while pos < len(codigo):
        join = _PADRAO.match(codigo, pos)

        if join is None:
            # nenhum padrao bateu: esse caractere nao existe na linguagem
            erros.append(f"linha {linha}: caractere invalido {codigo[pos]!r}")
            pos += 1
            continue

        tipo = join.lastgroup
        lexema = join.group()
        pos = join.end()

        if tipo == "QUEBRA_DE_LINHA":
            linha += 1
        elif tipo in _IGNORADOS:
            pass
        elif tipo == "IDENTIFICADOR_INVALIDO":
            erros.append(f"linha {linha}: identificador malformado {lexema!r} - (nao pode comecar com digito)")
        elif tipo == "STRING_INVALIDA":
            erros.append(f"linha {linha}: cadeia de caracteres nao terminada {lexema!r}")
        else:
            if tipo == "IDENTIFICADOR":
                tipo = classificar_identificador(lexema)
            resultado.append((tipo, lexema, linha))

    return resultado, erros

def imprimir_relatorio(nome, tokens_encontrados, erros):
    #Mostra na tela uma tabela com os tokens encontrados e a lista de
    #erros (se houver).
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
    #Le um arquivo, identifica os tokens e mostra o resultado na tela.
    #Devolve True se nao teve nenhum erro, False se teve.

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
    #Roda o analisador em todos os arquivos de examples/, um de cada vez.
    #Serve para testar visualmente: o esperado e 0 erros nos exemplos
    #validos, e exatamente os erros propositais no exemplo de erros.

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