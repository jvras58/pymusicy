"""
Engine principal do jogo de gestos sincronizados com acordes.

O jogador deve fazer o gesto correto para cada acorde.
A música pausa no início de cada acorde e só avança quando o gesto é aceito.
"""

import pygame
import pygame.freetype
import cv2
import time
import math
import numpy as np
import os
from enum import Enum
from src.audio.synthesizer import Sintetizador, Timbre
from src.vision.tracker import HandTracker
from src.vision.gesture_recognizer import GestureRecognizer, GestureType, GESTURE_EMOJI, GESTURE_NAMES
from src.utils.data_loader import load_chords
from src.utils.paths import get_assets_path
from src.utils.config import (
    GESTURE_HOLD_TIME,
    SHOW_GESTURE_DEBUG,
    FAIL_MODE_ENABLED,
    PENALTY_TIME_SECONDS,
)


class GameState(Enum):
    """Estados do jogo."""
    INTRO = "intro"                      # Tela inicial
    WAITING_FOR_GESTURE = "waiting"      # Aguardando gesto correto
    GESTURE_CORRECT = "correct"          # Gesto correto, tocando acorde
    PLAYING = "playing"                  # Música tocando até próximo acorde
    FAIL = "fail"                        # Erro! Não fez o gesto a tempo
    FINISHED = "finished"                # Música terminou


