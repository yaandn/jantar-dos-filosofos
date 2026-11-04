"""Visualização da mesa com Pygame. Só LÊ o estado da simulação; quem decide
tudo são as threads dos filósofos.

Teclas
  D           forçar deadlock (todos pegam o 1º garfo juntos)
  Espaço      pausar / continuar
  ↑ / ↓       número de filósofos (2 a 10)
  R           reiniciar
  Esc         sair
"""

from __future__ import annotations

import math
import time

import pygame

from .estrategias import ESTRATEGIAS
from .mesa import Estado
from .simulacao import Simulacao

LARGURA, ALTURA = 1280, 760

# Paleta (a mesma dos slides)
FUNDO = (16, 22, 43)
PAINEL = (27, 35, 64)
LINHA = (44, 54, 88)
CREME = (245, 241, 232)
SUAVE = (185, 192, 212)
APAGADO = (142, 151, 179)
MESA_A, MESA_B = (42, 53, 96), (26, 34, 64)
MESA_TRAVADA = (74, 34, 52)
AZUL, AMARELO, VERDE, VERMELHO = (59, 130, 246), (242, 179, 61), (34, 160, 107), (229, 72, 77)

COR_ESTADO = {Estado.PENSANDO: AZUL, Estado.COM_FOME: AMARELO, Estado.COMENDO: VERDE}
# Soluções previstas para os próximos checkpoints (exibidas no painel)
PROXIMAS = ["Hierarquia de recursos", "Garçom (semáforo N−1)", "Monitor (Tanenbaum)", "Timeout com espera aleatória"]
FOME_LONGA = 3.0  # segundos de espera para pintar de vermelho (possível starvation)


def misturar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fonte(tamanho, negrito=False):
    for nome in ("Inter", "DejaVu Sans", "Arial", "Helvetica"):
        f = pygame.font.SysFont(nome, tamanho, bold=negrito)
        if f:
            return f
    return pygame.font.Font(None, tamanho)


