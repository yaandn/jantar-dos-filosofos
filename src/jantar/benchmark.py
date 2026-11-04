"""Roda cada estratégia por X segundos sem interface e gera a tabela de métricas.

    python -m jantar.benchmark --tempo 20 --velocidade 4 --saida resultados/

Gera ``metricas.csv`` (uma linha por estratégia) e ``metricas.md`` (tabela
pronta para colar no relatório).
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from .estrategias import ESTRATEGIAS
from .simulacao import Simulacao


def medir(chave: str, tempo: float, n: int, velocidade: float, forcar: bool, semente: int | None):
    with Simulacao(chave, n, velocidade=velocidade, semente=semente) as sim:
        if forcar:
            time.sleep(0.3)
            sim.forcar_deadlock()
        fim = time.monotonic() + tempo
        while time.monotonic() < fim:
            time.sleep(0.1)
        r = sim.retrato()
        travou = sim.deadlock_em is not None
    return {
        "estrategia": ESTRATEGIAS[chave].nome,
        "quebra": ESTRATEGIAS[chave].quebra,
        "refeicoes_total": r.total,
        "refeicoes_por_filosofo": " ".join(map(str, r.refeicoes)),
        "desvio": round(r.desvio, 2),
        "espera_max_s": round(max(r.espera_max), 2),
        "tentativas": sum(r.tentativas),
        "deadlock": "sim" if travou else "não",
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tempo", type=float, default=15, help="segundos reais por estratégia (padrão 15)")
    p.add_argument("--filosofos", type=int, default=5)
    p.add_argument("--velocidade", type=float, default=4, help="acelera pensar/comer (padrão 4x)")
    p.add_argument("--forcar-deadlock", action="store_true", help="dispara 'forçar deadlock' no início")
    p.add_argument("--estrategias", nargs="*", default=list(ESTRATEGIAS), choices=list(ESTRATEGIAS))
    p.add_argument("--semente", type=int, default=None)
    p.add_argument("--saida", type=Path, default=Path("resultados"))
    a = p.parse_args(argv)

    linhas = []
    for chave in a.estrategias:
        print(f"medindo {chave} por {a.tempo:.0f}s...", flush=True)
        linhas.append(medir(chave, a.tempo, a.filosofos, a.velocidade, a.forcar_deadlock, a.semente))

    a.saida.mkdir(parents=True, exist_ok=True)
    with open(a.saida / "metricas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    cab = ["Estratégia", "Quebra", "Refeições", "Por filósofo", "Desvio", "Espera máx (s)", "Tentativas", "Deadlock"]
    md = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    md += ["| " + " | ".join(str(v) for v in linha.values()) + " |" for linha in linhas]
    nota = (f"\n{a.filosofos} filósofos, {a.tempo:.0f} s por estratégia, velocidade {a.velocidade:g}x"
            + (", com 'forçar deadlock'" if a.forcar_deadlock else "") + ".\n")
    (a.saida / "metricas.md").write_text("\n".join(md) + "\n" + nota, encoding="utf-8")
    print("\n".join(md) + "\n" + nota)
    print(f"salvo em {a.saida}/metricas.csv e metricas.md")


if __name__ == "__main__":
    main()
