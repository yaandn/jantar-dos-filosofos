import threading

from ..mesa import Estado, Parada
from .base import Estrategia


class Monitor(Estrategia):
    """Monitor de Tanenbaum: pega os dois garfos de uma vez, ou nenhum.

    Um único lock protege o vetor ``estado``. O filósofo com fome só passa a
    COMENDO se nenhum vizinho está comendo; senão dorme na sua variável de
    condição até um vizinho terminar e chamá-lo (``testar``).
    """

    chave = "monitor"
    nome = "Monitor"
    quebra = "posse e espera"

    def __init__(self, mesa):
        super().__init__(mesa)
        self.lock = threading.Lock()
        self.pode_comer = [threading.Condition(self.lock) for _ in range(mesa.n)]
        self.estado = [Estado.PENSANDO] * mesa.n

    def _testar(self, i):
        esq, dir_ = self.mesa.vizinhos(i)
        if (
            self.estado[i] is Estado.COM_FOME
            and self.estado[esq] is not Estado.COMENDO
            and self.estado[dir_] is not Estado.COMENDO
        ):
            self.estado[i] = Estado.COMENDO
            self.pode_comer[i].notify()

    def pegar(self, f):
        m, i = self.mesa, f.indice
        with self.lock:
            self.estado[i] = Estado.COM_FOME
            self._testar(i)
            while self.estado[i] is not Estado.COMENDO:
                self.pode_comer[i].wait(timeout=0.05)
                if m.parar.is_set():
                    self.estado[i] = Estado.PENSANDO
                    raise Parada
            # garantido livres: os dois vizinhos não estão comendo
            m.tentar_adquirir(f, m.esquerdo(i))
            m.tentar_adquirir(f, m.direito(i))

    def soltar(self, f):
        m, i = self.mesa, f.indice
        with self.lock:
            super().soltar(f)
            self.estado[i] = Estado.PENSANDO
            esq, dir_ = m.vizinhos(i)
            self._testar(esq)
            self._testar(dir_)
