#Gerador de Codigo Intermediario (TAC)

#TAC = codigo de tres enderecos: cada instrucao faz UMA operacao, com um
#destino, ate dois operandos e um operador.
#    x = (a + b) * c;     vira     t1 = a + b
#                                  t2 = t1 * c
#                                  x = t2

#A arvore e percorrida em POS-ORDEM: primeiro os filhos, depois o no. A
#folha devolve ela mesma (5, x) e cada conta guarda o resultado num
#temporario novo (t1, t2, ...) - estrategia ingenua. Como nenhum tN passa
#de um comando para o outro, a contagem volta para t1 a cada comando.

#Cada instrucao e um dicionario {op, destino, arg1, arg2}, para o assembly
#ler os campos direto. formatar() so monta o texto para mostrar.

import sys
from pathlib import Path
from analisador_sintatico import analisar
from analisador_semantico import analisar_semantica

funcoes = []      # instrucoes das funcoes
principal = []    # instrucoes do programa principal (main)
atual = principal # lista onde emitir() esta colocando agora
temporarios = 0   # ultimo tN criado no comando atual
rotulos = 0       # ultimo LN criado
nomes = {}        # nome no codigo -> nome no TAC (muda so no sombreamento)
renomeados = 0    # quantos nomes ja ganharam sufixo (x_1, x_2...)
locais = None     # variaveis da funcao atual (None = fora de funcao)


def gerar_tac(arvore):
    #Devolve a lista de instrucoes: funcoes primeiro, depois "main:".
    global funcoes, principal, atual, rotulos, nomes, renomeados
    funcoes = []
    principal = []
    atual = principal
    rotulos = 0
    nomes = {}
    renomeados = 0
    for no in arvore["filhos"]:
        gerar_comando(no)
    atual = funcoes
    emitir("rotulo", "main")
    return funcoes + principal


def emitir(op, destino=None, arg1=None, arg2=None):
    atual.append({"op": op, "destino": destino, "arg1": arg1, "arg2": arg2})


def novo_temporario():
    global temporarios
    temporarios = temporarios + 1
    return f"t{temporarios}"


def novo_rotulo():
    global rotulos
    rotulos = rotulos + 1
    return f"L{rotulos}"


def declarar(nome):
    #Variavel nova. O TAC nao tem { }, entao se ja existe outra com esse
    #nome (de fora do bloco), a nova vira x_1 para nao se misturarem.
    global renomeados
    nome_tac = nome
    if nome in nomes:
        renomeados = renomeados + 1
        nome_tac = f"{nome}_{renomeados}"
    nomes[nome] = nome_tac
    if locais is not None:
        locais.append(nome_tac)   # o assembly guarda essas na pilha da funcao
    return nome_tac


# -------------------------------- comandos --------------------------------

def gerar_comando(no):
    global temporarios
    temporarios = 0   # comando novo: volta para t1
    tipo = no["tipo"]

    if tipo == "DECL_VAR":                       # int x = 5;
        nome = no["valor"].split()[1]
        if no["filhos"]:
            valor = gerar_expressao(no["filhos"][0])   # valor antes de criar o x
            emitir("=", declarar(nome), valor)
        else:
            declarar(nome)

    elif tipo == "ATRIBUICAO":                   # x = 5;
        emitir("=", nomes[no["valor"]], gerar_expressao(no["filhos"][0]))

    elif tipo == "MOSTRAR":                      # mostrar(x);
        emitir("print", None, gerar_expressao(no["filhos"][0]))

    elif tipo == "RETORNA":                      # retorna x;   ou   retorna;
        valor = None
        if no["filhos"]:
            valor = gerar_expressao(no["filhos"][0])
        emitir("return", None, valor)

    elif tipo == "CHAMADA":                      # soma(1, 2);
        gerar_chamada(no, usa_valor=False)

    elif tipo == "DECL_FUNCAO":                  # int soma(int a, int b) { ... }
        gerar_funcao(no)

    elif tipo == "SE":                           # caso_isso (c) { } se_nao_isso { }
        senao = novo_rotulo()
        emitir("ifFalse", None, gerar_expressao(no["filhos"][0]), senao)
        gerar_bloco(no["filhos"][1])
        if len(no["filhos"]) == 3:               # tem se_nao_isso
            fim = novo_rotulo()
            emitir("goto", None, fim)
            emitir("rotulo", senao)
            gerar_bloco(no["filhos"][2])
            emitir("rotulo", fim)
        else:
            emitir("rotulo", senao)

    elif tipo == "LOOP":                         # loop (c) { }
        inicio = novo_rotulo()
        fim = novo_rotulo()
        emitir("rotulo", inicio)
        emitir("ifFalse", None, gerar_expressao(no["filhos"][0]), fim)
        gerar_bloco(no["filhos"][1])
        emitir("goto", None, inicio)
        emitir("rotulo", fim)


