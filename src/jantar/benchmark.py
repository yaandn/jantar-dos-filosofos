"""Roda cada estratégia várias vezes sem interface e gera as tabelas de métricas.

    python -m jantar.benchmark --tempo 10 --repeticoes 5 --saida resultados/
    python -m jantar.benchmark --tempo 10 --repeticoes 5 --forcar-deadlock --saida resultados/forcado

Gera em ``--saida``:
  execucoes.csv  uma linha por execução (para conferir e refazer gráficos)
  resumo.csv     média e desvio-padrão por estratégia
  resumo.md      tabela pronta para o relatório

Métricas (por execução):
  refeicoes        total de refeições no intervalo           -> vazão
  vazao            refeições por segundo de simulação
  jain             índice de justiça de Jain sobre as refeições por filósofo
                   (1 = todos comeram igual; 1/N = só um comeu)
  espera_max_s     maior espera de um filósofo com fome       -> starvation
  deadlock         1 se o detector encontrou ciclo de espera  -> corretude
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from pathlib import Path

from .estrategias import ESTRATEGIAS
from .simulacao import Simulacao


def jain(valores: list[int]) -> float:
    s, q = sum(valores), sum(v * v for v in valores)
    return (s * s) / (len(valores) * q) if q else 0.0


def medir(chave: str, tempo: float, n: int, velocidade: float, forcar: bool, semente: int | None) -> dict:
    with Simulacao(chave, n, velocidade=velocidade, semente=semente) as sim:
        if forcar:
            time.sleep(0.3)
            sim.forcar_deadlock()
        fim = time.monotonic() + tempo
        while time.monotonic() < fim:
            time.sleep(0.1)
        r = sim.retrato()
        travou = sim.deadlock_em is not None
    tempo_sim = r.tempo * velocidade  # tempo "de simulação" (velocidade acelera pensar/comer)
    return {
        "estrategia": ESTRATEGIAS[chave].nome,
        "refeicoes": r.total,
        "vazao": round(r.total / tempo_sim, 3) if tempo_sim else 0.0,
        "jain": round(jain(r.refeicoes), 3),
        "espera_max_s": round(max(r.espera_max) * velocidade, 2),
        "deadlock": int(travou),
        "por_filosofo": " ".join(map(str, r.refeicoes)),
    }


def resumir(execucoes: list[dict]) -> dict:
    def ms(campo):
        v = [e[campo] for e in execucoes]
        return statistics.mean(v), (statistics.stdev(v) if len(v) > 1 else 0.0)

    ref, vaz, ja, esp = ms("refeicoes"), ms("vazao"), ms("jain"), ms("espera_max_s")
    return {
        "estrategia": execucoes[0]["estrategia"],
        "execucoes": len(execucoes),
        "refeicoes_media": round(ref[0], 1), "refeicoes_dp": round(ref[1], 1),
        "vazao_media": round(vaz[0], 2), "vazao_dp": round(vaz[1], 2),
        "jain_media": round(ja[0], 3), "jain_dp": round(ja[1], 3),
        "espera_max_media": round(esp[0], 2), "espera_max_dp": round(esp[1], 2),
        "deadlocks": sum(e["deadlock"] for e in execucoes),
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tempo", type=float, default=10, help="segundos reais por execução (padrão 10)")
    p.add_argument("--repeticoes", type=int, default=5, help="execuções por estratégia (padrão 5)")
    p.add_argument("--filosofos", type=int, default=5)
    p.add_argument("--velocidade", type=float, default=4, help="acelera pensar/comer (padrão 4x)")
    p.add_argument("--forcar-deadlock", action="store_true", help="dispara 'forçar deadlock' no início")
    p.add_argument("--estrategias", nargs="*", default=list(ESTRATEGIAS), choices=list(ESTRATEGIAS))
    p.add_argument("--saida", type=Path, default=Path("resultados"))
    a = p.parse_args(argv)

    todas, resumos = [], []
    for chave in a.estrategias:
        execs = []
        for k in range(a.repeticoes):
            print(f"{chave}: execução {k + 1}/{a.repeticoes} ({a.tempo:.0f}s)...", flush=True)
            e = medir(chave, a.tempo, a.filosofos, a.velocidade, a.forcar_deadlock, semente=k)
            e["execucao"] = k + 1
            execs.append(e)
        todas += execs
        resumos.append(resumir(execs))

    a.saida.mkdir(parents=True, exist_ok=True)
    for nome, linhas in (("execucoes.csv", todas), ("resumo.csv", resumos)):
        with open(a.saida / nome, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
            w.writeheader()
            w.writerows(linhas)

    cab = ["Estratégia", "Refeições", "Vazão (ref/s)", "Justiça (Jain)", "Espera máx (s)", "Deadlocks"]
    md = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for r in resumos:
        md.append(
            f"| {r['estrategia']} | {r['refeicoes_media']} ± {r['refeicoes_dp']} "
            f"| {r['vazao_media']} ± {r['vazao_dp']} "
            f"| {r['jain_media']} ± {r['jain_dp']} | {r['espera_max_media']} ± {r['espera_max_dp']} "
            f"| {r['deadlocks']}/{r['execucoes']} |"
        )
    nota = (f"\nMédia ± desvio-padrão de {a.repeticoes} execuções por estratégia; {a.filosofos} filósofos; "
            f"{a.tempo:.0f} s reais por execução a {a.velocidade:g}x (tempos em segundos de simulação)"
            + ("; com 'forçar deadlock' no início" if a.forcar_deadlock else "") + ".\n")
    (a.saida / "resumo.md").write_text("\n".join(md) + "\n" + nota, encoding="utf-8")
    print("\n".join(md) + "\n" + nota)
    print(f"salvo em {a.saida}/")


if __name__ == "__main__":
    main()
