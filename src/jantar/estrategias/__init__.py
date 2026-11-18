from .base import Estrategia
from .garcom import Garcom
from .hierarquia import Hierarquia
from .ingenua import Ingenua

# Checkpoint 2: ingênua (reproduz o deadlock) + duas soluções que quebram a espera circular.
# Monitor e timeout entram no próximo checkpoint.
# Ordem = ordem das teclas 1..3 na interface
ESTRATEGIAS: dict[str, type[Estrategia]] = {cls.chave: cls for cls in (Ingenua, Hierarquia, Garcom)}

__all__ = ["ESTRATEGIAS", "Estrategia"]
