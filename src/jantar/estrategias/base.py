from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from ..mesa import Filosofo, Mesa


class Estrategia(ABC):
    """Protocolo para pegar e soltar os garfos.

    Para criar uma estratégia nova: herde desta classe, implemente ``pegar`` e
    ``soltar`` e registre em ``estrategias/__init__.py``.
    """

    chave: ClassVar[str]          # usado na linha de comando: --estrategia <chave>
    nome: ClassVar[str]           # nome exibido na interface
    quebra: ClassVar[str]         # condição de Coffman que a estratégia quebra
    pode_travar: ClassVar[bool] = False

    def __init__(self, mesa: Mesa) -> None:
        self.mesa = mesa

    @abstractmethod
    def pegar(self, f: Filosofo) -> None:
        """Retorna só quando ``f`` tem os dois garfos."""

    def soltar(self, f: Filosofo) -> None:
        m = self.mesa
        m.liberar(f, m.direito(f.indice))
        m.liberar(f, m.esquerdo(f.indice))

    # ajuda comum: pegar dois garfos em uma ordem, com o ponto do "forçar deadlock"
    def pegar_em_ordem(self, f: Filosofo, primeiro: int, segundo: int) -> None:
        self.mesa.adquirir(f, primeiro)
        self.mesa.ponto_de_encontro()
        self.mesa.adquirir(f, segundo)
