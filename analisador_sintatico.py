#Analisador Sintatico - Trabalho Pratico (Aula 5: Analise Sintatica)

#Este programa faz a segunda etapa do compilador: pega a lista de tokens
#que o analisador lexico ja reconheceu e verifica se ela segue a gramatica
#da linguagem, montando a arvore sintatica do programa.

#Tecnica usada: descida recursiva. Cada regra da gramatica abaixo virou
#uma funcao com o mesmo nome, e uma funcao chama a outra do mesmo jeito
#que uma regra aparece dentro da outra.

# Gramatica reconhecida (BNF simplificada: "|" e alternativa, "[ ]" e
# opcional, "{ }" e zero-ou-mais repeticoes, MAIUSCULO e um token vindo do
# analisador lexico, 'entre aspas' e um lexema exato):
#
#   programa    := { comando }
#   comando     := declaracao
#                | 'caso_isso' '(' expressao ')' bloco [ 'se_nao_isso' bloco ]
#                | 'loop' '(' expressao ')' bloco
#                | 'retorna' [ expressao ] ';'
#                | 'mostrar' '(' expressao ')' ';'
#                | IDENTIFICADOR ( '=' expressao | '(' argumentos ')' ) ';'
#   declaracao  := TIPO IDENTIFICADOR ( '(' parametros ')' bloco
#                                      | [ '=' expressao ] ';' )
#   parametros  := [ TIPO IDENTIFICADOR { ',' TIPO IDENTIFICADOR } ]
#   bloco       := '{' { comando } '}'
#   argumentos  := [ expressao { ',' expressao } ]
#
#   Expressoes: uma regra para cada nivel de prioridade, da mais fraca
#   (feita por ultimo) para a mais forte (feita primeiro):
#   expressao   := soma { ( '==' | '!=' | '<' | '>' | '<=' | '>=' ) soma }
#   soma        := produto { ( '+' | '-' ) produto }
#   produto     := unario { ( '*' | '/' ) unario }
#   unario      := '-' unario | potencia
#   potencia    := termo [ '^' unario ]
#   termo       := INTEIRO | FLOAT | STRING | BOOLEANO | '(' expressao ')'
#                | IDENTIFICADOR [ '(' argumentos ')' ]

import sys
from pathlib import Path
from analisador_lexico import tokenize

# O parser le os tokens um por um, da esquerda para a direita. Estas duas
# variaveis guardam onde ele esta. Elas sao preenchidas em analisar().
lista_tokens = []   # tokens vindos do lexico: (tipo, lexema, linha)
posicao = 0         # indice do token que esta sendo lido agora


def novo_no(tipo, valor=None, filhos=None, linha=None):
    #Cria um no da arvore. O no e so um dicionario com 4 informacoes:
    #  tipo   - o que o no representa (ex.: "DECL_VAR", "OP", "ID")
    #  valor  - o lexema, quando faz sentido (ex.: "+", "x", "int soma")
    #  filhos - lista com os nos que ficam embaixo dele
    #  linha  - linha do codigo-fonte (usada nas mensagens de erro)
    if filhos is None:
        filhos = []
    return {"tipo": tipo, "valor": valor, "filhos": filhos, "linha": linha}


# ---------------------------- ler os tokens -----------------------------

def token_atual():
    #Devolve o token da posicao atual: (tipo, lexema, linha). Quando a
    #lista acaba, devolve um token FIM "de mentira", pra nao ficar checando
    #o fim da lista toda hora.
    if posicao < len(lista_tokens):
        return lista_tokens[posicao]
    if lista_tokens:
        ultima_linha = lista_tokens[-1][2]
    else:
        ultima_linha = 1
    return ("FIM", "", ultima_linha)


def tipo_atual():
    return token_atual()[0]


def valor_atual():
    return token_atual()[1]


def linha_atual():
    return token_atual()[2]


def avancar():
    #Passa para o proximo token e devolve o lexema do token que ficou para tras.
    global posicao   # "global" porque esta funcao muda a variavel la de cima
    valor = valor_atual()
    posicao = posicao + 1
    return valor


def esperar_valor(valor):
    #O token atual TEM que ser esse lexema (ex.: ";"). Se for, avanca;
    #se nao for, e erro de sintaxe.
    if valor_atual() != valor:
        erro_sintatico(f"esperado {valor!r}, encontrado {valor_atual()!r}")
    return avancar()


def esperar_tipo(tipo):
    #Igual ao de cima, mas confere o tipo do token (ex.: "IDENTIFICADOR").
    if tipo_atual() != tipo:
        erro_sintatico(f"esperado {tipo!r}, encontrado {valor_atual()!r}")
    return avancar()


def erro_sintatico(mensagem):
    #A analise para no primeiro erro de sintaxe. O "raise" interrompe tudo
    #na hora e pula direto para o "except" da funcao analisar(), la embaixo.
    raise SyntaxError(f"linha {linha_atual()}: {mensagem}")


