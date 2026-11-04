from .base import Estrategia
from .ingenua import Ingenua

# Checkpoint 1: só a solução ingênua (para reproduzir o deadlock).
# As soluções (hierarquia, garçom, monitor, timeout) entram nos próximos checkpoints.
ESTRATEGIAS: dict[str, type[Estrategia]] = {cls.chave: cls for cls in (Ingenua,)}

__all__ = ["ESTRATEGIAS", "Estrategia"]
