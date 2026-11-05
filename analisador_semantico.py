#Analisador Semantico - Trabalho Pratico (Aula 9: Analise Semantica)

#Terceira etapa do compilador:
#  1. lexico     - as palavras existem?
#  2. sintatico  - a frase esta bem escrita?
#  3. semantico  - a frase FAZ SENTIDO?   (este arquivo)
#Ex.: "int x = sim;" esta bem escrito, mas bool nao cabe em int.

#O que e verificado:
#  - nome usado sem ser declarado        mostrar(z);
#  - nome declarado duas vezes           int x = 5;  int x = 10;
#  - tipos nas contas e comparacoes      3 + sim
#  - tipo do valor guardado              int n = sim;
#  - argumentos da funcao                soma(3);  (soma precisa de 2)
#  - tipo do retorna                     int f() { retorna "oi"; }
#  - condicao do caso_isso / loop        caso_isso (x + 1)  (nao e bool)
#  - && e || so com bool                 x && sim  (x e int)

#Escopos: cada { } e uma "caixinha" com os nomes criados dentro dela. A
#lista "escopos" guarda as caixinhas abertas; a primeira e a global.
#    int x = 5;              escopos = [ {x} ]
#    caso_isso (x > 0) {     escopos = [ {x}, {} ]
#        int y = 1;          escopos = [ {x}, {y} ]
#    }                       escopos = [ {x} ]     <- o y sumiu
#So entram nomes criados: variaveis, funcoes e parametros.

#Percurso da arvore:
#  - comandos em PRE-ORDEM: primeiro o no, depois os filhos
#    (a funcao e anotada antes do corpo, para permitir recursao)
#  - expressoes em POS-ORDEM: primeiro os filhos, depois o no
#    (em a + b, primeiro o tipo de a e b, depois o do +)

#Quando acha um erro, anota e continua. A expressao com erro ganha o tipo
#"erro", que e aceito em qualquer lugar, para nao repetir o mesmo erro.

import sys
from pathlib import Path
from analisador_sintatico import analisar

# Tipo de cada valor escrito direto no codigo (ex.: 10 e int)
TIPO_DO_LITERAL = {
    "INTEIRO": "int",
    "FLOAT": "decim",
    "STRING": "texto",
    "BOOLEANO": "bool",
}

NUMEROS = ["int", "decim"]
ARITMETICOS = ["+", "-", "*", "/", "^"]
COMPARACOES = ["<", ">", "<=", ">="]
LOGICOS = ["&&", "||"]
# "==" e "!=" nao estao nas listas: aceitam qualquer par de tipos iguais

# Memoria da analise (zerada no comeco de cada arquivo)
escopos = [{}]        # caixinhas de nomes; a primeira e a global
tabela = []           # todos os nomes criados (para imprimir no fim)
erros = []            # erros encontrados: (linha, mensagem)
funcao_atual = None   # funcao sendo conferida agora (None = fora de funcao)


def analisar_semantica(arvore):
    #Funcao principal: zera tudo, confere cada comando do programa e
    #devolve a tabela e os erros.
    global escopos, tabela, erros, funcao_atual   # troca as variaveis la de cima
    escopos = [{}]
    tabela = []
    erros = []
    funcao_atual = None

    for no in arvore["filhos"]:   # os comandos do programa, um por vez
        analisar_comando(no)

    erros.sort()   # ordena pela linha
    return tabela, erros


def erro(linha, mensagem):
    #Anota um erro e deixa a analise continuar.
    erros.append((linha, mensagem))


def pode_guardar(tipo_destino, tipo_valor):
    #Diz se o valor cabe no lugar. Ex.: int em decim cabe, bool em int nao.
    if tipo_destino == "erro" or tipo_valor == "erro":
        return True   # o erro ja foi avisado, nao repete
    if tipo_destino == tipo_valor:
        return True
    if tipo_destino == "decim" and tipo_valor == "int":
        return True   # 10 vira 10.0
    return False


# --------------------------- tabela de simbolos ---------------------------

def entrar_escopo():
    #Abriu "{": coloca uma caixinha nova.
    escopos.append({})


def sair_escopo():
    #Fechou "}": tira a ultima caixinha (os nomes de dentro somem).
    escopos.pop()


def nome_do_escopo():
    #So para a coluna ESCOPO da tabela.
    if len(escopos) == 1:
        return "global"
    if len(escopos) == 2:
        return "local"
    return "aninhado"