class MusicGame:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chord Hero AI - Gesture Game")
        self.clock = pygame.time.Clock()

        self.synth = Sintetizador()
        self.tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.cap = cv2.VideoCapture(0)

        # Carregar dados
        self.dados_chords = load_chords()

        # Preparar áudio
        self.carregar_musica()
        self.pre_carregar_acordes()

        # Estado do jogo
        self.running = True
        self.game_state = GameState.INTRO
        self.score = 0
        self.acertos = 0
        self.total_acordes = len(self.dados_chords)
        
        # Controle de acordes
        self.acorde_index = 0
        self.acorde_atual = None
        
        # Controle de gestos
        self.gesture_start_time = 0       # Quando começou a fazer o gesto correto
        self.gesture_hold_duration = 0    # Quanto tempo está segurando o gesto
        self.last_correct_gesture = False
        
        # Controle de transição
        self.transition_start_time = 0
        self.TRANSITION_DURATION = 0.5    # Tempo mostrando "CORRETO!"
        
        # Controle de música
        self.music_paused = True
        self.pause_position = 0
        self.waiting_start_time = 0      # Quando começou a esperar o gesto
        
        # Controle de FAIL
        self.fail_mode_enabled = FAIL_MODE_ENABLED  # Pode ser toggled com M
        self.fail_start_time = 0
        self.erros = 0
        
        # Controle de timbres (T para trocar)
        self.timbres = list(Timbre)
        self.timbre_index = 0
        
        # Feedback visual
        self.feedback_visual = []
        
        # Fontes
        self.font_big = None
        self.font_medium = None
        self.font_small = None
        self.emoji_font = None  # Fonte especial para emojis

    def carregar_musica(self):
        musica_path = os.path.join(get_assets_path(), "musica.mp3")
        if os.path.exists(musica_path):
            pygame.mixer.music.load(musica_path)
            pygame.mixer.music.set_volume(0.5)
            self.usando_musica_real = True
            print("Música carregada.")
        else:
            print(f"Aviso: {musica_path} não encontrada.")
            self.usando_musica_real = False

    def pre_carregar_acordes(self):
        print("Sintetizando acordes...")
        unique_chords = set(d["chord_majmin"] for d in self.dados_chords)
        for chord in unique_chords:
            self.synth.gerar_acorde(chord)
        print(f"Acordes prontos! ({len(unique_chords)} acordes únicos)")

    def iniciar_jogo(self):
        """Inicia o jogo no primeiro acorde."""
        self.acorde_index = 0
        self.score = 0
        self.acertos = 0
        self.erros = 0
        
        if self.acorde_index < len(self.dados_chords):
            self.acorde_atual = self.dados_chords[self.acorde_index]
            self.game_state = GameState.WAITING_FOR_GESTURE
            self.waiting_start_time = time.time()  # Marcar início da espera
            
            # Iniciar música pausada no início
            if self.usando_musica_real:
                pygame.mixer.music.play()
                pygame.mixer.music.pause()
                self.music_paused = True
            
            print(f"Aguardando gesto para: {self.acorde_atual['chord_simple_pop']}")

    def avancar_acorde(self):
        """Avança para o próximo acorde."""
        self.acorde_index += 1
        
        if self.acorde_index >= len(self.dados_chords):
            # Fim da música
            self.game_state = GameState.FINISHED
            if self.usando_musica_real:
                pygame.mixer.music.stop()
            print("Fim do jogo!")
            return
        
        self.acorde_atual = self.dados_chords[self.acorde_index]
        self.game_state = GameState.WAITING_FOR_GESTURE
        self.waiting_start_time = time.time()  # Marcar início da espera
        
        # Pausar música no início do novo acorde
        if self.usando_musica_real:
            pygame.mixer.music.pause()
            self.music_paused = True
        
        # Reset do estado de gesto
        self.gesture_start_time = 0
        self.gesture_hold_duration = 0
        self.last_correct_gesture = False
        
        print(f"Próximo acorde: {self.acorde_atual['chord_simple_pop']}")

    def tocar_acorde_e_avancar(self):
        """Toca o som do acorde e prepara para tocar a música."""
        if self.acorde_atual is None:
            return
        
        # Tocar som do acorde
        nome_completo = self.acorde_atual["chord_majmin"]
        som = self.synth.gerar_acorde(nome_completo)
        if som:
            som.set_volume(1.0)
            som.play()
        
        # Atualizar score
        self.score += 100
        self.acertos += 1
        
        # Mostrar feedback de acerto
        self.game_state = GameState.GESTURE_CORRECT
        self.transition_start_time = time.time()
        
        # Despausar música
        if self.usando_musica_real and self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False

    def get_music_time(self):
        """Retorna o tempo atual da música em segundos."""
        if self.usando_musica_real:
            return pygame.mixer.music.get_pos() / 1000.0
        else:
            return 0

    def update_game_logic(self, landmarks):
        """Atualiza a lógica do jogo baseada no estado atual."""
        
        if self.game_state == GameState.INTRO:
            # Aguardando início
            return
        
        elif self.game_state == GameState.WAITING_FOR_GESTURE:
            if self.acorde_atual is None:
                return
            
            # Calcular tempo limite baseado na duração do acorde
            chord_duration = self.acorde_atual["end"] - self.acorde_atual["start"]
            time_waiting = time.time() - self.waiting_start_time
            
            # Verificar timeout (FAIL MODE)
            if self.fail_mode_enabled and time_waiting >= chord_duration:
                self._entrar_fail_mode()
                return
            
            # Verificar gesto
            chord_name = self.acorde_atual["chord_simple_pop"]
            is_correct, confidence, detected_gesture = self.gesture_recognizer.is_gesture_correct(
                landmarks, chord_name
            )
            
            if is_correct:
                if not self.last_correct_gesture:
                    # Começou a fazer o gesto correto agora
                    self.gesture_start_time = time.time()
                    self.last_correct_gesture = True
                
                # Calcular quanto tempo está segurando
                self.gesture_hold_duration = time.time() - self.gesture_start_time
                
                # Se segurou tempo suficiente, aceitar
                if self.gesture_hold_duration >= GESTURE_HOLD_TIME:
                    self.tocar_acorde_e_avancar()
            else:
                # Gesto incorreto, resetar
                self.last_correct_gesture = False
                self.gesture_start_time = 0
                self.gesture_hold_duration = 0
        
        elif self.game_state == GameState.GESTURE_CORRECT:
            # Mostrando feedback de acerto
            elapsed = time.time() - self.transition_start_time
            
            if elapsed >= self.TRANSITION_DURATION:
                # Estado de transição: tocar música até o fim do acorde
                self.game_state = GameState.PLAYING
        
        elif self.game_state == GameState.PLAYING:
            # Música tocando, verificar se chegou no próximo acorde
            if self.acorde_atual is None:
                return
            
            music_time = self.get_music_time()
            
            # Verificar se passou do fim do acorde atual
            if music_time >= self.acorde_atual["end"]:
                self.avancar_acorde()
        
        elif self.game_state == GameState.FAIL:
            # Modo FAIL - aguardar tempo de penalidade
            tempo_na_penalidade = time.time() - self.fail_start_time
            
            if tempo_na_penalidade >= PENALTY_TIME_SECONDS:
                # Sair do FAIL e avançar para próximo acorde
                self.avancar_acorde()
        
        elif self.game_state == GameState.FINISHED:
            # Jogo terminou
            pass
    
    def _entrar_fail_mode(self):
        """Entra no modo de penalidade quando o jogador não faz o gesto a tempo."""
        self.game_state = GameState.FAIL
        self.fail_start_time = time.time()
        self.erros += 1
        
        # Tocar som de erro
        self.synth.tocar_som_erro()
        
        print(f"FAIL! Não fez o gesto a tempo!")

    def draw_ui(self, frame_cv, landmarks):
        """Desenha a interface do jogo."""
        # Preparar fontes (lazy loading)
        if self.font_big is None:
            self.font_big = pygame.font.SysFont("Arial", 80, bold=True)
            self.font_medium = pygame.font.SysFont("Arial", 40, bold=True)
            self.font_small = pygame.font.SysFont("Arial", 28)
        
        # Converter câmera para Pygame
        frame_cv = np.rot90(frame_cv)
        frame_cv = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
        frame_surf = pygame.surfarray.make_surface(frame_cv)
        frame_surf = pygame.transform.scale(frame_surf, (self.WIDTH, self.HEIGHT))

        # Overlay escuro
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(120)
        overlay.fill((20, 20, 40))

        self.screen.blit(frame_surf, (0, 0))
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.WIDTH // 2, self.HEIGHT // 2

        if self.game_state == GameState.INTRO:
            self._draw_intro_screen(cx, cy)
        
        elif self.game_state == GameState.WAITING_FOR_GESTURE:
            self._draw_waiting_screen(cx, cy, landmarks)
        
        elif self.game_state == GameState.GESTURE_CORRECT:
            self._draw_correct_screen(cx, cy)
        
        elif self.game_state == GameState.PLAYING:
            self._draw_playing_screen(cx, cy)
        
        elif self.game_state == GameState.FAIL:
            self._draw_fail_screen(cx, cy)
        
        elif self.game_state == GameState.FINISHED:
            self._draw_finished_screen(cx, cy)
        
        # HUD sempre visível (exceto intro)
        if self.game_state != GameState.INTRO:
            self._draw_hud()
        
        # Efeitos visuais (partículas)
        self._draw_particles()

    def _draw_intro_screen(self, cx, cy):
        """Tela inicial do jogo."""
        # Inicializar emoji_font se necessário
        if self.emoji_font is None:
            try:
                self.emoji_font = pygame.freetype.SysFont("Segoe UI Emoji", 60)
            except:
                self.emoji_font = pygame.freetype.SysFont("Arial", 60)
        
        # Título
        title = self.font_big.render("CHORD HERO AI", True, (0, 200, 255))
        title_rect = title.get_rect(center=(cx, cy - 120))
        self.screen.blit(title, title_rect)
        
        # Subtítulo
        subtitle = self.font_medium.render("Jogo de Gestos Musicais", True, (255, 255, 255))
        subtitle_rect = subtitle.get_rect(center=(cx, cy - 50))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instruções
        instr1 = self.font_small.render("Faça o gesto correto para cada acorde!", True, (200, 200, 200))
        instr1_rect = instr1.get_rect(center=(cx, cy + 10))
        self.screen.blit(instr1, instr1_rect)
        
        # Gestos disponíveis - usando emojis renderizados com freetype
        gestos_label = self.font_small.render("Gestos disponíveis:", True, (150, 200, 255))
        gestos_label_rect = gestos_label.get_rect(center=(cx, cy + 50))
        self.screen.blit(gestos_label, gestos_label_rect)
        
        # Desenhar emojis dos gestos em linha
        emojis = ["✋", "✊", "✌", "👍", "👆"]  # ✌ sem variation selector para centralizar melhor
        nomes = ["Mão", "Punho", "Paz", "Joinha", "Apontar"]
        icon_spacing = 130
        start_x = cx - (len(emojis) - 1) * icon_spacing // 2
        icon_y = cy + 100
        
        for i, (emoji, nome) in enumerate(zip(emojis, nomes)):
            icon_x = start_x + i * icon_spacing
            
            # Emoji
            emoji_surf, emoji_rect = self.emoji_font.render(emoji, (150, 200, 255))
            emoji_rect.center = (icon_x, icon_y)
            self.screen.blit(emoji_surf, emoji_rect)
            
            # Nome abaixo
            nome_text = self.font_small.render(nome, True, (120, 160, 200))
            nome_rect = nome_text.get_rect(center=(icon_x, icon_y + 45))
            self.screen.blit(nome_text, nome_rect)
        
        # Botão de start (pulsando)
        pulse = math.sin(time.time() * 4) * 10
        start_text = self.font_medium.render("PRESSIONE ESPAÇO PARA INICIAR", True, (0, 255, 100))
        start_rect = start_text.get_rect(center=(cx, cy + 200 + pulse))
        self.screen.blit(start_text, start_rect)

    def _draw_waiting_screen(self, cx, cy, landmarks):
        """Tela de espera pelo gesto correto."""
        if self.acorde_atual is None:
            return
        
        chord_name = self.acorde_atual["chord_simple_pop"]
        expected_gesture = self.gesture_recognizer.get_expected_gesture(chord_name)
        expected_emoji = self.gesture_recognizer.get_gesture_emoji(expected_gesture)
        expected_name = self.gesture_recognizer.get_gesture_name(expected_gesture)
        
        # Detectar gesto atual
        detected_gesture, confidence = self.gesture_recognizer.detect_gesture(landmarks)
        detected_emoji = self.gesture_recognizer.get_gesture_emoji(detected_gesture)
        
        # Nome do acorde
        chord_text = self.font_big.render(chord_name, True, (255, 255, 255))
        chord_rect = chord_text.get_rect(center=(cx, cy - 150))
        self.screen.blit(chord_text, chord_rect)
        
        # Instrução
        instr = self.font_small.render("Faça o gesto:", True, (200, 200, 200))
        instr_rect = instr.get_rect(center=(cx, cy - 80))
        self.screen.blit(instr, instr_rect)
        
        # Círculo do gesto esperado
        raio = 100
        centro_y = cy + 30  # Centro Y do círculo
        cor_circulo = (0, 200, 255)  # Azul
        
        # Se está fazendo o gesto correto, mudar cor
        if self.last_correct_gesture:
            progress = min(self.gesture_hold_duration / GESTURE_HOLD_TIME, 1.0)
            cor_circulo = (
                int(0 + 0 * progress),
                int(200 + 55 * progress),
                int(255 - 155 * progress)
            )  # Transição para verde
            
            # Arco de progresso (centralizado, um pouco maior que o círculo)
            raio_arco = raio + 15
            rect_arc = pygame.Rect(
                cx - raio_arco, 
                centro_y - raio_arco, 
                raio_arco * 2, 
                raio_arco * 2
            )
            angulo_inicio = math.pi / 2
            angulo_fim = angulo_inicio - (2 * math.pi * progress)
            pygame.draw.arc(self.screen, (0, 255, 100), rect_arc, angulo_fim, angulo_inicio, 8)
        
        pygame.draw.circle(self.screen, cor_circulo, (cx, centro_y), raio, 5)
        
        # Emoji do gesto esperado (grande, no centro)
        # Usar freetype para melhor suporte a Unicode/emojis
        if self.emoji_font is None:
            try:
                # Tentar carregar fonte com suporte a emoji
                self.emoji_font = pygame.freetype.SysFont("Segoe UI Emoji", 60)
            except:
                self.emoji_font = pygame.freetype.SysFont("Arial", 60)
        
        emoji_surface, emoji_rect = self.emoji_font.render(expected_emoji, (255, 255, 255))
        emoji_rect.center = (cx, cy + 30)
        self.screen.blit(emoji_surface, emoji_rect)
        
        # Nome do gesto esperado
        gesto_name = self.font_small.render(expected_name, True, (200, 200, 200))
        gesto_rect = gesto_name.get_rect(center=(cx, cy + 150))
        self.screen.blit(gesto_name, gesto_rect)
        
        # Mostrar gesto detectado (canto inferior direito, layout vertical)
        if landmarks is not None and self.emoji_font:
            # Posição base (canto inferior direito)
            base_x = self.WIDTH - 120
            base_y = self.HEIGHT - 120
            
            # Emoji do gesto detectado (grande, em cima)
            emoji_surf, emoji_rect = self.emoji_font.render(detected_emoji, (255, 255, 255))
            emoji_rect.center = (base_x, base_y)
            self.screen.blit(emoji_surf, emoji_rect)
            
            # Nome do gesto (abaixo do emoji)
            detected_name = self.gesture_recognizer.get_gesture_name(detected_gesture)
            name_text = self.font_small.render(detected_name, True, (180, 180, 180))
            name_rect = name_text.get_rect(center=(base_x, base_y + 45))
            self.screen.blit(name_text, name_rect)
            
            # Barra de confiança (abaixo do nome)
            bar_width = 100
            bar_height = 8
            bar_x = base_x - bar_width // 2
            bar_y = base_y + 70
            
            # Fundo da barra
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
            # Preenchimento
            fill_width = int(bar_width * confidence)
            if fill_width > 0:
                pygame.draw.rect(self.screen, (0, 200, 255), (bar_x, bar_y, fill_width, bar_height), border_radius=4)
        
        # Barra de tempo restante (se FAIL mode ativo)
        if self.fail_mode_enabled and self.acorde_atual:
            chord_duration = self.acorde_atual["end"] - self.acorde_atual["start"]
            time_waiting = time.time() - self.waiting_start_time
            tempo_restante = chord_duration - time_waiting
            progresso_tempo = time_waiting / chord_duration
            
            # Barra de tempo no topo
            bar_width = 600
            bar_height = 12
            bar_x = cx - bar_width // 2
            bar_y = 660
            
            # Cor muda de verde para vermelho conforme o tempo passa
            if progresso_tempo < 0.5:
                cor_barra = (100, 255, 100)  # Verde
            elif progresso_tempo < 0.8:
                cor_barra = (255, 200, 0)  # Amarelo
            else:
                cor_barra = (255, 100, 100)  # Vermelho
            
            # Fundo da barra
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
            # Preenchimento (diminui conforme tempo passa)
            fill_width = int(bar_width * (1 - progresso_tempo))
            if fill_width > 0:
                pygame.draw.rect(self.screen, cor_barra, (bar_x, bar_y, fill_width, bar_height), border_radius=3)
            
            # Texto do tempo
            tempo_text = self.font_small.render(f"Tempo: {tempo_restante:.1f}s", True, cor_barra)
            tempo_rect = tempo_text.get_rect(center=(cx, bar_y - 20))
            self.screen.blit(tempo_text, tempo_rect)
        
        # Debug de gestos
        if SHOW_GESTURE_DEBUG and landmarks is not None:
            self._draw_gesture_debug(landmarks, detected_gesture, confidence)

    def _draw_correct_screen(self, cx, cy):
        """Tela de acerto (breve transição)."""
        # Efeito de flash verde
        flash = pygame.Surface((self.WIDTH, self.HEIGHT))
        elapsed = time.time() - self.transition_start_time
        alpha = int(150 * (1 - elapsed / self.TRANSITION_DURATION))
        flash.set_alpha(max(0, alpha))
        flash.fill((0, 255, 100))
        self.screen.blit(flash, (0, 0))
        
        # Texto "CORRETO!"
        scale = 1 + 0.3 * math.sin(elapsed * 20)
        font_size = int(100 * scale)
        font_correct = pygame.font.SysFont("Arial", font_size, bold=True)
        correct_text = font_correct.render("CORRETO!", True, (255, 255, 255))
        correct_rect = correct_text.get_rect(center=(cx, cy))
        self.screen.blit(correct_text, correct_rect)
        
        # Adicionar partículas
        if len(self.feedback_visual) < 20:
            for _ in range(3):
                self.feedback_visual.append({
                    "x": cx + np.random.randint(-100, 100),
                    "y": cy + np.random.randint(-100, 100),
                    "r": 10,
                    "alpha": 255,
                    "cor": (0, 255, 100)
                })

    def _draw_playing_screen(self, cx, cy):
        """Tela durante a reprodução do trecho."""
        if self.acorde_atual is None:
            return
        
        chord_name = self.acorde_atual["chord_simple_pop"]
        
        # Mostrar acorde atual tocando
        playing_text = self.font_medium.render(f"♪ {chord_name} ♪", True, (0, 255, 100))
        playing_rect = playing_text.get_rect(center=(cx, cy - 50))
        self.screen.blit(playing_text, playing_rect)
        
        # Barra de progresso do trecho
        music_time = self.get_music_time()
        start = self.acorde_atual["start"]
        end = self.acorde_atual["end"]
        duracao = end - start
        
        if duracao > 0:
            progress = min((music_time - start) / duracao, 1.0)
            progress = max(0, progress)
            
            bar_width = 400
            bar_height = 20
            bar_x = cx - bar_width // 2
            bar_y = cy + 50
            
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, (0, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Próximo acorde (preview)
        if self.acorde_index + 1 < len(self.dados_chords):
            next_chord = self.dados_chords[self.acorde_index + 1]
            next_name = next_chord["chord_simple_pop"]
            next_gesture = self.gesture_recognizer.get_expected_gesture(next_name)
            next_emoji = self.gesture_recognizer.get_gesture_emoji(next_gesture)
            
            # Label "Próximo:"
            next_label = self.font_small.render(f"Próximo: {next_name}", True, (150, 150, 200))
            next_label_rect = next_label.get_rect(center=(cx - 30, cy + 120))
            self.screen.blit(next_label, next_label_rect)
            
            # Emoji do próximo gesto
            if self.emoji_font:
                next_emoji_surf, _ = self.emoji_font.render(next_emoji, (150, 150, 200))
                self.screen.blit(next_emoji_surf, (cx + 50, cy + 105))

    def _draw_fail_screen(self, cx, cy):
        """Tela de penalidade (FAIL)."""
        tempo_na_penalidade = time.time() - self.fail_start_time
        
        # Overlay vermelho pulsante
        pulse_intensity = int(150 + 50 * math.sin(time.time() * 8))
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(pulse_intensity)
        overlay.fill((200, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Texto "ERROU!" com sombra
        font_erro = pygame.font.SysFont("Arial", 100, bold=True)
        
        # Sombra
        sombra = font_erro.render("ERROU!", True, (100, 0, 0))
        sombra_rect = sombra.get_rect(center=(cx + 4, cy - 50 + 4))
        self.screen.blit(sombra, sombra_rect)
        
        # Texto principal
        erro_text = font_erro.render("ERROU!", True, (255, 255, 255))
        erro_rect = erro_text.get_rect(center=(cx, cy - 50))
        self.screen.blit(erro_text, erro_rect)
        
        # Mostrar qual gesto era esperado
        if self.acorde_atual and self.emoji_font:
            chord_name = self.acorde_atual["chord_simple_pop"]
            expected_gesture = self.gesture_recognizer.get_expected_gesture(chord_name)
            expected_emoji = self.gesture_recognizer.get_gesture_emoji(expected_gesture)
            expected_name = self.gesture_recognizer.get_gesture_name(expected_gesture)
            
            esperado_text = self.font_small.render(f"Esperado: {chord_name}", True, (255, 200, 200))
            esperado_rect = esperado_text.get_rect(center=(cx, cy + 30))
            self.screen.blit(esperado_text, esperado_rect)
            
            # Emoji do gesto esperado
            emoji_surf, emoji_rect = self.emoji_font.render(expected_emoji, (255, 200, 200))
            emoji_rect.center = (cx, cy + 80)
            self.screen.blit(emoji_surf, emoji_rect)
        
        # Barra de progresso da penalidade
        tempo_restante = PENALTY_TIME_SECONDS - tempo_na_penalidade
        progresso = tempo_na_penalidade / PENALTY_TIME_SECONDS
        
        bar_width = 400
        bar_height = 25
        bar_x = cx - bar_width // 2
        bar_y = cy + 140
        
        # Fundo da barra
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        # Progresso
        fill_width = int(bar_width * progresso)
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, fill_width, bar_height), border_radius=5)
        # Borda
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 3, border_radius=5)
        
        # Texto do tempo restante
        tempo_text = self.font_medium.render(f"Aguarde {tempo_restante:.1f}s", True, (255, 255, 255))
        tempo_rect = tempo_text.get_rect(center=(cx, bar_y + bar_height + 40))
        self.screen.blit(tempo_text, tempo_rect)

    def _draw_finished_screen(self, cx, cy):
        """Tela de fim de jogo."""
        # Título
        title = self.font_big.render("FIM!", True, (0, 255, 100))
        title_rect = title.get_rect(center=(cx, cy - 120))
        self.screen.blit(title, title_rect)
        
        # Score
        score_text = self.font_medium.render(f"Pontuação: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(cx, cy - 30))
        self.screen.blit(score_text, score_rect)
        
        # Acertos
        percent = (self.acertos / self.total_acordes * 100) if self.total_acordes > 0 else 0
        acertos_text = self.font_small.render(
            f"✓ Acertos: {self.acertos}/{self.total_acordes} ({percent:.0f}%)", 
            True, (100, 255, 100)
        )
        acertos_rect = acertos_text.get_rect(center=(cx, cy + 30))
        self.screen.blit(acertos_text, acertos_rect)
        
        # Erros
        if self.erros > 0:
            erros_text = self.font_small.render(
                f"✗ Erros: {self.erros}", 
                True, (255, 100, 100)
            )
            erros_rect = erros_text.get_rect(center=(cx, cy + 70))
            self.screen.blit(erros_text, erros_rect)
        
        # Replay
        replay_text = self.font_small.render("Pressione ESPAÇO para jogar novamente", True, (150, 200, 255))
        replay_rect = replay_text.get_rect(center=(cx, cy + 150))
        self.screen.blit(replay_text, replay_rect)

    def _draw_hud(self):
        """Desenha o HUD (score, progresso, configurações)."""
        # Score
        score_text = self.font_small.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # Progresso
        progress_text = self.font_small.render(
            f"Acorde: {self.acorde_index + 1}/{self.total_acordes}", 
            True, (200, 200, 200)
        )
        self.screen.blit(progress_text, (self.WIDTH - progress_text.get_width() - 20, 20))
        
        # Sidebar de configurações (canto superior esquerdo, abaixo do score)
        sidebar_y = 55
        
        # Timbre atual
        timbre_nome = self.timbres[self.timbre_index].value.upper()
        timbre_text = self.font_small.render(f"♪ {timbre_nome}", True, (100, 200, 255))
        self.screen.blit(timbre_text, (20, sidebar_y))
        
        # Fail Mode status
        if self.fail_mode_enabled:
            fail_text = self.font_small.render("⏱ FAIL: ON", True, (255, 100, 100))
        else:
            fail_text = self.font_small.render("⏱ FAIL: OFF", True, (100, 255, 100))
        self.screen.blit(fail_text, (20, sidebar_y + 28))
        
        # Dica de teclas (pequena)
        hint_font = pygame.font.SysFont("Arial", 16)
        hint_text = hint_font.render("T=Timbre  M=Fail", True, (100, 100, 120))
        self.screen.blit(hint_text, (20, sidebar_y + 56))

    def _draw_particles(self):
        """Desenha partículas de feedback."""
        for p in self.feedback_visual[:]:
            p["r"] += 2
            p["alpha"] -= 8
            if p["alpha"] <= 0:
                self.feedback_visual.remove(p)
            else:
                s = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["cor"], p["alpha"]), (p["r"], p["r"]), p["r"])
                self.screen.blit(s, (p["x"] - p["r"], p["y"] - p["r"]))

    def _draw_gesture_debug(self, landmarks, detected_gesture, confidence):
        """Desenha informações de debug dos gestos."""
        if landmarks is None:
            return
        
        # Mostrar landmarks
        debug_y = 100
        debug_text = self.font_small.render(
            f"Gesto: {detected_gesture.value} ({confidence:.2f})", 
            True, (255, 255, 0)
        )
        self.screen.blit(debug_text, (20, debug_y))

    def run(self):
        """Loop principal do jogo."""
        while self.running:
            # 1. Input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        if self.game_state == GameState.INTRO:
                            self.iniciar_jogo()
                        elif self.game_state == GameState.FINISHED:
                            self.game_state = GameState.INTRO
                    elif event.key == pygame.K_m:
                        # Toggle fail mode
                        self.fail_mode_enabled = not self.fail_mode_enabled
                        status = "ATIVADO" if self.fail_mode_enabled else "DESATIVADO"
                        print(f"Fail Mode: {status}")
                    elif event.key == pygame.K_t:
                        # Trocar timbre
                        self.timbre_index = (self.timbre_index + 1) % len(self.timbres)
                        novo_timbre = self.timbres[self.timbre_index]
                        self.synth.set_timbre(novo_timbre)
                        print(f"Timbre: {novo_timbre.value}")

            # 2. Captura de vídeo
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            
            # 3. Processamento de visão
            frame, is_pinching, pinch_pos, landmarks = self.tracker.process(frame)

            # 4. Lógica do jogo
            self.update_game_logic(landmarks)

            # 5. Renderização
            self.draw_ui(frame, landmarks)
            pygame.display.flip()
            self.clock.tick(30)

        self.cap.release()
        pygame.quit()

