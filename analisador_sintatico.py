#Analisador Sintatico - Trabalho Pratico (Aula 5: Analise Sintatica)

#Este programa faz a segunda etapa do compilador: pega a lista de tokens
#que o analisador lexico ja reconheceu e verifica se ela segue a gramatica
#da linguagem, montando a arvore sintatica do programa.

# Gramatica reconhecida (BNF simplificada: "|" e alternativa, "[ ]" e
# opcional, "{ }" e zero-ou-mais repeticoes, MAIUSCULO e um token vindo do
# analisador lexico, 'entre aspas' e um lexema exato):
#
#   programa    := { comando }
#   declaracao  := TIPO IDENTIFICADOR ( '(' parametros ')' bloco
#                                      | [ '=' expressao ] ';' )
#   parametros  := [ TIPO IDENTIFICADOR { ',' TIPO IDENTIFICADOR } ]
#   bloco       := '{' { comando } '}'
#   comando     := declaracao
#                | 'caso_isso' '(' expressao ')' bloco [ 'se_nao_isso' bloco ]
#                | 'loop' '(' expressao ')' bloco
#                | 'retorna' [ expressao ] ';'
#                | 'mostrar' '(' expressao ')' ';'
#                | IDENTIFICADOR ( '=' expressao | '(' argumentos ')' ) ';'
#   expressao   := termo { OPERADOR termo }
#   termo       := INTEIRO | FLOAT | STRING | BOOLEANO | '(' expressao ')'
#                | IDENTIFICADOR [ '(' argumentos ')' ]
#   argumentos  := [ expressao { ',' expressao } ]
#
# Simplificacao proposital: "expressao" nao diferencia precedencia entre
# operadores (+ - * / == != < > <= >=), so encadeia termo-operador-termo
# da esquerda para a direita. Isso da conta de tudo que a linguagem deste
# projeto usa, sem precisar de uma regra por nivel de precedencia.

import sys
from pathlib import Path
from analisador_lexico import tokenize


class No:
    #Um no da arvore sintatica: "tipo" identifica a regra/token que
    #originou o no, "valor" guarda o lexema quando faz sentido e "filhos"
    #guarda os nos vindos dessa regra.
    def __init__(self, tipo, valor=None, filhos=None):
        self.tipo = tipo
        self.valor = valor
        self.filhos = filhos or []


