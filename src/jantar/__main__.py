"""Ponto de entrada: ``python -m jantar``.

    python -m jantar                          # abre a interface
    python -m jantar --estrategia monitor     # já começa no monitor
    python -m jantar --sem-interface --tempo 10 --estrategia ingenua --forcar-deadlock
"""

from __future__ import annotations

import argparse
import time

from .estrategias import ESTRATEGIAS


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="jantar", description="Jantar dos Filósofos com threads reais")
    p.add_argument("--estrategia", choices=list(ESTRATEGIAS), default="ingenua")
    p.add_argument("--filosofos", type=int, default=5)
    p.add_argument("--velocidade", type=float, default=1.0)
    p.add_argument("--sem-interface", action="store_true", help="roda no terminal e imprime métricas")
    p.add_argument("--tempo", type=float, default=10, help="duração no modo sem interface")
    p.add_argument("--forcar-deadlock", action="store_true", help="força o deadlock logo no início")
    p.add_argument("--captura", help="salva um PNG da interface e sai (para docs/slides)")
    p.add_argument("--apos", type=float, default=3.0, help="segundos até a captura")
    a = p.parse_args(argv)

    if a.sem_interface:
        from .simulacao import Simulacao

        with Simulacao(a.estrategia, a.filosofos, velocidade=a.velocidade) as sim:
            if a.forcar_deadlock:
                time.sleep(0.3)
                sim.forcar_deadlock()
            fim = time.monotonic() + a.tempo
            while time.monotonic() < fim:
                time.sleep(1)
                r = sim.retrato()
                status = f"DEADLOCK {r.deadlock}" if r.deadlock else ""
                print(f"{r.tempo:5.1f}s  refeições {r.refeicoes}  total {r.total}  {status}", flush=True)
        return

    from .interface import Interface

    Interface(a.estrategia, a.filosofos, a.velocidade).rodar(
        captura=a.captura, apos=a.apos, forcar_em=0.5 if a.forcar_deadlock else None
    )


if __name__ == "__main__":
    main()
