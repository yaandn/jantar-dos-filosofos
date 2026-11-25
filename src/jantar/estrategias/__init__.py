from .base import Estrategia
from .garcom import Garcom
from .hierarquia import Hierarquia
from .ingenua import Ingenua
from .monitor import Monitor
from .timeout import Timeout

# Ordem = ordem das teclas 1..5 na interface
ESTRATEGIAS: dict[str, type[Estrategia]] = {
    cls.chave: cls for cls in (Ingenua, Hierarquia, Garcom, Monitor, Timeout)
}

__all__ = ["ESTRATEGIAS", "Estrategia"]