def declarar(nome, categoria, tipo, linha, parametros=None):
    #Anota um nome NOVO na ultima caixinha. Erro se ele ja estiver nela.
    escopo_atual = escopos[-1]
    if nome in escopo_atual:
        linha_anterior = escopo_atual[nome]["linha"]
        erro(linha, f"'{nome}' ja foi declarado neste escopo (na linha {linha_anterior})")
        return
    # a "ficha" do nome (cada ficha e uma linha da tabela)
    simbolo = {
        "nome": nome,
        "categoria": categoria,      # "variavel", "parametro" ou "funcao"
        "tipo": tipo,                # na funcao, e o tipo do retorno
        "escopo": nome_do_escopo(),
        "linha": linha,
        "parametros": parametros,    # so na funcao: tipo de cada parametro
    }
    escopo_atual[nome] = simbolo
    tabela.append(simbolo)


def buscar(nome):
    #Procura um nome USADO, da ultima caixinha para a primeira.
    #Devolve a ficha, ou None se nao foi declarado.
    for escopo in reversed(escopos):
        if nome in escopo:
            return escopo[nome]
    return None


# -------------------------------- comandos --------------------------------

def analisar_comando(no):
    #Ve que comando e e chama a funcao certa (pre-ordem).
    tipo = no["tipo"]
    if tipo == "DECL_VAR":                 # int x = 5;
        analisar_declaracao(no)
    elif tipo == "DECL_FUNCAO":            # int soma(int a, int b) { ... }
        analisar_funcao(no)
    elif tipo == "ATRIBUICAO":             # x = 10;
        analisar_atribuicao(no)
    elif tipo == "CHAMADA":                # soma(1, 2);
        tipo_da_chamada(no)
    elif tipo == "SE":                     # caso_isso (...) { ... }
        checar_condicao(no, "caso_isso")
        for bloco in no["filhos"][1:]:     # pula a condicao, pega os blocos
            analisar_bloco(bloco)
    elif tipo == "LOOP":                   # loop (...) { ... }
        checar_condicao(no, "loop")
        analisar_bloco(no["filhos"][1])
    elif tipo == "RETORNA":                # retorna x;
        analisar_retorna(no)
    elif tipo == "MOSTRAR":                # mostrar(x);
        tipo_valor = tipo_da_expressao(no["filhos"][0])
        if tipo_valor == "void":
            erro(no["linha"], "nao da para mostrar uma funcao void (ela nao devolve valor)")


def analisar_bloco(bloco):
    #Abre a caixinha, confere o que tem dentro e fecha.
    entrar_escopo()
    for comando in bloco["filhos"]:
        analisar_comando(comando)
    sair_escopo()


def checar_condicao(no, comando):
    #A condicao do caso_isso / loop tem que ser bool.
    tipo = tipo_da_expressao(no["filhos"][0])
    if tipo != "bool" and tipo != "erro":
        erro(no["linha"], f"a condicao do '{comando}' precisa ser bool (sim/nao), encontrado '{tipo}'")


def analisar_declaracao(no):
    #int x = 10;  -> confere se o valor cabe e cria o x.
    tipo, nome = no["valor"].split()   # "int x" -> "int", "x"
    if tipo == "void":
        erro(no["linha"], f"variavel '{nome}' nao pode ser void (void e so para funcao)")
        tipo = "erro"
    # o valor e conferido ANTES de criar o x (em "int x = x;" o x da
    # direita tem que ser outro, criado antes)
    if no["filhos"]:
        tipo_valor = tipo_da_expressao(no["filhos"][0])
        if not pode_guardar(tipo, tipo_valor):
            erro(no["linha"], f"tipos incompativeis em '{nome}': esperado '{tipo}', encontrado '{tipo_valor}'")
    declarar(nome, "variavel", tipo, no["linha"])


def analisar_atribuicao(no):
    #x = 10;  -> confere se o x existe e se o valor cabe nele.
    nome = no["valor"]
    tipo_valor = tipo_da_expressao(no["filhos"][0])
    simbolo = buscar(nome)
    if simbolo is None:
        erro(no["linha"], f"variavel '{nome}' nao declarada")
    elif simbolo["categoria"] == "funcao":
        erro(no["linha"], f"'{nome}' e uma funcao, nao da para atribuir valor a ela")
    elif not pode_guardar(simbolo["tipo"], tipo_valor):
        erro(no["linha"], f"tipos incompativeis em '{nome}': esperado '{simbolo['tipo']}', encontrado '{tipo_valor}'")


