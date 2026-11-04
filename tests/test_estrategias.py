"""Testes de comportamento (checkpoint 1): a ingênua trava quando forçada, o
detector acha o ciclo e vizinhos nunca comem juntos. Os testes das soluções
voltam junto com elas nos próximos checkpoints."""

import time

import pytest

from jantar.estrategias import ESTRATEGIAS
from jantar.mesa import Estado
from jantar.simulacao import Simulacao, ciclo_de_espera

RAPIDO = dict(pensar=(0.01, 0.05), comer=(0.01, 0.05), velocidade=1.0, semente=42)


def rodar(chave, segundos, forcar=False, n=5):
    with Simulacao(chave, n, **RAPIDO) as sim:
        if forcar:
            time.sleep(0.1)
            sim.forcar_deadlock()
        time.sleep(segundos)
        return sim.retrato(), sim.deadlock_em


def test_ingenua_trava_quando_forcada():
    r, deadlock_em = rodar("ingenua", 2.0, forcar=True)
    assert deadlock_em is not None
    assert sorted(r.deadlock) == [0, 1, 2, 3, 4]


@pytest.mark.parametrize("chave", list(ESTRATEGIAS))
def test_vizinhos_nunca_comem_juntos(chave):
    """Exclusão mútua: dois vizinhos nunca estão COMENDO ao mesmo tempo."""
    with Simulacao(chave, 5, **RAPIDO) as sim:
        fim = time.monotonic() + 1.5
        while time.monotonic() < fim:
            comendo = [f.estado is Estado.COMENDO for f in sim.mesa.filosofos]
            for i in range(5):
                assert not (comendo[i] and comendo[(i + 1) % 5]), f"P{i} e P{(i + 1) % 5} comendo juntos"
            time.sleep(0.002)


def test_ciclo_de_espera_detecta_ciclo_manual():
    sim = Simulacao("ingenua", 3)
    m = sim.mesa
    for i in range(3):  # P0 segura G0 e espera G1, P1 segura G1 e espera G2, ...
        m.garfos[i].dono = i
        m.filosofos[i].aguardando = (i + 1) % 3
    assert sorted(ciclo_de_espera(m)) == [0, 1, 2]
    m.filosofos[2].aguardando = None
    assert ciclo_de_espera(m) is None