class ErroSintatico(Exception):
    #Lancado quando um token nao bate com o que a gramatica esperava.
    #A analise para assim que o primeiro erro sintatico e' encontrado -
    #diferente do analisador lexico, que continua apos um erro.
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _atual(self):
        #Devolve o token atual (tipo, lexema, linha). Quando a lista
        #acaba, devolve um token FIM "de mentira", pra nao ficar checando
        #limite de lista toda hora.
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        linha = self.tokens[-1][2] if self.tokens else 1
        return ("FIM", "", linha)

    def _checar(self, tipo=None, valor=None):
        tipo_atual, valor_atual, _ = self._atual()
        return (tipo is None or tipo_atual == tipo) and (valor is None or valor_atual == valor)

    def _avancar(self):
        token = self._atual()
        self.pos += 1
        return token

    def _esperar(self, tipo=None, valor=None):
        #Consome o token atual se ele bater com o esperado; senao, aborta
        #a analise com uma mensagem de erro (com a linha).
        if self._checar(tipo, valor):
            return self._avancar()
        tipo_atual, valor_atual, linha = self._atual()
        raise ErroSintatico(f"linha {linha}: esperado {valor or tipo!r}, encontrado {valor_atual!r}")

    # ---------------------- regras da gramatica -----------------------

    def programa(self):
        raiz = No("PROGRAMA")
        while not self._checar("FIM"):
            raiz.filhos.append(self.comando())
        return raiz

    def declaracao(self):
        tipo_tok = self._esperar("TIPO")
        nome_tok = self._esperar("IDENTIFICADOR")
        if self._checar(valor="("):
            return self._funcao(tipo_tok[1], nome_tok[1])
        no = No("DECL_VAR", f"{tipo_tok[1]} {nome_tok[1]}")
        if self._checar(valor="="):
            self._avancar()
            no.filhos.append(self.expressao())
        self._esperar(valor=";")
        return no

    def _funcao(self, tipo, nome):
        no = No("DECL_FUNCAO", f"{tipo} {nome}")
        self._esperar(valor="(")
        if not self._checar(valor=")"):
            no.filhos.append(self._parametro())
            while self._checar(valor=","):
                self._avancar()
                no.filhos.append(self._parametro())
        self._esperar(valor=")")
        no.filhos.append(self.bloco())
        return no

    def _parametro(self):
        tipo_tok = self._esperar("TIPO")
        nome_tok = self._esperar("IDENTIFICADOR")
        return No("PARAM", f"{tipo_tok[1]} {nome_tok[1]}")

    def bloco(self):
        self._esperar(valor="{")
        no = No("BLOCO")
        while not self._checar(valor="}"):
            no.filhos.append(self.comando())
        self._esperar(valor="}")
        return no

    def comando(self):
        tipo, valor, linha = self._atual()
        if tipo == "TIPO":
            return self.declaracao()
        if valor == "caso_isso":
            return self._comando_se()
        if valor == "loop":
            return self._comando_loop()
        if valor == "retorna":
            return self._comando_retorna()
        if valor == "mostrar":
            return self._comando_mostrar()
        if tipo == "IDENTIFICADOR":
            return self._atribuicao_ou_chamada()
        raise ErroSintatico(f"linha {linha}: comando invalido perto de {valor!r}")

    def _comando_se(self):
        self._esperar(valor="caso_isso")
        self._esperar(valor="(")
        condicao = self.expressao()
        self._esperar(valor=")")
        filhos = [condicao, self.bloco()]
        if self._checar(valor="se_nao_isso"):
            self._avancar()
            filhos.append(self.bloco())
        return No("SE", None, filhos)

    def _comando_loop(self):
        self._esperar(valor="loop")
        self._esperar(valor="(")
        condicao = self.expressao()
        self._esperar(valor=")")
        return No("LOOP", None, [condicao, self.bloco()])

    def _comando_retorna(self):
        self._esperar(valor="retorna")
        no = No("RETORNA")
        if not self._checar(valor=";"):
            no.filhos.append(self.expressao())
        self._esperar(valor=";")
        return no

    def _comando_mostrar(self):
        self._esperar(valor="mostrar")
        self._esperar(valor="(")
        expr = self.expressao()
        self._esperar(valor=")")
        self._esperar(valor=";")
        return No("MOSTRAR", None, [expr])

    def _atribuicao_ou_chamada(self):
        nome_tok = self._esperar("IDENTIFICADOR")
        if self._checar(valor="("):
            no = self._chamada(nome_tok[1])
        else:
            self._esperar(valor="=")
            no = No("ATRIBUICAO", nome_tok[1], [self.expressao()])
        self._esperar(valor=";")
        return no

    def _chamada(self, nome):
        self._esperar(valor="(")
        args = No("ARGUMENTOS")
        if not self._checar(valor=")"):
            args.filhos.append(self.expressao())
            while self._checar(valor=","):
                self._avancar()
                args.filhos.append(self.expressao())
        self._esperar(valor=")")
        return No("CHAMADA", nome, [args])

    def expressao(self):
        no = self.termo()
        while self._checar("OPERADOR"):
            operador = self._avancar()[1]
            no = No("OP", operador, [no, self.termo()])
        return no

    def termo(self):
        tipo, valor, linha = self._atual()
        if tipo in ("INTEIRO", "FLOAT", "STRING", "BOOLEANO"):
            self._avancar()
            return No(tipo, valor)
        if tipo == "IDENTIFICADOR":
            self._avancar()
            if self._checar(valor="("):
                return self._chamada(valor)
            return No("ID", valor)
        if valor == "(":
            self._avancar()
            expr = self.expressao()
            self._esperar(valor=")")
            return expr
        raise ErroSintatico(f"linha {linha}: esperado um valor (numero, texto, identificador...), encontrado {valor!r}")


def analisar(codigo):
    #Roda o analisador lexico e, em cima do resultado, o sintatico.
    #Devolve (arvore, erros_lexicos, erro_sintatico) - "arvore" e
    #"erro_sintatico" sao mutuamente exclusivos: se a sintaxe falhou, a
    #arvore fica None; se a analise terminou, erro_sintatico fica None.
    tokens, erros_lexicos = tokenize(codigo)
    try:
        arvore = Parser(tokens).programa()
        return arvore, erros_lexicos, None
    except ErroSintatico as erro:
        return None, erros_lexicos, str(erro)


def imprimir_arvore(no, profundidade=0):
    #Imprime a arvore sintatica indentada (2 espacos por nivel).
    prefixo = "  " * profundidade
    sufixo = f" ({no.valor})" if no.valor is not None else ""
    print(f"{prefixo}{no.tipo}{sufixo}")
    for filho in no.filhos:
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
        if arvore.filhos:
            imprimir_arvore(arvore)
        else:
            print(" (nenhuma declaracao reconhecida)")
    else:
        print(f" ERRO SINTATICO: {erro_sintatico}")

    print(linha_divisoria)
    situacao = "OK" if not erros_lexicos and not erro_sintatico else "COM ERROS"
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
