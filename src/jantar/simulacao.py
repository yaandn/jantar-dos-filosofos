"""Liga mesa + estratégia + threads + detector de deadlock + métricas."""

from __future__ import annotations

import statistics
import threading
import time
from dataclasses import dataclass

from .estrategias import ESTRATEGIAS, Estrategia
from .mesa import Estado, Filosofo, Mesa, Parada


def ciclo_de_espera(mesa: Mesa) -> list[int] | None:
    """Procura um ciclo no grafo de espera: filósofo -> dono do garfo que ele espera."""
    espera: dict[int, int] = {}
    for f in mesa.filosofos:
        g = f.aguardando
        if g is None:
            continue
        dono = mesa.garfos[g].dono
        if dono is not None and dono != f.indice:
            espera[f.indice] = dono
    for inicio in espera:
        caminho, atual = [], inicio
        while atual in espera and atual not in caminho:
            caminho.append(atual)
            atual = espera[atual]
        if atual in caminho:
            return caminho[caminho.index(atual):]
    return None


@dataclass
class Retrato:
    """Métricas num instante — o que a interface desenha e o benchmark registra."""

    tempo: float
    refeicoes: list[int]
    espera_max: list[float]
    tentativas: list[int]
    deadlock: list[int] | None

    @property
    def total(self) -> int:
        return sum(self.refeicoes)

    @property
    def desvio(self) -> float:
        return statistics.pstdev(self.refeicoes) if len(self.refeicoes) > 1 else 0.0

    @property
    def vazao(self) -> float:
        return self.total / self.tempo if self.tempo > 0 else 0.0


class Simulacao:
    def __init__(self, estrategia: str = "ingenua", n: int = 5, **opcoes_mesa) -> None:
        if estrategia not in ESTRATEGIAS:
            raise ValueError(f"estratégia desconhecida: {estrategia} (use {', '.join(ESTRATEGIAS)})")
        self.mesa = Mesa(n, **opcoes_mesa)
        self.estrategia: Estrategia = ESTRATEGIAS[estrategia](self.mesa)
        self.deadlock: list[int] | None = None
        self.deadlock_em: float | None = None
        self._detector: threading.Thread | None = None

    # ------------------------------------------------------------------ threads
    def _viver(self, f: Filosofo) -> None:
        m, e = self.mesa, self.estrategia
        try:
            while not m.parar.is_set():
                f.estado = Estado.PENSANDO
                m.dormir(m.sortear(m.pensar), interrompivel=True)  # pensar()

                f.estado = Estado.COM_FOME
                f.inicio_fome = time.monotonic()
                e.pegar(f)                                         # pegar os garfos
                esperou = time.monotonic() - f.inicio_fome
                f.inicio_fome = None
                f.espera_max = max(f.espera_max, esperou)
                f.espera_total += esperou

                f.estado = Estado.COMENDO
                f.refeicoes += 1
                m.dormir(m.sortear(m.comer))                       # comer()
                e.soltar(f)                                        # soltar os garfos
        except Parada:
            pass

    def _detectar(self) -> None:
        anterior = None
        while not self.mesa.parar.wait(0.15):
            ciclo = ciclo_de_espera(self.mesa)
            # mesmo ciclo em duas leituras seguidas = deadlock (evita falso positivo)
            if ciclo and anterior and sorted(ciclo) == sorted(anterior):
                if self.deadlock is None:
                    self.deadlock_em = self.mesa.tempo()
                self.deadlock = ciclo
            elif not ciclo:
                self.deadlock = None
            anterior = ciclo

    # ------------------------------------------------------------------ controle
    def iniciar(self) -> Simulacao:
        for f in self.mesa.filosofos:
            f.thread = threading.Thread(target=self._viver, args=(f,), name=f"P{f.indice}", daemon=True)
            f.thread.start()
        self._detector = threading.Thread(target=self._detectar, name="detector", daemon=True)
        self._detector.start()
        return self

    def parar(self, timeout: float = 2.0) -> None:
        self.mesa.parar.set()
        self.mesa.rodando.set()
        for f in self.mesa.filosofos:
            if f.thread:
                f.thread.join(timeout)
        if self._detector:
            self._detector.join(timeout)

    def pausar(self, pausado: bool) -> None:
        (self.mesa.rodando.clear if pausado else self.mesa.rodando.set)()

    def forcar_deadlock(self) -> None:
        self.mesa.forcar_deadlock()

    def retrato(self) -> Retrato:
        agora = time.monotonic()
        fs = self.mesa.filosofos
        return Retrato(
            tempo=self.mesa.tempo(),
            refeicoes=[f.refeicoes for f in fs],
            espera_max=[max(f.espera_max, f.espera_atual(agora)) for f in fs],
            tentativas=[f.tentativas for f in fs],
            deadlock=self.deadlock,
        )

    def __enter__(self) -> Simulacao:
        return self.iniciar()

    def __exit__(self, *exc) -> None:
        self.parar()
