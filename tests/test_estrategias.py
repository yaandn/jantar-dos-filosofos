"""Testes de comportamento das estratégias, sem interface.

Cobrem as 4 soluções e a ingênua, com mesas de 2 a 10 filósofos:
- corretude: as soluções comem e nunca travam, mesmo forçando o pior caso;
- a ingênua trava quando forçada, e o detector aponta o ciclo completo;
- exclusão mútua: vizinhos nunca comem juntos e um garfo tem um dono só;
- propriedades de cada solução (garçom limita os sentados, monitor e timeout).
"""

import time

import pytest

from jantar.estrategias import ESTRATEGIAS
from jantar.mesa import Estado
from jantar.simulacao import Simulacao

SOLUCOES = [k for k, cls in ESTRATEGIAS.items() if not cls.pode_travar]
TAMANHOS = [2, 3, 5, 7, 10]
RAPIDO = dict(pensar=(0.01, 0.05), comer=(0.01, 0.05), velocidade=1.0, semente=42)


def rodar(chave, segundos, forcar=False, n=5, **extra):
    with Simulacao(chave, n, **{**RAPIDO, **extra}) as sim:
        if forcar:
            time.sleep(0.1)
            sim.forcar_deadlock()
        time.sleep(segundos)
        return sim.retrato(), sim.deadlock_em


def test_registro_tem_as_cinco_estrategias():
    assert list(ESTRATEGIAS) == ["ingenua", "hierarquia", "garcom", "monitor", "timeout"]
    assert [k for k, c in ESTRATEGIAS.items() if c.pode_travar] == ["ingenua"]


# ------------------------------------------------------------------ corretude
@pytest.mark.parametrize("n", TAMANHOS)
@pytest.mark.parametrize("chave", SOLUCOES)
def test_solucoes_todos_comem_sem_deadlock(chave, n):
    r, deadlock_em = rodar(chave, 1.5, n=n)
    assert deadlock_em is None
    assert all(c > 0 for c in r.refeicoes), r.refeicoes


@pytest.mark.parametrize("n", [3, 5, 7, 10])
@pytest.mark.parametrize("chave", SOLUCOES)
def test_solucoes_resistem_ao_pior_caso(chave, n):
    r, deadlock_em = rodar(chave, 3.0, forcar=True, n=n)
    assert deadlock_em is None
    assert r.total > 0


@pytest.mark.parametrize("n", [3, 5, 7, 10])
def test_ingenua_trava_quando_forcada(n):
    r, deadlock_em = rodar("ingenua", 2.0, forcar=True, n=n)
    assert deadlock_em is not None
    assert sorted(r.deadlock) == list(range(n))  # o ciclo passa por todos


def test_deadlock_e_permanente():
    """Depois de travar, ninguém come mais."""
    with Simulacao("ingenua", 5, **RAPIDO) as sim:
        time.sleep(0.1)
        sim.forcar_deadlock()
        time.sleep(1.5)
        antes = sim.retrato().total
        time.sleep(1.0)
        assert sim.retrato().total == antes
        assert sim.deadlock is not None


# ------------------------------------------------------------------ exclusão mútua
@pytest.mark.parametrize("chave", list(ESTRATEGIAS))
def test_vizinhos_nunca_comem_juntos(chave):
    with Simulacao(chave, 5, **RAPIDO) as sim:
        fim = time.monotonic() + 1.5
        while time.monotonic() < fim:
            comendo = [f.estado is Estado.COMENDO for f in sim.mesa.filosofos]
            for i in range(5):
                assert not (comendo[i] and comendo[(i + 1) % 5]), f"P{i} e P{(i + 1) % 5} comendo juntos"
            time.sleep(0.002)


@pytest.mark.parametrize("chave", SOLUCOES)
def test_quem_come_tem_os_dois_garfos(chave):
    with Simulacao(chave, 5, **RAPIDO) as sim:
        m = sim.mesa
        fim = time.monotonic() + 1.5
        vistos = 0
        while time.monotonic() < fim:
            for f in m.filosofos:
                if f.estado is Estado.COMENDO:
                    donos = (m.garfos[m.esquerdo(f.indice)].dono, m.garfos[m.direito(f.indice)].dono)
                    # leitura sem trava: o filósofo pode ter acabado de soltar; só checamos quando ainda come
                    if f.estado is Estado.COMENDO and None not in donos:
                        assert donos == (f.indice, f.indice)
                        vistos += 1
            time.sleep(0.002)
        assert vistos > 0


# ------------------------------------------------------------------ propriedades de cada solução
def test_garcom_deixa_no_maximo_n_menos_1_com_garfo():
    with Simulacao("garcom", 5, **RAPIDO) as sim:
        time.sleep(0.1)
        sim.forcar_deadlock()
        fim = time.monotonic() + 2.0
        while time.monotonic() < fim:
            donos = {g.dono for g in sim.mesa.garfos if g.dono is not None}
            assert len(donos) <= 4
            time.sleep(0.002)


def test_timeout_desiste_quando_forcado():
    r, deadlock_em = rodar("timeout", 2.0, forcar=True)
    assert deadlock_em is None
    assert sum(r.tentativas) > 0  # alguém soltou o garfo e tentou de novo


def test_monitor_nunca_solta_e_tenta_de_novo():
    r, _ = rodar("monitor", 1.5, forcar=True)
    assert sum(r.tentativas) == 0  # pega os dois de uma vez: não há tentativa frustrada