# ------------------------- regras da gramatica --------------------------

def programa():
    raiz = novo_no("PROGRAMA")
    while tipo_atual() != "FIM":
        raiz["filhos"].append(comando())
    return raiz


def comando():
    #Olha o token atual para decidir qual comando vem pela frente.
    tipo = tipo_atual()
    valor = valor_atual()
    if tipo == "TIPO":
        return declaracao()
    if valor == "caso_isso":
        return comando_se()
    if valor == "loop":
        return comando_loop()
    if valor == "retorna":
        return comando_retorna()
    if valor == "mostrar":
        return comando_mostrar()
    if tipo == "IDENTIFICADOR":
        return atribuicao_ou_chamada()
    erro_sintatico(f"comando invalido perto de {valor!r}")


def declaracao():
    # int x = 10;    ou    int soma(int a, int b) { ... }
    linha = linha_atual()
    tipo = esperar_tipo("TIPO")
    nome = esperar_tipo("IDENTIFICADOR")
    if valor_atual() == "(":
        return funcao(tipo, nome, linha)
    no = novo_no("DECL_VAR", tipo + " " + nome, linha=linha)
    if valor_atual() == "=":
        avancar()
        no["filhos"].append(expressao())
    esperar_valor(";")
    return no


def funcao(tipo, nome, linha):
    # int soma(int a, int b) { ... }   -> o tipo e o nome ja foram lidos
    no = novo_no("DECL_FUNCAO", tipo + " " + nome, linha=linha)
    esperar_valor("(")
    if valor_atual() != ")":
        no["filhos"].append(parametro())
        while valor_atual() == ",":
            avancar()
            no["filhos"].append(parametro())
    esperar_valor(")")
    no["filhos"].append(bloco())
    return no


def parametro():
    linha = linha_atual()
    tipo = esperar_tipo("TIPO")
    nome = esperar_tipo("IDENTIFICADOR")
    return novo_no("PARAM", tipo + " " + nome, linha=linha)


def bloco():
    # { comando comando ... }
    esperar_valor("{")
    no = novo_no("BLOCO")
    while valor_atual() != "}":
        no["filhos"].append(comando())
    esperar_valor("}")
    return no


def comando_se():
    # caso_isso (condicao) { ... } se_nao_isso { ... }
    linha = linha_atual()
    esperar_valor("caso_isso")
    esperar_valor("(")
    condicao = expressao()
    esperar_valor(")")
    filhos = [condicao, bloco()]
    if valor_atual() == "se_nao_isso":
        avancar()
        filhos.append(bloco())
    return novo_no("SE", None, filhos, linha)


def comando_loop():
    # loop (condicao) { ... }
    linha = linha_atual()
    esperar_valor("loop")
    esperar_valor("(")
    condicao = expressao()
    esperar_valor(")")
    return novo_no("LOOP", None, [condicao, bloco()], linha)


def comando_retorna():
    # retorna valor;    ou    retorna;
    linha = linha_atual()
    esperar_valor("retorna")
    no = novo_no("RETORNA", linha=linha)
    if valor_atual() != ";":
        no["filhos"].append(expressao())
    esperar_valor(";")
    return no


def comando_mostrar():
    # mostrar(valor);
    linha = linha_atual()
    esperar_valor("mostrar")
    esperar_valor("(")
    valor = expressao()
    esperar_valor(")")
    esperar_valor(";")
    return novo_no("MOSTRAR", None, [valor], linha)


def atribuicao_ou_chamada():
    # x = 5;    ou    soma(1, 2);
    linha = linha_atual()
    nome = esperar_tipo("IDENTIFICADOR")
    if valor_atual() == "(":
        no = chamada(nome, linha)
    else:
        esperar_valor("=")
        no = novo_no("ATRIBUICAO", nome, [expressao()], linha)
    esperar_valor(";")
    return no


def chamada(nome, linha):
    # soma(1, 2)   -> o nome ja foi lido
    esperar_valor("(")
    argumentos = novo_no("ARGUMENTOS")
    if valor_atual() != ")":
        argumentos["filhos"].append(expressao())
        while valor_atual() == ",":
            avancar()
            argumentos["filhos"].append(expressao())
    esperar_valor(")")
    return novo_no("CHAMADA", nome, [argumentos], linha)


# ------------------------------ expressoes ------------------------------
# Cada nivel de prioridade e uma funcao. Para ler os lados de uma conta,
# cada funcao chama a do nivel MAIS FORTE. Por isso as operacoes mais
# fortes ficam mais fundo na arvore e sao calculadas primeiro:
# "2 + 3 * 4" vira 2 + (3 * 4).
#
# O "while" junta varias contas do mesmo nivel da esquerda para a direita:
# "10 - 4 - 3" vira (10 - 4) - 3.

