"""Gera as tabelas (Markdown) e os gráficos (PNG) do relatório a partir de execucoes.csv.

    python -m jantar.analise --entrada docs/resultados/final --imagens docs/img

Saídas:
  <entrada>/tabelas.md         tabelas E1, E2 e E3 prontas para o README
  <entrada>/resumo_e2.csv      médias e IC 95% por estratégia e N
  <imagens>/vazao_por_n.png    vazão × número de filósofos (E2)
  <imagens>/espera_por_n.png   espera máxima × número de filósofos (E2)
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

from .estrategias import ESTRATEGIAS

NOMES = {k: c.nome for k, c in ESTRATEGIAS.items()}
ORDEM = list(ESTRATEGIAS)
# paleta categórica validada (daltonismo e contraste) sobre fundo #FFFDF8
CORES = {"ingenua": "#D9443F", "hierarquia": "#2F6FD6", "garcom": "#1E9463", "monitor": "#7C4FD9", "timeout": "#C98A12"}
T95 = {4: 2.776, 9: 2.262, 19: 2.093}  # t de Student, 95%, por graus de liberdade


def ler(arq: Path) -> list[dict]:
    with open(arq, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(v):
    return float(v) if v not in ("", None) else None


def media_ic(valores: list[float]) -> tuple[float, float]:
    m = statistics.mean(valores)
    if len(valores) < 2:
        return m, 0.0
    t = T95.get(len(valores) - 1, 1.96)
    return m, t * statistics.stdev(valores) / math.sqrt(len(valores))


def fmt(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def grupos(linhas, exp):
    g = defaultdict(list)
    for r in linhas:
        if r["experimento"] == exp:
            g[(r["estrategia"], int(r["n"]))].append(r)
    return g


def tabela_e1(linhas) -> str:
    g = grupos(linhas, "E1")
    ns = sorted({n for _, n in g})
    cab = "| Estratégia | " + " | ".join(f"N = {n}" for n in ns) + " | Total | Tempo até travar |"
    out = [cab, "|" + "---|" * (len(ns) + 3)]
    for e in ORDEM:
        cel, tot, rep, ts = [], 0, 0, []
        for n in ns:
            rs = g.get((e, n), [])
            d = sum(int(r["deadlock"]) for r in rs)
            cel.append(f"{d}/{len(rs)}")
            tot += d
            rep += len(rs)
            ts += [num(r["t_deadlock_s"]) for r in rs if r["t_deadlock_s"]]
        tempo = f"{fmt(statistics.mean(ts), 1)} s" if ts else "—"
        out.append(f"| {NOMES[e]} | " + " | ".join(cel) + f" | **{tot}/{rep}** | {tempo} |")
    return "\n".join(out)


def resumo_e2(linhas) -> list[dict]:
    g = grupos(linhas, "E2")
    res = []
    for (e, n), rs in sorted(g.items(), key=lambda kv: (ORDEM.index(kv[0][0]), kv[0][1])):
        vz = media_ic([num(r["vazao"]) for r in rs])
        ja = media_ic([num(r["jain"]) for r in rs])
        em = media_ic([num(r["espera_max_s"]) for r in rs])
        ed = media_ic([num(r["espera_media_s"]) for r in rs if r["espera_media_s"]])
        res.append(dict(estrategia=e, n=n, execucoes=len(rs), deadlocks=sum(int(r["deadlock"]) for r in rs),
                        vazao=vz[0], vazao_ic=vz[1], jain=ja[0], jain_ic=ja[1],
                        espera_max=em[0], espera_max_ic=em[1], espera_media=ed[0], espera_media_ic=ed[1],
                        tentativas=statistics.mean(int(r["tentativas"]) for r in rs)))
    return res


def tabela_e2(res, n) -> str:
    out = ["| Estratégia | Vazão (ref/s) | Justiça (Jain) | Espera média (s) | Espera máx (s) | Deadlocks |",
           "|---|---|---|---|---|---|"]
    for r in [x for x in res if x["n"] == n]:
        out.append(f"| {NOMES[r['estrategia']]} | {fmt(r['vazao'])} ± {fmt(r['vazao_ic'])} "
                   f"| {fmt(r['jain'], 3)} | {fmt(r['espera_media'])} ± {fmt(r['espera_media_ic'])} "
                   f"| {fmt(r['espera_max'])} ± {fmt(r['espera_max_ic'])} | {r['deadlocks']}/{r['execucoes']} |")
    return "\n".join(out)


def tabela_e2_vazao(res) -> str:
    ns = sorted({r["n"] for r in res})
    out = ["| Estratégia | " + " | ".join(f"N = {n}" for n in ns) + " |", "|" + "---|" * (len(ns) + 1)]
    for e in ORDEM:
        cel = []
        for n in ns:
            r = next(x for x in res if x["estrategia"] == e and x["n"] == n)
            cel.append(f"{fmt(r['vazao'])} ± {fmt(r['vazao_ic'])}")
        out.append(f"| {NOMES[e]} | " + " | ".join(cel) + " |")
    return "\n".join(out)


def tabela_e3(linhas) -> str:
    g = grupos(linhas, "E3")
    out = ["| Estratégia | Refeições | Justiça (Jain) | Menor nº de refeições | Pior espera (s) | Deadlocks |",
           "|---|---|---|---|---|---|"]
    for e in ORDEM:
        rs = g.get((e, 5), [])
        if not rs:
            continue
        sem = [r for r in rs if r["deadlock"] == "0"] or rs
        out.append(f"| {NOMES[e]} | {fmt(statistics.mean(int(r['refeicoes']) for r in sem), 0)} "
                   f"| {fmt(statistics.mean(num(r['jain']) for r in sem), 3)} "
                   f"| {min(int(r['min_refeicoes']) for r in sem)} "
                   f"| {fmt(max(num(r['espera_max_s']) for r in sem), 1)} "
                   f"| {sum(int(r['deadlock']) for r in rs)}/{len(rs)} |")
    return "\n".join(out)


def grafico(res, campo, rotulo_y, titulo, arq):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
    fig.patch.set_facecolor("#FFFDF8")
    ax.set_facecolor("#FFFDF8")
    ns = sorted({r["n"] for r in res})
    finais = []
    for e in ORDEM:
        rs = [r for r in res if r["estrategia"] == e]
        ys = [r[campo] for r in rs]
        ics = [r[campo + "_ic"] for r in rs]
        ax.errorbar(ns, ys, yerr=ics, color=CORES[e], lw=2, marker="o", ms=7, capsize=4,
                    markeredgecolor="#FFFDF8", markeredgewidth=2, label=NOMES[e])
        finais.append([ys[-1], ys[-1], e])  # [posição do rótulo, valor real, estratégia]
    # rótulos diretos na ponta: afastados o mínimo para não colidir e recentrados nos valores reais
    finais.sort()
    faixa = ax.get_ylim()[1] - ax.get_ylim()[0]
    minimo = faixa * 0.055
    for i in range(1, len(finais)):
        if finais[i][0] - finais[i - 1][0] < minimo:
            finais[i][0] = finais[i - 1][0] + minimo
    desvio = statistics.mean(f[0] for f in finais) - statistics.mean(f[1] for f in finais)
    for f in finais:
        f[0] -= desvio
    for i in range(1, len(finais)):  # garante o espaçamento depois de recentrar
        if finais[i][0] - finais[i - 1][0] < minimo:
            finais[i][0] = finais[i - 1][0] + minimo
    x0 = ns[-1]
    for y_rot, y_real, e in finais:
        ax.plot([x0 + 0.12, x0 + 0.45], [y_real, y_rot], color=CORES[e], lw=1.5)
        ax.text(x0 + 0.55, y_rot, NOMES[e], color="#2A2F3F", va="center", fontsize=10.5)
    ax.set_xticks(ns)
    ax.set_xlim(ns[0] - 0.5, ns[-1] + 2.6)
    ax.set_xlabel("Número de filósofos")
    ax.set_ylabel(rotulo_y)
    ax.set_title(titulo, loc="left", fontsize=12.5, color="#10162B", pad=12)
    ax.grid(axis="y", color="#E6E0D2", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#B9B3A3")
    ax.tick_params(colors="#4A5064")
    ax.legend(loc="upper left", frameon=False, ncol=5, fontsize=9.5, bbox_to_anchor=(0, -0.16))
    fig.tight_layout()
    fig.savefig(arq, facecolor=fig.get_facecolor())
    plt.close(fig)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entrada", type=Path, default=Path("docs/resultados/final"))
    p.add_argument("--imagens", type=Path, default=Path("docs/img"))
    a = p.parse_args(argv)

    linhas = ler(a.entrada / "execucoes.csv")
    res = resumo_e2(linhas)
    with open(a.entrada / "resumo_e2.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)

    partes = [f"Total de execuções: {len(linhas)}",
              "", "## E1 — deadlocks no pior caso forçado", "", tabela_e1(linhas),
              "", "## E2 — vazão por número de filósofos (média ± IC 95%)", "", tabela_e2_vazao(res)]
    for n in sorted({r["n"] for r in res}):
        partes += ["", f"## E2 — N = {n}", "", tabela_e2(res, n)]
    partes += ["", "## E3 — longa duração (N = 5, 30 s reais = 120 s de simulação)", "", tabela_e3(linhas)]
    (a.entrada / "tabelas.md").write_text("\n".join(partes) + "\n", encoding="utf-8")
    print("\n".join(partes))

    a.imagens.mkdir(parents=True, exist_ok=True)
    grafico(res, "vazao", "Refeições por segundo", "Vazão por número de filósofos (média e IC 95%, 10 execuções)",
            a.imagens / "vazao_por_n.png")
    grafico(res, "espera_max", "Espera máxima (s)", "Maior espera de um filósofo (média e IC 95%, 10 execuções)",
            a.imagens / "espera_por_n.png")
    print("gráficos salvos em", a.imagens)


if __name__ == "__main__":
    main()
