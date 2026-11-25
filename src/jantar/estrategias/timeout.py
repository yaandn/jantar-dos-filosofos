from ..mesa import Parada
from .base import Estrategia


class Timeout(Estrategia):
    """Tenta e solta: sem o 2º garfo, devolve o 1º e tenta de novo depois.

    Quebra a não preempção (o filósofo abre mão do que tem). A espera
    aleatória (backoff) desfaz a simetria entre os filósofos; com uma espera
    fixa e filósofos perfeitamente sincronizados, o resultado seria livelock.
    """

    chave = "timeout"
    nome = "Timeout"
    quebra = "não preempção"

    def __init__(self, mesa, *, espera=(0.05, 0.6)):
        super().__init__(mesa)
        self.espera = espera

    def pegar(self, f):
        m = self.mesa
        esq, dir_ = m.esquerdo(f.indice), m.direito(f.indice)
        while True:
            if m.parar.is_set():
                raise Parada
            m.adquirir(f, esq)
            m.ponto_de_encontro()
            if m.tentar_adquirir(f, dir_):
                return
            m.liberar(f, esq)
            f.tentativas += 1
            m.dormir(m.sortear(self.espera))  # backoff aleatório