def analisar_funcao(no):
    #int soma(int a, int b) { ... }  -> anota a funcao, confere o corpo e
    #ve se ela tem retorna.
    global funcao_atual
    tipo, nome = no["valor"].split()   # "int soma" -> "int", "soma"
    if len(escopos) > 1:   # esta dentro de um { }
        erro(no["linha"], f"funcao '{nome}' esta dentro de um bloco: funcao so pode ser declarada no escopo global")
        return

    parametros = no["filhos"][:-1]   # todos menos o ultimo: os parametros
    corpo = no["filhos"][-1]         # o ultimo: o { ... }

    # anota a funcao ANTES do corpo, para ela poder chamar ela mesma
    tipos_parametros = []
    for parametro in parametros:
        tipo_parametro, nome_parametro = parametro["valor"].split()
        tipos_parametros.append(tipo_parametro)
    declarar(nome, "funcao", tipo, no["linha"], tipos_parametros)

    funcao_atual = {"nome": nome, "tipo": tipo, "achou_retorna": False}

    # parametros e corpo na MESMA caixinha
    entrar_escopo()
    for parametro in parametros:
        tipo_parametro, nome_parametro = parametro["valor"].split()
        if tipo_parametro == "void":
            erro(parametro["linha"], f"parametro '{nome_parametro}' nao pode ser void")
        declarar(nome_parametro, "parametro", tipo_parametro, parametro["linha"])
    for comando in corpo["filhos"]:
        analisar_comando(comando)
    sair_escopo()

    if tipo != "void" and not funcao_atual["achou_retorna"]:
        erro(no["linha"], f"funcao '{nome}' deveria retornar '{tipo}', mas nao tem nenhum 'retorna'")

    funcao_atual = None


def analisar_retorna(no):
    #retorna x;  -> confere com o tipo da funcao onde ele esta.
    tipo_valor = "void"   # "retorna;" sem valor
    if no["filhos"]:
        tipo_valor = tipo_da_expressao(no["filhos"][0])

    if funcao_atual is None:
        erro(no["linha"], "'retorna' so pode ser usado dentro de uma funcao")
        return
    funcao_atual["achou_retorna"] = True

    nome = funcao_atual["nome"]
    tipo_esperado = funcao_atual["tipo"]
    if tipo_esperado == "void" and no["filhos"]:
        erro(no["linha"], f"funcao '{nome}' e void, entao o 'retorna' nao pode ter valor")
    elif tipo_esperado != "void" and not no["filhos"]:
        erro(no["linha"], f"funcao '{nome}' precisa retornar um valor '{tipo_esperado}'")
    elif not pode_guardar(tipo_esperado, tipo_valor):
        erro(no["linha"], f"retorno errado na funcao '{nome}': esperado '{tipo_esperado}', encontrado '{tipo_valor}'")


# ------------------------------- expressoes -------------------------------
# Descobrem o TIPO de uma expressao (pos-ordem: primeiro os filhos).

def tipo_da_expressao(no):
    #Devolve o tipo de qualquer expressao.
    tipo = no["tipo"]
    if tipo in TIPO_DO_LITERAL:        # 5, 2.5, "oi", sim
        return TIPO_DO_LITERAL[tipo]
    if tipo == "ID":                   # x
        return tipo_da_variavel(no)
    if tipo == "CHAMADA":              # soma(1, 2)
        return tipo_da_chamada(no)
    if tipo == "NEG":                  # -x
        tipo_numero = tipo_da_expressao(no["filhos"][0])
        if tipo_numero in NUMEROS or tipo_numero == "erro":
            return tipo_numero
        erro(no["linha"], f"o sinal '-' so funciona com numero, encontrado '{tipo_numero}'")
        return "erro"
    if tipo == "OP":                   # a + b, x > 0
        return tipo_da_operacao(no)
    return "erro"   # nao deveria acontecer


def tipo_da_variavel(no):
    #Nome usado numa conta: procura e devolve o tipo dele.
    nome = no["valor"]
    simbolo = buscar(nome)
    if simbolo is None:
        erro(no["linha"], f"variavel '{nome}' nao declarada")
        return "erro"
    if simbolo["categoria"] == "funcao":
        erro(no["linha"], f"'{nome}' e uma funcao: faltou chamar com parenteses, ex.: {nome}(...)")
        return "erro"
    return simbolo["tipo"]


def tipo_da_chamada(no):
    #soma(3, 4)  -> confere a quantidade e o tipo dos argumentos.
    nome = no["valor"]
    argumentos = no["filhos"][0]["filhos"]

    tipos_argumentos = []
    for argumento in argumentos:
        tipos_argumentos.append(tipo_da_expressao(argumento))

    simbolo = buscar(nome)
    if simbolo is None:
        erro(no["linha"], f"funcao '{nome}' nao declarada")
        return "erro"
    if simbolo["categoria"] != "funcao":
        erro(no["linha"], f"'{nome}' nao e uma funcao, e uma variavel do tipo '{simbolo['tipo']}'")
        return "erro"

    parametros = simbolo["parametros"]
    if len(tipos_argumentos) != len(parametros):
        erro(no["linha"], f"funcao '{nome}' espera {len(parametros)} argumento(s), mas recebeu {len(tipos_argumentos)}")
    else:
        for i in range(len(parametros)):
            if not pode_guardar(parametros[i], tipos_argumentos[i]):
                erro(no["linha"], f"argumento {i + 1} da funcao '{nome}': esperado '{parametros[i]}', encontrado '{tipos_argumentos[i]}'")
    return simbolo["tipo"]


