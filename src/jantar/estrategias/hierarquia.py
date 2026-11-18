from .base import Estrategia


class Hierarquia(Estrategia):
    """Hierarquia de recursos (Dijkstra): sempre o garfo de menor número primeiro.

    O último filósofo acaba pegando o garfo 0 antes do N-1, invertendo a ordem
    dele em relação aos demais; com isso o ciclo de espera nunca fecha.
    """

    chave = "hierarquia"
    nome = "Hierarquia"
    quebra = "espera circular"

    def pegar(self, f):
        m = self.mesa
        a, b = m.esquerdo(f.indice), m.direito(f.indice)
        self.pegar_em_ordem(f, min(a, b), max(a, b))
