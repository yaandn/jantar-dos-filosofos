# Como o grupo trabalha neste repositório

## Fluxo

1. Atualize a `main`: `git pull`
2. Crie uma branch por tarefa: `git checkout -b feat/grafo-de-recursos`
3. Commits pequenos, mensagem no imperativo: `adiciona grafo de alocação na interface`
4. Rode antes de enviar: `ruff check . && pytest -q`
5. `git push -u origin <branch>` e abra um **Pull Request**; outra pessoa revisa e faz o merge

Prefixos de branch: `feat/` (funcionalidade), `fix/` (correção), `docs/` (relatório, README), `exp/` (experimento).

## Divisão sugerida

| Pessoa | Área | Onde mexe |
|---|---|---|
| Carlos | Slides, design e GIF/vídeo da simulação | `docs/apresentacao/`, `docs/img/` |
| Yan | Lógica concorrente e estratégias | `src/jantar/estrategias/`, `mesa.py`, `simulacao.py` |
| Pedro | Interface e animação | `src/jantar/interface.py` |
| João | Relatório, métricas e aplicações | `docs/relatorio/`, `benchmark.py` |

## Próximas tarefas

As implementações de hierarquia, garçom, monitor e timeout já existem na branch
`estrategias-completas`. A cada checkpoint, traga as do roteiro do README para a `main`
(com os testes delas) e evolua o relatório.

- [x] Checkpoint 2: hierarquia de recursos e garçom + benchmark com repetições
- [x] Checkpoint 3: monitor e timeout + bateria final (315 execuções) + relatório no README
- [ ] Gravar GIF/vídeo da simulação para os slides
- [ ] Interface: grafo de alocação de recursos ao lado da mesa
- [ ] Extra: Chandy–Misra, estratégia assimétrica (par/ímpar), demonstração de livelock

## Adicionando uma estratégia

1. Crie `src/jantar/estrategias/minha.py` com uma classe que herda de `Estrategia`
   e define `chave`, `nome`, `quebra` e o método `pegar(f)` (e `soltar(f)` se precisar).
2. Registre em `src/jantar/estrategias/__init__.py`.
3. Ela aparece sozinha na interface, no benchmark e nos testes.
