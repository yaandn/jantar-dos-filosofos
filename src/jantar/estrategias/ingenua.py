from .base import Estrategia


class Ingenua(Estrategia):
    """Pega o esquerdo, depois o direito. Pode travar (deadlock).

        pegar(garfo[i])
        pegar(garfo[(i+1) % N])
    """

    chave = "ingenua"
    nome = "Ingênua"
    quebra = "nenhuma"
    pode_travar = True

    def pegar(self, f):
        m = self.mesa
        self.pegar_em_ordem(f, m.esquerdo(f.indice), m.direito(f.indice))
