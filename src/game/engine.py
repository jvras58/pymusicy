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
            music_time = self.get_music_time()
            idx, chord_data = self.get_acorde_atual(music_time)

            # Lógica de "Tocar" o acorde
            # Trigger: Se pinçou AGORA e não estava pinçando antes
            trigger = is_pinching and not self.was_pinched

            if trigger and chord_data:
                # TOCA O ACORDE!
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
