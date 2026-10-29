#Analisador Semantico - Trabalho Pratico (Aula 9: Analise Semantica)

#Este programa faz a terceira etapa do compilador: recebe a arvore
#sintatica (montada pelo analisador_sintatico.py) e verifica se o
#programa FAZ SENTIDO. Exemplo: "int x = sim;" esta certo na gramatica,
#mas guardar um bool numa variavel int nao faz sentido.

#O que e verificado:
#  - variavel ou funcao usada sem ter sido declarada
#  - nome declarado duas vezes no mesmo escopo
#  - tipos nas contas e comparacoes (ex.: int + bool nao pode)
#  - tipo do valor guardado numa variavel (declaracao e atribuicao)
#  - chamada de funcao: quantidade e tipo dos argumentos
#  - retorna: tipo do valor devolvido pela funcao
#  - condicao do caso_isso / loop precisa ser bool

#A arvore e lida UMA vez, de cima para baixo. Por isso, como no C, uma
#variavel ou funcao tem que ser declarada antes de ser usada.

#Tabela de simbolos: e uma PILHA de escopos. Cada escopo e um dicionario
#{nome: simbolo}. Ao entrar num bloco { } empilha um dicionario novo; ao
#sair, desempilha. Para achar um nome, procura do topo (escopo mais de
#dentro) ate a base (escopo global) - por isso uma variavel de dentro pode
#ter o mesmo nome de uma de fora (sombreamento).

#Regras de tipo da linguagem:
#  - int e decim sao numeros. Conta misturando int com decim da decim.
#  - um int pode ser guardado num decim (conversao automatica), mas um
#    decim NAO pode ser guardado num int (perderia a parte decimal).
#  - "+" tambem junta dois textos: "Ola, " + nome.
#  - comparacoes (== != < > <= >=) dao bool; < > <= >= so com numeros.

#Quando acha um erro, o programa anota e continua. A expressao com erro
#ganha o tipo "erro", que e aceito em qualquer lugar - assim um unico
#erro nao gera uma cascata de outros erros falsos.

#Para testar: sem nenhum argumento, roda sobre todos os arquivos de
#exemplo da pasta examples/.

import sys
from pathlib import Path
from analisador_sintatico import analisar

# Tipo de cada valor escrito direto no codigo (o "tipo" do no da arvore
# e o tipo do token que veio do analisador lexico)
TIPO_DO_LITERAL = {
    "INTEIRO": "int",
    "FLOAT": "decim",
    "STRING": "texto",
    "BOOLEANO": "bool",
}

NUMEROS = ["int", "decim"]
ARITMETICOS = ["+", "-", "*", "/", "^"]
COMPARACOES = ["<", ">", "<=", ">="]
# "==" e "!=" nao estao nas listas: aceitam qualquer par de tipos iguais

# Variaveis que guardam o andamento da analise. Elas sao zeradas no
# comeco de analisar_semantica(), antes de cada arquivo.
escopos = [{}]        # pilha de escopos; o primeiro e o global
tabela = []           # todos os simbolos declarados, na ordem (para imprimir)
erros = []            # erros encontrados: lista de (linha, mensagem)
funcao_atual = None   # funcao sendo analisada agora (None = fora de funcao)


def analisar_semantica(arvore):
    #Funcao principal: analisa a arvore inteira, comando por comando.
    #Devolve a tabela de simbolos e a lista de erros.
    global escopos, tabela, erros, funcao_atual   # "global": vai trocar as variaveis la de cima
    escopos = [{}]
    tabela = []
    erros = []
    funcao_atual = None

    for no in arvore["filhos"]:
        analisar_comando(no)

    erros.sort()   # ordena os erros pela linha
    return tabela, erros


def erro(linha, mensagem):
    erros.append((linha, mensagem))


def pode_guardar(tipo_destino, tipo_valor):
    #Diz se um valor do tipo "tipo_valor" pode ser guardado num lugar
    #(variavel, parametro ou retorno) do tipo "tipo_destino".
    if tipo_destino == "erro" or tipo_valor == "erro":
        return True   # o erro ja foi avisado antes, nao reclama de novo
    if tipo_destino == tipo_valor:
        return True
    if tipo_destino == "decim" and tipo_valor == "int":
        return True   # int vira decim sem perder nada (coercao)
    return False


# --------------------------- tabela de simbolos ---------------------------

def entrar_escopo():
    escopos.append({})


def sair_escopo():
    escopos.pop()


def nome_do_escopo():
    if len(escopos) == 1:
        return "global"
    if len(escopos) == 2:
        return "local"
    return "aninhado"


def declarar(nome, categoria, tipo, linha, parametros=None):
    #Coloca o nome no escopo atual (o do topo da pilha). So e erro se o
    #nome ja existir NESTE escopo - num escopo de fora pode.
    escopo_atual = escopos[-1]
    if nome in escopo_atual:
        linha_anterior = escopo_atual[nome]["linha"]
        erro(linha, f"'{nome}' ja foi declarado neste escopo (na linha {linha_anterior})")
        return
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
    #Procura o nome do escopo mais de dentro para o mais de fora.
    #Devolve o simbolo, ou None se o nome nao foi declarado.
    for escopo in reversed(escopos):
        if nome in escopo:
            return escopo[nome]
    return None


# -------------------------------- comandos --------------------------------