def tipo_da_operacao(no):
    #a + b, x > 0, p && q  -> tipo dos dois lados, depois o do operador.
    operador = no["valor"]
    esquerda = tipo_da_expressao(no["filhos"][0])
    direita = tipo_da_expressao(no["filhos"][1])

    if esquerda == "erro" or direita == "erro":
        return "erro"

    dois_numeros = esquerda in NUMEROS and direita in NUMEROS

    if operador in ARITMETICOS:
        if dois_numeros:
            if esquerda == "decim" or direita == "decim":
                return "decim"   # int com decim da decim
            return "int"
        if operador == "+" and esquerda == "texto" and direita == "texto":
            return "texto"       # juntar textos
    elif operador in COMPARACOES:
        if dois_numeros:
            return "bool"
    elif operador in LOGICOS:
        if esquerda == "bool" and direita == "bool":
            return "bool"
    else:   # "==" e "!="
        if dois_numeros or (esquerda == direita and esquerda != "void"):
            return "bool"

    erro(no["linha"], f"tipos incompativeis: nao da para fazer '{esquerda}' {operador} '{direita}'")
    return "erro"


# ------------------------------ rodar e mostrar ------------------------------

def imprimir_tabela(simbolos):
    if not simbolos:
        print(" (nenhum simbolo declarado)")
        return
    print(f" {'NOME':<18} {'CATEGORIA':<10} {'TIPO':<18} {'ESCOPO':<8} LINHA")
    print(f" {'-' * 18} {'-' * 10} {'-' * 18} {'-' * 8} -----")
    for simbolo in simbolos:
        tipo = simbolo["tipo"]
        if simbolo["categoria"] == "funcao":
            tipo = tipo + " (" + ", ".join(simbolo["parametros"]) + ")"
        print(f" {simbolo['nome']:<18} {simbolo['categoria']:<10} {tipo:<18} {simbolo['escopo']:<8} {simbolo['linha']}")


def analisar_arquivo(caminho):
    #Le o arquivo, roda as 3 etapas e mostra o resultado.
    #Devolve True se nao teve nenhum erro.
    if not caminho.is_file():
        print(f"Erro: arquivo '{caminho}' nao encontrado.")
        return False
    try:
        codigo = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Erro: '{caminho}' nao parece ser um arquivo de texto valido (UTF-8).")
        return False

    linha_divisoria = "-" * 64
    print(linha_divisoria)
    print(f" {caminho.name}")
    print(linha_divisoria)

    arvore, erros_lexicos, erro_sintatico = analisar(codigo)

    # com erro lexico ou sintatico a arvore fica incompleta: nao roda a semantica
    if erros_lexicos or erro_sintatico:
        for erro_lexico in erros_lexicos:
            print(f" ERRO LEXICO: {erro_lexico}")
        if erro_sintatico:
            print(f" ERRO SINTATICO: {erro_sintatico}")
        print(linha_divisoria)
        print(" analise semantica nao executada: corrija os erros acima primeiro")
        print(linha_divisoria)
        return False

    simbolos, erros_semanticos = analisar_semantica(arvore)

    print(" TABELA DE SIMBOLOS")
    imprimir_tabela(simbolos)

    if erros_semanticos:
        print(linha_divisoria)
        print(f" ERROS SEMANTICOS ({len(erros_semanticos)}):")
        for linha, mensagem in erros_semanticos:
            print(f"   - linha {linha}: {mensagem}")

    print(linha_divisoria)
    if not erros_semanticos:
        situacao = "OK"
    else:
        situacao = "COM ERROS"
    print(f" {len(simbolos)} simbolo(s), {len(erros_semanticos)} erro(s) semantico(s)  [{situacao}]")
    print(linha_divisoria)
    return not erros_semanticos


def rodar_exemplos():
    #Roda em todos os arquivos de examples/.
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
    # com nome de arquivo: analisa so ele; sem nada: todos os exemplos
    if len(sys.argv) > 1:
        ok = analisar_arquivo(Path(sys.argv[1]))
    else:
        ok = rodar_exemplos()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