def expressao():
    # nivel mais fraco: comparacoes (a < b, x == 10)
    no = soma()
    while valor_atual() in ["==", "!=", "<", ">", "<=", ">="]:
        linha = linha_atual()
        operador = avancar()
        no = novo_no("OP", operador, [no, soma()], linha)
    return no


def soma():
    # + e -
    no = produto()
    while valor_atual() in ["+", "-"]:
        linha = linha_atual()
        operador = avancar()
        no = novo_no("OP", operador, [no, produto()], linha)
    return no


def produto():
    # * e /
    no = unario()
    while valor_atual() in ["*", "/"]:
        linha = linha_atual()
        operador = avancar()
        no = novo_no("OP", operador, [no, unario()], linha)
    return no


def unario():
    # menos na frente (-x). Ele pega a potencia inteira: -2 ^ 2 = -(2 ^ 2)
    if valor_atual() == "-":
        linha = linha_atual()
        avancar()
        return novo_no("NEG", "-", [unario()], linha)
    return potencia()


def potencia():
    # ^ e o nivel mais forte. Aqui e "if" e nao "while": o lado direito
    # chama unario() de novo, e e la dentro que entra a proxima potencia.
    # Assim 2 ^ 3 ^ 2 vira 2 ^ (3 ^ 2), como na matematica.
    no = termo()
    if valor_atual() == "^":
        linha = linha_atual()
        avancar()
        no = novo_no("OP", "^", [no, unario()], linha)
    return no


def termo():
    # o pedaco mais basico: numero, texto, sim/nao, nome, chamada ou ( ... )
    tipo = tipo_atual()
    valor = valor_atual()
    linha = linha_atual()
    if tipo in ["INTEIRO", "FLOAT", "STRING", "BOOLEANO"]:
        avancar()
        return novo_no(tipo, valor, linha=linha)
    if tipo == "IDENTIFICADOR":
        avancar()
        if valor_atual() == "(":
            return chamada(valor, linha)
        return novo_no("ID", valor, linha=linha)
    if valor == "(":
        avancar()
        no = expressao()
        esperar_valor(")")
        return no
    erro_sintatico(f"esperado um valor (numero, texto, identificador...), encontrado {valor!r}")


# --------------------------- rodar a analise ----------------------------

def analisar(codigo):
    #Roda o analisador lexico e, em cima do resultado, o sintatico.
    #Devolve (arvore, erros_lexicos, erro_sintatico). Se a sintaxe falhou,
    #a arvore fica None; se deu certo, erro_sintatico fica None.
    global lista_tokens, posicao
    lista_tokens, erros_lexicos = tokenize(codigo)
    posicao = 0   # comeca do primeiro token (importante ao ler varios arquivos)
    try:
        arvore = programa()
        return arvore, erros_lexicos, None
    except SyntaxError as erro:
        return None, erros_lexicos, str(erro)


def imprimir_arvore(no, profundidade=0):
    #Imprime a arvore indentada (2 espacos por nivel). Ela chama ela mesma
    #para cada filho, um nivel mais para dentro.
    prefixo = "  " * profundidade
    if no["valor"] is not None:
        print(f"{prefixo}{no['tipo']} ({no['valor']})")
    else:
        print(f"{prefixo}{no['tipo']}")
    for filho in no["filhos"]:
        imprimir_arvore(filho, profundidade + 1)


def imprimir_relatorio(nome, arvore, erros_lexicos, erro_sintatico):
    largura = 64
    linha_divisoria = "-" * largura

    print(linha_divisoria)
    print(f" {nome}")
    print(linha_divisoria)

    if erros_lexicos:
        print(f" ERROS LEXICOS ({len(erros_lexicos)}):")
        for erro in erros_lexicos:
            print(f"   - {erro}")
        print(linha_divisoria)

    if arvore is not None:
        if arvore["filhos"]:
            imprimir_arvore(arvore)
        else:
            print(" (nenhuma declaracao reconhecida)")
    else:
        print(f" ERRO SINTATICO: {erro_sintatico}")

    print(linha_divisoria)
    if not erros_lexicos and not erro_sintatico:
        situacao = "OK"
    else:
        situacao = "COM ERROS"
    print(f" [{situacao}]")
    print(linha_divisoria)


def analisar_arquivo(caminho):
    #Le um arquivo, faz a analise lexica + sintatica e mostra o resultado.
    #Devolve True se nao teve nenhum erro (lexico ou sintatico).
    if not caminho.is_file():
        print(f"Erro: arquivo '{caminho}' nao encontrado.")
        return False
    try:
        codigo = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Erro: '{caminho}' nao parece ser um arquivo de texto valido (UTF-8).")
        return False

    arvore, erros_lexicos, erro_sintatico = analisar(codigo)
    imprimir_relatorio(caminho.name, arvore, erros_lexicos, erro_sintatico)
    return not erros_lexicos and not erro_sintatico


def rodar_exemplos():
    #Roda o analisador em todos os arquivos de examples/, um de cada vez.
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