class Interface:
    def __init__(self, estrategia="ingenua", n=5, velocidade=1.0):
        pygame.init()
        pygame.display.set_caption("Jantar dos Filósofos — Grupo CJPY")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.relogio = pygame.time.Clock()
        self.f = {k: fonte(s, b) for k, s, b in [
            ("titulo", 30, True), ("h", 22, True), ("txt", 18, False), ("txtb", 18, True),
            ("pequeno", 15, False), ("filo", 24, True), ("grande", 40, True)]}
        self.estrategia, self.n, self.velocidade = estrategia, n, velocidade
        self.pausado = False
        self.sim: Simulacao | None = None
        self.reiniciar()

    # ------------------------------------------------------------------ simulação
    def reiniciar(self):
        if self.sim:
            self.sim.parar(timeout=0.5)
        self.sim = Simulacao(self.estrategia, self.n, velocidade=self.velocidade).iniciar()
        self.pos_garfo = [None] * self.n
        self.cor_filo = [AZUL] * self.n
        self.pausado = False

    # ------------------------------------------------------------------ geometria
    def geometria(self):
        cx, cy = 430, 360
        r_mesa = 150 + 6 * max(0, self.n - 5)
        r_filo = r_mesa + 95
        raio = max(28, 46 - 3 * max(0, self.n - 5))
        return cx, cy, r_mesa, r_filo, raio

    def ang_filo(self, i):
        return -math.pi / 2 + 2 * math.pi * i / self.n

    def ang_garfo(self, g):
        # garfo g fica entre P(g-1) e P(g): é o esquerdo de Pg e o direito de P(g-1)
        return -math.pi / 2 + 2 * math.pi * (g - 0.5) / self.n

    # ------------------------------------------------------------------ desenho
    def desenhar_mesa(self, travado):
        t, m = self.tela, self.sim.mesa
        cx, cy, r_mesa, r_filo, raio = self.geometria()
        agora = time.monotonic()

        # mesa com gradiente simples
        base = MESA_TRAVADA if travado else MESA_A
        for k in range(r_mesa, 0, -4):
            pygame.draw.circle(t, misturar(base, MESA_B, 1 - k / r_mesa), (cx, cy), k)
        pygame.draw.circle(t, LINHA, (cx, cy), r_mesa, 2)

        # ciclo de espera (deadlock)
        ciclo = self.sim.deadlock
        if ciclo:
            for a in ciclo:
                b = m.garfos[m.filosofos[a].aguardando].dono if m.filosofos[a].aguardando is not None else None
                if b is None:
                    continue
                self.seta(self.pos_filo(a, r_filo - raio - 12), self.pos_filo(b, r_filo - raio - 12), VERMELHO)

        # garfos: deslizam para perto de quem os segura
        for g, garfo in enumerate(m.garfos):
            dono = garfo.dono
            if dono is None:
                a, r = self.ang_garfo(g), r_mesa - 45
            else:
                ad = self.ang_filo(dono)
                d = math.atan2(math.sin(self.ang_garfo(g) - ad), math.cos(self.ang_garfo(g) - ad))
                a, r = ad + d * 0.45, r_mesa + 20
            alvo = (a, r)
            atual = self.pos_garfo[g] or alvo
            atual = (atual[0] + (alvo[0] - atual[0]) * 0.25, atual[1] + (alvo[1] - atual[1]) * 0.25)
            self.pos_garfo[g] = atual
            a, r = atual
            cor = self.cor_filo[dono] if dono is not None else CREME
            dx, dy = math.cos(a) * 34, math.sin(a) * 34
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            pygame.draw.line(t, cor, (x - dx, y - dy), (x + dx, y + dy), 9)
            rotulo = self.f["pequeno"].render(f"G{g}", True, APAGADO)
            rx, ry = cx + (r_mesa - 90) * math.cos(self.ang_garfo(g)), cy + (r_mesa - 90) * math.sin(self.ang_garfo(g))
            t.blit(rotulo, rotulo.get_rect(center=(rx, ry)))

        # filósofos
        for f in m.filosofos:
            i = f.indice
            if travado and i in (ciclo or []):
                alvo, nome = VERMELHO, "travado"
            elif f.estado is Estado.COM_FOME and f.espera_atual(agora) > FOME_LONGA * (1 / self.velocidade):
                alvo, nome = VERMELHO, "passando fome"
            else:
                alvo, nome = COR_ESTADO[f.estado], f.estado.value
            self.cor_filo[i] = misturar(self.cor_filo[i], alvo, 0.3)
            x, y = self.pos_filo(i, r_filo)
            pygame.draw.circle(t, FUNDO, (x, y), raio + 5)
            pygame.draw.circle(t, self.cor_filo[i], (x, y), raio)
            s = self.f["filo"].render(f"P{i}", True, FUNDO)
            t.blit(s, s.get_rect(center=(x, y)))
            s = self.f["pequeno"].render(nome, True, misturar(self.cor_filo[i], CREME, 0.3))
            dy = -(raio + 16) if y < cy - 10 else raio + 16
            t.blit(s, s.get_rect(center=(x, y + dy)))

    def pos_filo(self, i, r):
        cx, cy, *_ = self.geometria()
        a = self.ang_filo(i)
        return int(cx + r * math.cos(a)), int(cy + r * math.sin(a))

    def seta(self, p, q, cor):
        pygame.draw.line(self.tela, cor, p, q, 4)
        a = math.atan2(q[1] - p[1], q[0] - p[0])
        ponta = [q, (q[0] - 16 * math.cos(a - 0.4), q[1] - 16 * math.sin(a - 0.4)),
                 (q[0] - 16 * math.cos(a + 0.4), q[1] - 16 * math.sin(a + 0.4))]
        pygame.draw.polygon(self.tela, cor, ponta)

    def texto(self, s, pos, fonte="txt", cor=CREME, centro=False):
        surf = self.f[fonte].render(s, True, cor)
        rect = surf.get_rect(center=pos) if centro else surf.get_rect(topleft=pos)
        self.tela.blit(surf, rect)
        return rect

    def desenhar_painel(self, retrato):
        t = self.tela
        x0, y = 860, 30
        pygame.draw.rect(t, PAINEL, (x0 - 24, 0, LARGURA - x0 + 24, ALTURA))
        self.texto("ESTRATÉGIA", (x0, y), "pequeno", AMARELO)
        y += 24
        cls = ESTRATEGIAS[self.estrategia]
        pygame.draw.rect(t, AMARELO, (x0 - 8, y - 3, 380, 30), border_radius=15)
        self.texto(cls.nome, (x0 + 4, y), "txtb", FUNDO)
        self.texto("esquerdo → direito", (x0 + 170, y + 2), "pequeno", FUNDO)
        y += 40
        self.texto("PRÓXIMOS CHECKPOINTS", (x0, y), "pequeno", APAGADO)
        y += 22
        for nome in PROXIMAS:
            self.texto(f"·  {nome}", (x0 + 4, y), "pequeno", APAGADO)
            y += 21

        y += 14
        self.texto("REFEIÇÕES  ·  ESPERA MÁX", (x0, y), "pequeno", AMARELO)
        y += 26
        maior = max(1, max(retrato.refeicoes))
        alt = max(18, min(30, int(260 / self.n)))
        for i in range(self.n):
            cor = VERMELHO if retrato.espera_max[i] > FOME_LONGA / self.velocidade else CREME
            self.texto(f"P{i}", (x0, y), "txtb", cor)
            pygame.draw.rect(t, LINHA, (x0 + 40, y + 5, 190, 10), border_radius=5)
            w = int(190 * retrato.refeicoes[i] / maior)
            if w:
                pygame.draw.rect(t, VERDE, (x0 + 40, y + 5, w, 10), border_radius=5)
            self.texto(str(retrato.refeicoes[i]), (x0 + 240, y), "txtb", cor)
            self.texto(f"{retrato.espera_max[i]:.1f}s", (x0 + 290, y), "txt", cor)
            y += alt

        y += 10
        self.texto(f"total {retrato.total}   ·   desvio {retrato.desvio:.2f}   ·   {retrato.tempo:.0f}s",
                   (x0, y), "txt", SUAVE)
        y += 26
        if any(retrato.tentativas):
            self.texto(f"tentativas (soltou e tentou de novo): {sum(retrato.tentativas)}", (x0, y), "txt", SUAVE)
        y += 34

        self.texto("CONTROLES", (x0, y), "pequeno", AMARELO)
        y += 24
        for linha in ["D  forçar deadlock", "Espaço  pausar / continuar",
                      f"↑ / ↓  filósofos ({self.n})", "R  reiniciar    Esc  sair"]:
            self.texto(linha, (x0, y), "txt", SUAVE)
            y += 24

    def desenhar(self):
        t = self.tela
        r = self.sim.retrato()
        travado = r.deadlock is not None
        t.fill(FUNDO)
        self.texto("O Jantar dos Filósofos", (40, 28), "titulo")
        self.texto(f"{ESTRATEGIAS[self.estrategia].nome} · {self.n} filósofos", (40, 66), "txt", SUAVE)
        self.desenhar_mesa(travado)
        self.desenhar_painel(r)
        if travado:
            ciclo = r.deadlock + [r.deadlock[0]]
            caixa = pygame.Rect(40, ALTURA - 112, 760, 84)
            pygame.draw.rect(t, VERMELHO, caixa, border_radius=16)
            self.texto("DEADLOCK", (64, ALTURA - 104), "grande", FUNDO)
            self.texto("ciclo de espera: " + " → ".join(f"P{i}" for i in ciclo), (64, ALTURA - 56), "txtb", FUNDO)
        elif self.sim.mesa.forcando:
            self.texto("forçando: todos pegam o 1º garfo juntos...", (40, ALTURA - 60), "txtb", AMARELO)
        if self.pausado:
            self.texto("PAUSADO", (430, 60), "h", AMARELO, centro=True)

    # ------------------------------------------------------------------ laço
    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            return False
        if k == pygame.K_d:
            self.sim.forcar_deadlock()
        elif k == pygame.K_SPACE:
            self.pausado = not self.pausado
            self.sim.pausar(self.pausado)
        elif k == pygame.K_UP and self.n < 10:
            self.n += 1
            self.reiniciar()
        elif k == pygame.K_DOWN and self.n > 2:
            self.n -= 1
            self.reiniciar()
        elif k == pygame.K_r:
            self.reiniciar()
        return True

    def rodar(self, captura: str | None = None, apos: float = 3.0, forcar_em: float | None = None):
        inicio = time.monotonic()
        forcou = False
        try:
            while True:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and not self.tecla(ev)):
                        return
                decorrido = time.monotonic() - inicio
                if forcar_em is not None and not forcou and decorrido >= forcar_em:
                    self.sim.forcar_deadlock()
                    forcou = True
                self.desenhar()
                pygame.display.flip()
                if captura and decorrido >= apos:
                    pygame.image.save(self.tela, captura)
                    return
                self.relogio.tick(60)
        finally:
            self.sim.parar(timeout=0.5)
            pygame.quit()
