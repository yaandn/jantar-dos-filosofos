"""Estado compartilhado da simulação: garfos, filósofos e a mesa que os une.

Cada garfo é um ``threading.Lock`` real. A mesa apenas *registra* quem segura
cada garfo e quem espera por qual, para que a interface e o detector de
deadlock possam observar o sistema sem interferir na concorrência.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum


class Estado(Enum):
    PENSANDO = "pensando"
    COM_FOME = "com fome"
    COMENDO = "comendo"


class Garfo:
    """Um recurso exclusivo. ``dono`` é só para observação (não é usado como trava)."""

    def __init__(self, indice: int) -> None:
        self.indice = indice
        self.lock = threading.Lock()
        self.dono: int | None = None

    def __repr__(self) -> str:  # pragma: no cover - ajuda no debug
        return f"Garfo({self.indice}, dono={self.dono})"


@dataclass
class Filosofo:
    indice: int
    estado: Estado = Estado.PENSANDO
    aguardando: int | None = None  # índice do garfo que está esperando, se houver
    refeicoes: int = 0
    tentativas: int = 0  # quantas vezes desistiu e tentou de novo (estratégia timeout)
    inicio_fome: float | None = None
    espera_max: float = 0.0
    espera_total: float = 0.0
    thread: threading.Thread | None = field(default=None, repr=False)

    def espera_atual(self, agora: float | None = None) -> float:
        if self.inicio_fome is None:
            return 0.0
        return (agora or time.monotonic()) - self.inicio_fome


class Parada(Exception):
    """Lançada dentro das threads quando a simulação é encerrada."""


class Mesa:
    """Mesa com ``n`` filósofos e ``n`` garfos.

    Parâmetros de tempo estão em segundos "de simulação"; ``velocidade`` divide
    todos eles (velocidade 2 = tudo duas vezes mais rápido).
    """

    def __init__(
        self,
        n: int = 5,
        *,
        pensar: tuple[float, float] = (0.4, 1.2),
        comer: tuple[float, float] = (0.4, 0.9),
        velocidade: float = 1.0,
        semente: int | None = None,
    ) -> None:
        if n < 2:
            raise ValueError("a mesa precisa de pelo menos 2 filósofos")
        self.n = n
        self.garfos = [Garfo(i) for i in range(n)]
        self.filosofos = [Filosofo(i) for i in range(n)]
        self.pensar = pensar
        self.comer = comer
        self.velocidade = velocidade
        self.rng = random.Random(semente)
        self._rng_lock = threading.Lock()

        self.parar = threading.Event()
        self.rodando = threading.Event()  # limpo = pausado
        self.rodando.set()

        # "Forçar deadlock": todos pegam o 1º garfo e se encontram nesta barreira
        # antes de tentar o 2º. Na estratégia ingênua isso trava a mesa.
        self._forcar = threading.Event()
        self._barreira = threading.Barrier(n)

        self.inicio = time.monotonic()

    # ------------------------------------------------------------- vizinhança
    def esquerdo(self, i: int) -> int:
        return i

    def direito(self, i: int) -> int:
        return (i + 1) % self.n

    def vizinhos(self, i: int) -> tuple[int, int]:
        return (i - 1) % self.n, (i + 1) % self.n

    # ------------------------------------------------------------- tempo
    def sortear(self, faixa: tuple[float, float]) -> float:
        with self._rng_lock:
            return self.rng.uniform(*faixa)

    def dormir(self, segundos: float, *, interrompivel: bool = False) -> None:
        """Dorme respeitando pausa, velocidade e parada.

        ``interrompivel``: acorda antes se alguém pediu "forçar deadlock"
        (usado no ``pensar()``, para todos ficarem com fome juntos).
        """
        restante = segundos
        passo = 0.02
        while restante > 0:
            if self.parar.is_set():
                raise Parada
            if interrompivel and self._forcar.is_set():
                return
            if not self.rodando.is_set():
                self.rodando.wait(0.1)
                continue
            fatia = min(passo * self.velocidade, restante)
            time.sleep(fatia / self.velocidade)
            restante -= fatia

    # ------------------------------------------------------------- garfos
    def adquirir(self, f: Filosofo, g: int) -> None:
        """``pegar(garfo)``: bloqueia até conseguir. Nunca solta o que já tem.

        O laço com timeout curto existe só para a thread poder ser encerrada;
        semanticamente é um lock bloqueante comum.
        """
        garfo = self.garfos[g]
        f.aguardando = g
        while not garfo.lock.acquire(timeout=0.05):
            if self.parar.is_set():
                f.aguardando = None
                raise Parada
        garfo.dono = f.indice
        f.aguardando = None

    def tentar_adquirir(self, f: Filosofo, g: int) -> bool:
        """``tryLock``: tenta uma vez, sem bloquear."""
        garfo = self.garfos[g]
        if garfo.lock.acquire(blocking=False):
            garfo.dono = f.indice
            return True
        return False

    def liberar(self, f: Filosofo, g: int) -> None:
        garfo = self.garfos[g]
        if garfo.dono == f.indice:
            garfo.dono = None
        garfo.lock.release()

    # ------------------------------------------------------------- forçar deadlock
    def forcar_deadlock(self) -> None:
        """Na próxima rodada, todos pegam o primeiro garfo antes de tentar o segundo."""
        self._barreira.reset()
        self._forcar.set()  # quem está pensando para de pensar (ver dormir)
        # estratégias que não passam pelo ponto de encontro (monitor) não limpam a flag
        t = threading.Timer(3.5, self._forcar.clear)
        t.daemon = True
        t.start()

    def ponto_de_encontro(self) -> None:
        """Chamado pelas estratégias entre o 1º e o 2º garfo."""
        if not self._forcar.is_set():
            return
        try:
            self._barreira.wait(timeout=1.5)
        except threading.BrokenBarrierError:
            pass
        finally:
            self._forcar.clear()

    @property
    def forcando(self) -> bool:
        return self._forcar.is_set()

    # ------------------------------------------------------------- observação
    def tempo(self) -> float:
        return time.monotonic() - self.inicio