def gerar_bloco(bloco):
    global nomes
    antes = dict(nomes)       # guarda os nomes de fora
    for comando in bloco["filhos"]:
        gerar_comando(comando)
    nomes = antes             # fechou "}": os nomes de dentro somem


def gerar_funcao(no):
    #A funcao vira um rotulo com o nome dela. A instrucao do rotulo leva os
    #parametros (em ordem: a0, a1... no assembly) e as variaveis locais.
    global atual, nomes, locais
    antes = dict(nomes)
    atual = funcoes
    parametros = []
    for parametro in no["filhos"][:-1]:
        parametros.append(declarar(parametro["valor"].split()[1]))
    locais = []               # declarar() preenche enquanto gera o corpo
    emitir("funcao", no["valor"].split()[1], parametros, locais)
    for comando in no["filhos"][-1]["filhos"]:
        gerar_comando(comando)
    if atual[-1]["op"] != "return":   # void, ou o retorna ficou dentro de um if
        emitir("return")
    nomes = antes
    locais = None
    atual = principal


# ------------------------------- expressoes -------------------------------

def gerar_expressao(no):
    #Devolve onde ficou o valor: o proprio numero/nome, ou um tN.
    tipo = no["tipo"]
    if tipo == "ID":                             # x
        return nomes[no["valor"]]
    if tipo == "BOOLEANO":                       # sim -> 1, nao -> 0
        return "1" if no["valor"] == "sim" else "0"
    if tipo == "CHAMADA":                        # soma(1, 2)
        return gerar_chamada(no, usa_valor=True)
    if tipo == "NEG":                            # -x
        valor = gerar_expressao(no["filhos"][0])
        t = novo_temporario()
        emitir("neg", t, valor)
        return t
    if tipo == "OP":                             # a + b
        esquerda = gerar_expressao(no["filhos"][0])
        direita = gerar_expressao(no["filhos"][1])
        t = novo_temporario()
        emitir(no["valor"], t, esquerda, direita)
        return t
    return no["valor"]                           # 5, 2.5, "oi"


def gerar_chamada(no, usa_valor):
    #soma(a + 1, b)  ->  t1 = a + 1 / param t1 / param b / t2 = call soma, 2
    #Calcula todos os argumentos antes dos "param", para os param de uma
    #chamada dentro do argumento nao se misturarem com os desta.
    argumentos = []
    for argumento in no["filhos"][0]["filhos"]:
        argumentos.append(gerar_expressao(argumento))
    for argumento in argumentos:
        emitir("param", None, argumento)
    t = None
    if usa_valor:
        t = novo_temporario()
    emitir("call", t, no["valor"], len(argumentos))
    return t


# ------------------------------ rodar e mostrar ------------------------------

def formatar(i):
    #Monta o texto de uma instrucao (o rotulo fica sem recuo).
    op, destino, arg1, arg2 = i["op"], i["destino"], i["arg1"], i["arg2"]
    if op == "rotulo":
        return f"{destino}:"
    if op == "funcao":
        return (f"{destino}:".ljust(20) + f"// parametros: {', '.join(arg1) or '-'}"
                f"   locais: {', '.join(arg2) or '-'}")
    if op == "=":
        texto = f"{destino} = {arg1}"
    elif op == "neg":
        texto = f"{destino} = -{arg1}"
    elif op == "ifFalse":
        texto = f"ifFalse {arg1} goto {arg2}"
    elif op == "call":
        texto = f"call {arg1}, {arg2}"
        if destino:
            texto = f"{destino} = {texto}"
    elif op in ["goto", "param", "print", "return"]:
        texto = op if arg1 is None else f"{op} {arg1}"
    else:                                        # t1 = a + b
        texto = f"{destino} = {arg1} {op} {arg2}"
    return "    " + texto


def analisar_arquivo(caminho):
    if not caminho.is_file():
        print(f"Erro: arquivo '{caminho}' nao encontrado.")
        return False
    print("-" * 64)
    print(f" {caminho.name}")
    print("-" * 64)
    arvore, erros_lexicos, erro_sintatico = analisar(caminho.read_text(encoding="utf-8"))
    if erros_lexicos or erro_sintatico or analisar_semantica(arvore)[1]:
        print(" programa com erro: TAC nao gerado (veja 'uv run semantico')")
        return False
    for instrucao in gerar_tac(arvore):
        print(formatar(instrucao))
    return True


def main():
    # com nome de arquivo: so ele; sem nada: todos os exemplos
    if len(sys.argv) > 1:
        arquivos = [Path(sys.argv[1])]
    else:
        arquivos = sorted((Path(__file__).parent / "examples").glob("*.mini"))
    tudo_ok = True
    for caminho in arquivos:
        if not analisar_arquivo(caminho):
            tudo_ok = False
        print()
    sys.exit(0 if tudo_ok else 1)


if __name__ == "__main__":
    main()
