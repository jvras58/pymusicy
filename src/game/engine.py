import pygame
import cv2
import time
import math
import numpy as np
import os
from src.audio.synthesizer import Sintetizador
from src.vision.tracker import HandTracker
from src.utils.data_loader import load_chords
from src.utils.paths import get_assets_path
from src.utils.config import (
    FAIL_MODE_ENABLED,
    PENALTY_TIME_SECONDS,
    FAIL_COOLDOWN_SECONDS,
    MIN_CHORD_DURATION,
)


class MusicGame:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chord Hero AI")
        self.clock = pygame.time.Clock()

        self.synth = Sintetizador()
        self.tracker = HandTracker()
        self.cap = cv2.VideoCapture(0)

        # Carregar dados
        self.dados_chords = load_chords()

        # Preparar áudio
        self.carregar_musica()
        self.pre_carregar_acordes()

        # Variáveis de Estado
        self.running = True
        self.start_time = time.time()
        self.score = 0
        self.ultimo_acorde_index = -1
        self.acorde_atual = None
        self.feedback_visual = []  # Lista de efeitos visuais

        # Sistema de Input
        self.was_pinched = False

        # Sistema de Penalidade (FAIL Mode)
        self.acorde_tocado = False  # Se o jogador tocou o acorde atual
        self.fail_mode = False  # Se está no modo de penalidade
        self.fail_start_time = 0  # Quando começou a penalidade
        self.pause_position = 0  # Posição da música quando pausou
        self.last_fail_end_time = 0  # Quando terminou o último FAIL (para cooldown)

    def carregar_musica(self):
        musica_path = os.path.join(get_assets_path(), "musica.mp3")
        if os.path.exists(musica_path):
            pygame.mixer.music.load(musica_path)
            pygame.mixer.music.set_volume(0.4)  # Música de fundo mais baixa
            pygame.mixer.music.play()
            self.usando_musica_real = True
            print("Música carregada.")
        else:
            print(
                f"Aviso: {musica_path} não encontrada. Rodando apenas com clock interno."
            )
            self.usando_musica_real = False
            self.start_time = time.time()

    def pre_carregar_acordes(self):
        print("Sintetizando acordes...")
        # Cria os sons antes do jogo começar para não travar
        unique_chords = set(d["chord_majmin"] for d in self.dados_chords)
        for chord in unique_chords:
            self.synth.gerar_acorde(chord)
        print("Acordes prontos!")

    def get_music_time(self):
        if self.usando_musica_real:
            # get_pos retorna milissegundos
            return pygame.mixer.music.get_pos() / 1000.0
        else:
            return time.time() - self.start_time

    def get_acorde_atual(self, music_time):
        # Busca linear simples (pode ser otimizado para busca binária)
        for i, dado in enumerate(self.dados_chords):
            if dado["start"] <= music_time <= dado["end"]:
                return i, dado
        return -1, None

    def draw_ui(self, frame_cv, music_time, chord_data, is_pinching, pinch_pos):
        # Converter câmera para Pygame
        frame_cv = np.rot90(frame_cv)
        frame_cv = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
        frame_surf = pygame.surfarray.make_surface(frame_cv)
        frame_surf = pygame.transform.scale(frame_surf, (self.WIDTH, self.HEIGHT))

        # Filtro escuro para UI brilhar
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(100)
        overlay.fill((20, 20, 40))

        self.screen.blit(frame_surf, (0, 0))
        self.screen.blit(overlay, (0, 0))

        # Fontes
        font_big = pygame.font.SysFont("Arial", 80, bold=True)
        font_small = pygame.font.SysFont("Arial", 30)

        # --- VISUALIZAÇÃO DO ACORDE ---
        if chord_data:
            nome_acorde = chord_data["chord_simple_pop"]  # Ex: Am, G, C
            duracao_total = chord_data["end"] - chord_data["start"]
            progresso = (music_time - chord_data["start"]) / duracao_total

            # Centro da tela
            cx, cy = self.WIDTH // 2, self.HEIGHT // 2

            # Círculo de ritmo (pulsa com o tempo)
            raio_base = 150
            raio_pulso = raio_base + (math.sin(time.time() * 10) * 5)

            cor = (0, 200, 255)  # Azul Neon
            if is_pinching:
                cor = (0, 255, 100)  # Verde se estiver tocando
                raio_pulso += 20

            pygame.draw.circle(self.screen, cor, (cx, cy), int(raio_pulso), 5)

            # Arco de progresso do acorde (círculo externo que preenche conforme o tempo)
            rect_arc = pygame.Rect(cx - 180, cy - 180, 360, 360)
            # Pygame desenha arco em radianos (sentido anti-horário, começando do topo)
            angulo_inicio = math.pi / 2  # Começa no topo (90 graus)
            angulo_fim = angulo_inicio - (
                2 * math.pi * progresso
            )  # Preenche no sentido horário

            # Desenha o arco de progresso
            if progresso > 0.01:  # Evita desenhar arco muito pequeno
                pygame.draw.arc(
                    self.screen, cor, rect_arc, angulo_fim, angulo_inicio, 8
                )

            # Círculo de fundo do arco (cinza)
            pygame.draw.circle(self.screen, (60, 60, 80), (cx, cy), 180, 3)

            # Barra de progresso inferior (mantida como indicador secundário)
            pygame.draw.rect(self.screen, (50, 50, 50), (cx - 200, cy + 200, 400, 20))
            pygame.draw.rect(
                self.screen, cor, (cx - 200, cy + 200, 400 * progresso, 20)
            )

            # Texto do Acorde
            text_surf = font_big.render(nome_acorde, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(cx, cy))
            self.screen.blit(text_surf, text_rect)

            text_hint = font_small.render("PINCE PARA TOCAR", True, (200, 200, 200))
            self.screen.blit(text_hint, (cx - text_hint.get_width() // 2, cy + 80))

        else:
            text_wait = font_small.render("Aguardando música...", True, (255, 255, 255))
            self.screen.blit(text_wait, (20, 20))

        # Efeitos visuais (Partículas)
        for p in self.feedback_visual[:]:
            p["r"] += 2
            p["alpha"] -= 5
            if p["alpha"] <= 0:
                self.feedback_visual.remove(p)
            else:
                s = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["cor"], p["alpha"]), (p["r"], p["r"]), p["r"])
                self.screen.blit(s, (p["x"] - p["r"], p["y"] - p["r"]))

    def run(self):
        while self.running:
            # 1. Input Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # 2. Visão Computacional
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame, is_pinching, pinch_pos = self.tracker.process(frame)

            # 3. Lógica do Jogo

            # Verificar se está em modo FAIL
            if self.fail_mode:
                tempo_na_penalidade = time.time() - self.fail_start_time
                if tempo_na_penalidade >= PENALTY_TIME_SECONDS:
                    # Sair do modo FAIL e retomar música
                    self.fail_mode = False
                    self.last_fail_end_time = time.time()  # Marcar quando saiu do FAIL
                    pygame.mixer.music.unpause()
                    self.acorde_tocado = True  # Marcar como tocado para não dar FAIL imediato no acorde atual
                else:
                    # Ainda em penalidade - desenhar tela de erro e continuar loop
                    self._draw_fail_screen(frame, tempo_na_penalidade)
                    pygame.display.flip()
                    self.clock.tick(30)
                    continue  # Pula o resto do loop

            music_time = self.get_music_time()
            idx, chord_data = self.get_acorde_atual(music_time)

            # Detectar mudança de acorde (o acorde anterior terminou)
            if idx != self.ultimo_acorde_index:
                # Verifica se havia um acorde anterior e se NÃO foi tocado
                if self.ultimo_acorde_index >= 0 and not self.acorde_tocado:
                    # Verificar se está em cooldown (acabou de sair de um FAIL)
                    tempo_desde_ultimo_fail = time.time() - self.last_fail_end_time
                    em_cooldown = tempo_desde_ultimo_fail < FAIL_COOLDOWN_SECONDS

                    # Verificar se o acorde anterior era longo o suficiente para contar
                    acorde_anterior = (
                        self.dados_chords[self.ultimo_acorde_index]
                        if self.ultimo_acorde_index < len(self.dados_chords)
                        else None
                    )
                    duracao_acorde = (
                        (acorde_anterior["end"] - acorde_anterior["start"])
                        if acorde_anterior
                        else 0
                    )
                    acorde_muito_curto = duracao_acorde < MIN_CHORD_DURATION

                    if FAIL_MODE_ENABLED and not em_cooldown and not acorde_muito_curto:
                        # ENTRAR NO MODO FAIL!
                        self._entrar_fail_mode()
                        self.ultimo_acorde_index = idx
                        continue  # Pula o resto do loop

                # Reset para novo acorde
                self.acorde_tocado = False
                self.ultimo_acorde_index = idx

            # Lógica de "Tocar" o acorde
            # Trigger: Se pinçou AGORA e não estava pinçando antes
            trigger = is_pinching and not self.was_pinched

            if trigger and chord_data:
                # TOCA O ACORDE!
                self.acorde_tocado = True  # Marca que tocou este acorde
                nome_completo = chord_data["chord_majmin"]
                som = self.synth.gerar_acorde(nome_completo)
                if som:
                    som.set_volume(1.0)  # Volume alto para destacar
                    som.play()

                # Feedback Visual
                self.feedback_visual.append(
                    {
                        "x": pinch_pos[0]
                        * self.WIDTH
                        // frame.shape[1],  # Mapear coord
                        "y": pinch_pos[1] * self.HEIGHT // frame.shape[0],
                        "r": 20,
                        "alpha": 255,
                        "cor": (0, 255, 100),
                    }
                )
                self.score += 100

            self.was_pinched = is_pinching

            # Reiniciar música se acabar (loop para teste)
            if (
                not pygame.mixer.music.get_busy()
                and self.usando_musica_real
                and music_time > 1
            ):
                # Reinicia lógica se necessário ou encerra
                pass

            # 4. Renderizar
            self.draw_ui(frame, music_time, chord_data, is_pinching, pinch_pos)
            pygame.display.flip()
            self.clock.tick(30)

        self.cap.release()
        pygame.quit()

    def _entrar_fail_mode(self):
        """Entra no modo de penalidade quando o jogador não toca o acorde"""
        self.fail_mode = True
        self.fail_start_time = time.time()

        # Pausar a música
        pygame.mixer.music.pause()

        # Tocar som de erro
        self.synth.tocar_som_erro()

        print("FAIL! Acorde não tocado!")

    def _draw_fail_screen(self, frame_cv, tempo_na_penalidade):
        """Desenha a tela de penalidade vermelha"""
        # Converter câmera para Pygame
        frame_cv = np.rot90(frame_cv)
        frame_cv = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
        frame_surf = pygame.surfarray.make_surface(frame_cv)
        frame_surf = pygame.transform.scale(frame_surf, (self.WIDTH, self.HEIGHT))

        # Overlay vermelho semi-transparente
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        # Pulsar o vermelho para efeito dramático
        intensidade = int(180 + 40 * math.sin(time.time() * 8))
        overlay.set_alpha(intensidade)
        overlay.fill((200, 0, 0))

        self.screen.blit(frame_surf, (0, 0))
        self.screen.blit(overlay, (0, 0))

        # Fontes
        font_big = pygame.font.SysFont("Arial", 100, bold=True)
        font_medium = pygame.font.SysFont("Arial", 40)
        font_small = pygame.font.SysFont("Arial", 30)

        cx, cy = self.WIDTH // 2, self.HEIGHT // 2

        # Texto "ERROU!"
        text_erro = font_big.render("ERROU!", True, (255, 255, 255))
        text_rect = text_erro.get_rect(center=(cx, cy - 50))

        # Sombra do texto
        text_sombra = font_big.render("ERROU!", True, (100, 0, 0))
        self.screen.blit(text_sombra, (text_rect.x + 4, text_rect.y + 4))
        self.screen.blit(text_erro, text_rect)

        # Barra de progresso da penalidade
        tempo_restante = PENALTY_TIME_SECONDS - tempo_na_penalidade
        progresso = tempo_na_penalidade / PENALTY_TIME_SECONDS

        bar_width = 400
        bar_height = 30
        bar_x = cx - bar_width // 2
        bar_y = cy + 50

        # Fundo da barra
        pygame.draw.rect(
            self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height)
        )
        # Progresso
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (bar_x, bar_y, int(bar_width * progresso), bar_height),
        )
        # Borda
        pygame.draw.rect(
            self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 3
        )

        # Texto do tempo restante
        text_tempo = font_medium.render(
            f"Aguarde {tempo_restante:.1f}s", True, (255, 255, 255)
        )
        text_rect_tempo = text_tempo.get_rect(center=(cx, bar_y + bar_height + 40))
        self.screen.blit(text_tempo, text_rect_tempo)

        # Mensagem motivacional
        text_msg = font_small.render("Não perca o ritmo!", True, (255, 200, 200))
        text_rect_msg = text_msg.get_rect(center=(cx, cy + 150))
        self.screen.blit(text_msg, text_rect_msg)
