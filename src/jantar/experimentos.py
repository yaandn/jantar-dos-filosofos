"""Bateria final de experimentos do relatório (checkpoint 3).

    python -m jantar.experimentos --saida docs/resultados/final --processos 2

Três experimentos, cada execução num processo novo (threads e locks zerados):

  E1  corretude   cenário forçado · 5 estratégias × N ∈ {5, 7, 10} × 10 repetições · 5 s
  E2  desempenho  cenário normal  · 5 estratégias × N ∈ {5, 7, 10} × 10 repetições · 8 s
  E3  longa       cenário normal  · 5 estratégias × N = 5 × 3 repetições · 30 s (starvation)

Tempos em segundos reais; a simulação roda a 4x (8 s reais = 32 s de simulação).
Cada execução vira uma linha de ``execucoes.csv`` assim que termina; rodar de novo
retoma de onde parou (pula o que já existe).
"""

from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import time
from pathlib import Path

from .benchmark import jain
from .estrategias import ESTRATEGIAS

VELOCIDADE = 4.0
CAMPOS = ["experimento", "estrategia", "cenario", "n", "rep", "duracao_s", "refeicoes", "vazao", "jain",
          "min_refeicoes", "espera_max_s", "espera_media_s", "deadlock", "t_deadlock_s", "tentativas",
          "por_filosofo"]


def plano() -> list[dict]:
    tarefas = []
    for exp, cenario, tamanhos, reps, dur in (
        ("E1", "forcado", (5, 7, 10), 10, 5.0),
        ("E2", "normal", (5, 7, 10), 10, 8.0),
        ("E3", "normal", (5,), 3, 30.0),
    ):
        for n in tamanhos:
            for rep in range(1, reps + 1):
                for chave in ESTRATEGIAS:
                    tarefas.append(dict(experimento=exp, estrategia=chave, cenario=cenario, n=n, rep=rep,
                                        duracao_s=dur))
    return tarefas


def chave_de(t: dict) -> tuple:
    return (t["experimento"], t["estrategia"], str(t["n"]), str(t["rep"]))


def executar(t: dict) -> dict:
    from .simulacao import Simulacao  # importado no processo filho

    with Simulacao(t["estrategia"], t["n"], velocidade=VELOCIDADE, semente=t["rep"]) as sim:
        if t["cenario"] == "forcado":
            time.sleep(0.3)
            sim.forcar_deadlock()
        fim = time.monotonic() + t["duracao_s"]
        while time.monotonic() < fim:
            time.sleep(0.1)
        r = sim.retrato()
        fs = sim.mesa.filosofos
        espera_total = sum(f.espera_total for f in fs)
        t_dead = sim.deadlock_em
    tempo_sim = r.tempo * VELOCIDADE
    return {
        **t,
        "refeicoes": r.total,
        "vazao": round(r.total / tempo_sim, 4) if tempo_sim else 0.0,
        "jain": round(jain(r.refeicoes), 4),
        "min_refeicoes": min(r.refeicoes),
        "espera_max_s": round(max(r.espera_max) * VELOCIDADE, 3),
        "espera_media_s": round(espera_total / r.total * VELOCIDADE, 3) if r.total else "",
        "deadlock": int(t_dead is not None),
        "t_deadlock_s": round(t_dead * VELOCIDADE, 2) if t_dead is not None else "",
        "tentativas": sum(r.tentativas),
        "por_filosofo": " ".join(map(str, r.refeicoes)),
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--saida", type=Path, default=Path("resultados/final"))
    p.add_argument("--processos", type=int, default=2, help="execuções em paralelo (padrão 2)")
    p.add_argument("--so", nargs="*", choices=["E1", "E2", "E3"], help="rodar só estes experimentos")
    a = p.parse_args(argv)

    a.saida.mkdir(parents=True, exist_ok=True)
    arq = a.saida / "execucoes.csv"
    feitas = set()
    if arq.exists():
        with open(arq, encoding="utf-8") as fh:
            feitas = {(r["experimento"], r["estrategia"], r["n"], r["rep"]) for r in csv.DictReader(fh)}
    tarefas = [t for t in plano() if chave_de(t) not in feitas and (not a.so or t["experimento"] in a.so)]
    total = len(plano())
    print(f"{len(feitas)} já feitas, {len(tarefas)} a fazer (plano completo: {total} execuções)", flush=True)

    novo = not arq.exists()
    with open(arq, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        ctx = mp.get_context("fork")
        with ctx.Pool(a.processos, maxtasksperchild=1) as pool:
            for k, linha in enumerate(pool.imap_unordered(executar, tarefas), 1):
                w.writerow(linha)
                fh.flush()
                if k % 10 == 0 or k == len(tarefas):
                    print(f"{k}/{len(tarefas)}  último: {linha['experimento']} {linha['estrategia']} "
                          f"n={linha['n']} rep={linha['rep']} deadlock={linha['deadlock']}", flush=True)
    print("fim")


if __name__ == "__main__":
    main()
