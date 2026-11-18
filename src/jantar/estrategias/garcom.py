import threading

from ..mesa import Parada
from .base import Estrategia


class Garcom(Estrategia):
    """Garçom/árbitro: um semáforo deixa no máximo N-1 filósofos à mesa.

        wait(garcom)          # garcom começa em N-1
        pegar esquerdo; pegar direito
        ...
        soltar ambos; signal(garcom)

    Com N-1 sentados sobra sempre um garfo, então pelo menos um consegue comer.
    """

    chave = "garcom"
    nome = "Garçom"
    quebra = "espera circular"

    def __init__(self, mesa):
        super().__init__(mesa)
        self.garcom = threading.Semaphore(mesa.n - 1)

    def pegar(self, f):
        m = self.mesa
        while not self.garcom.acquire(timeout=0.05):  # = wait(garcom), encerrável
            if m.parar.is_set():
                raise Parada
        try:
            self.pegar_em_ordem(f, m.esquerdo(f.indice), m.direito(f.indice))
        except BaseException:
            self.garcom.release()
            raise

    def soltar(self, f):
        super().soltar(f)
        self.garcom.release()  # signal(garcom)