def analisar_comando(no):
    #Olha o tipo do no e chama a funcao que sabe analisar aquele comando.
    tipo = no["tipo"]
    if tipo == "DECL_VAR":
        analisar_declaracao(no)
    elif tipo == "DECL_FUNCAO":
        analisar_funcao(no)
    elif tipo == "ATRIBUICAO":
        analisar_atribuicao(no)
    elif tipo == "CHAMADA":
        tipo_da_chamada(no)   # chamada sozinha: o valor devolvido e ignorado
    elif tipo == "SE":
        checar_condicao(no, "caso_isso")
        for bloco in no["filhos"][1:]:   # bloco do caso_isso e, se tiver, do se_nao_isso
            analisar_bloco(bloco)
    elif tipo == "LOOP":
        checar_condicao(no, "loop")
        analisar_bloco(no["filhos"][1])
    elif tipo == "RETORNA":
        analisar_retorna(no)
    elif tipo == "MOSTRAR":
        tipo_valor = tipo_da_expressao(no["filhos"][0])
        if tipo_valor == "void":
            erro(no["linha"], "nao da para mostrar uma funcao void (ela nao devolve valor)")


def analisar_bloco(bloco):
    entrar_escopo()
    for comando in bloco["filhos"]:
        analisar_comando(comando)
    sair_escopo()


def checar_condicao(no, comando):
    tipo = tipo_da_expressao(no["filhos"][0])
    if tipo != "bool" and tipo != "erro":
        erro(no["linha"], f"a condicao do '{comando}' precisa ser bool (sim/nao), encontrado '{tipo}'")


def analisar_declaracao(no):
    # int x = 10;   -> o valor do no e "int x"; o split() separa em "int" e "x"
    tipo, nome = no["valor"].split()
    if tipo == "void":
        erro(no["linha"], f"variavel '{nome}' nao pode ser void (void e so para funcao)")
        tipo = "erro"
    # o valor e analisado ANTES de declarar: em "int x = x;" o x da
    # direita tem que ser outro x, ja declarado antes
    if no["filhos"]:
        tipo_valor = tipo_da_expressao(no["filhos"][0])
        if not pode_guardar(tipo, tipo_valor):
            erro(no["linha"], f"tipos incompativeis em '{nome}': esperado '{tipo}', encontrado '{tipo_valor}'")
    declarar(nome, "variavel", tipo, no["linha"])


def analisar_atribuicao(no):
    # x = 10;
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
    # int soma(int a, int b) { ... }
    global funcao_atual   # "global": vai trocar a variavel la de cima
    tipo, nome = no["valor"].split()
    if len(escopos) > 1:
        erro(no["linha"], f"funcao '{nome}' esta dentro de um bloco: funcao so pode ser declarada no escopo global")
        return

    parametros = no["filhos"][:-1]   # todos os filhos menos o ultimo sao os PARAM
    corpo = no["filhos"][-1]         # o ultimo filho e o BLOCO com o corpo

    # a funcao entra na tabela ANTES do corpo: assim ela pode chamar ela
    # mesma (recursao)
    tipos_parametros = []
    for parametro in parametros:
        tipo_parametro, nome_parametro = parametro["valor"].split()
        tipos_parametros.append(tipo_parametro)
    declarar(nome, "funcao", tipo, no["linha"], tipos_parametros)

    funcao_atual = {"nome": nome, "tipo": tipo, "achou_retorna": False}

    # parametros e corpo da funcao ficam no MESMO escopo: assim
    # "int f(int a) { int a = 1; }" da erro de nome repetido
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
    # retorna valor;   ou   retorna;
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
# As funcoes abaixo devolvem o TIPO da expressao ("int", "decim", "texto",
# "bool", "void" ou "erro"). O tipo e descoberto de baixo para cima:
# primeiro o tipo dos filhos, depois o do no (pos-ordem).

def tipo_da_expressao(no):
    tipo = no["tipo"]
    if tipo in TIPO_DO_LITERAL:
        return TIPO_DO_LITERAL[tipo]
    if tipo == "ID":
        return tipo_da_variavel(no)
    if tipo == "CHAMADA":
        return tipo_da_chamada(no)
    if tipo == "NEG":
        tipo_numero = tipo_da_expressao(no["filhos"][0])
        if tipo_numero in NUMEROS or tipo_numero == "erro":
            return tipo_numero
        erro(no["linha"], f"o sinal '-' so funciona com numero, encontrado '{tipo_numero}'")
        return "erro"
    if tipo == "OP":
        return tipo_da_operacao(no)
    return "erro"   # nao deveria acontecer: a sintatica so monta os nos acima


def tipo_da_variavel(no):
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
    nome = no["valor"]
    argumentos = no["filhos"][0]["filhos"]   # o filho da CHAMADA e o no ARGUMENTOS

    # analisa os argumentos primeiro, para achar erros dentro deles tambem
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
    operador = no["valor"]
    esquerda = tipo_da_expressao(no["filhos"][0])
    direita = tipo_da_expressao(no["filhos"][1])

    if esquerda == "erro" or direita == "erro":
        return "erro"   # o erro ja foi avisado mais embaixo na arvore

    dois_numeros = esquerda in NUMEROS and direita in NUMEROS

    if operador in ARITMETICOS:
        if dois_numeros:
            if esquerda == "decim" or direita == "decim":
                return "decim"   # conta com int e decim da decim
            return "int"
        if operador == "+" and esquerda == "texto" and direita == "texto":
            return "texto"       # juntar dois textos
    elif operador in COMPARACOES:
        if dois_numeros:
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
    #Le um arquivo, faz a analise lexica + sintatica + semantica e mostra o
    #resultado. Devolve True se nao teve nenhum erro.
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

    # A semantica so roda com a arvore completa: com erro lexico ou
    # sintatico a arvore fica pela metade e apareceriam erros falsos.
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
