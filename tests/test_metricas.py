"""Testes do detector de ciclo e das métricas usadas no relatório."""

import pytest

from jantar.benchmark import jain
from jantar.simulacao import Simulacao, ciclo_de_espera


def test_ciclo_de_espera_detecta_ciclo_manual():
    sim = Simulacao("ingenua", 3)
    m = sim.mesa
    for i in range(3):  # P0 segura G0 e espera G1, P1 segura G1 e espera G2, ...
        m.garfos[i].dono = i
        m.filosofos[i].aguardando = (i + 1) % 3
    assert sorted(ciclo_de_espera(m)) == [0, 1, 2]
    m.filosofos[2].aguardando = None
    assert ciclo_de_espera(m) is None


def test_fila_de_espera_nao_e_ciclo():
    """P4 -> P0 -> P1 -> P2 -> P3 (P3 não espera ninguém): é fila, não deadlock."""
    sim = Simulacao("hierarquia", 5)
    m = sim.mesa
    for i in range(4):
        m.garfos[i].dono = i
    for i in range(3):
        m.filosofos[i].aguardando = i + 1
    m.filosofos[4].aguardando = 0
    assert ciclo_de_espera(m) is None


def test_ciclo_parcial_e_encontrado():
    """Um ciclo entre só dois filósofos também é deadlock."""
    sim = Simulacao("ingenua", 5)
    m = sim.mesa
    m.garfos[0].dono, m.garfos[1].dono = 0, 1
    m.filosofos[0].aguardando, m.filosofos[1].aguardando = 1, 0
    assert sorted(ciclo_de_espera(m)) == [0, 1]


@pytest.mark.parametrize(
    ("valores", "esperado"),
    [([10, 10, 10, 10, 10], 1.0), ([50, 0, 0, 0, 0], 0.2), ([1, 1], 1.0), ([3, 1], 0.8)],
)
def test_indice_de_jain(valores, esperado):
    assert jain(valores) == pytest.approx(esperado)


def test_jain_sem_refeicoes_vale_zero():
    assert jain([0, 0, 0]) == 0.0


@pytest.mark.parametrize("n", [1, 0])
def test_mesa_precisa_de_dois_filosofos(n):
    with pytest.raises(ValueError):
        Simulacao("ingenua", n)


def test_estrategia_desconhecida():
    with pytest.raises(ValueError):
        Simulacao("nao-existe", 5)
