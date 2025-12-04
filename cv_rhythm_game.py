import cv2
import mediapipe as mp
import pygame
import numpy as np
import json
import math
import time
import os

# --- DADOS DE EXEMPLO (SEU JSON) ---
# Na prática, você carregaria isso de um arquivo .json externo
DADOS_CHORDS_PADRAO = [
    {"start": 0.0, "end": 2.0, "chord_majmin": "C:maj", "chord_simple_pop": "C"},
    {"start": 2.0, "end": 4.0, "chord_majmin": "G:maj", "chord_simple_pop": "G"},
    {"start": 4.0, "end": 6.0, "chord_majmin": "A:min", "chord_simple_pop": "Am"},
    {"start": 6.0, "end": 8.0, "chord_majmin": "F:maj", "chord_simple_pop": "F"},
]

# Tenta carregar dados reais se você salvar o JSON que enviou num arquivo
if os.path.exists("chords.json"):
    with open("chords.json", "r") as f:
        DADOS_CHORDS = json.load(f)
else:
    # Usa um loop básico se não tiver arquivo, ou usa o snippet que você mandou
    # Vou expandir o snippet que você mandou para ser usado como padrão se não houver arquivo
    DADOS_CHORDS = [
        {"start": 0.27, "end": 11.66, "chord_majmin": "G:maj", "chord_simple_pop": "G"},
        {
            "start": 11.66,
            "end": 16.46,
            "chord_majmin": "A:min",
            "chord_simple_pop": "Am",
        },
        {
            "start": 16.46,
            "end": 17.66,
            "chord_majmin": "C:maj",
            "chord_simple_pop": "C",
        },
        # Adicionei um loop final para teste
        {
            "start": 17.66,
            "end": 25.00,
            "chord_majmin": "D:maj",
            "chord_simple_pop": "D",
        },
    ]

# --- TEORIA MUSICAL E SINTETIZADOR ---
NOTAS_BASE = {
    "C": 261.63,
    "C#": 277.18,
    "Db": 277.18,
    "D": 293.66,
    "D#": 311.13,
    "Eb": 311.13,
    "E": 329.63,
    "F": 349.23,
    "F#": 369.99,
    "Gb": 369.99,
    "G": 392.00,
    "G#": 415.30,
    "Ab": 415.30,
    "A": 440.00,
    "A#": 466.16,
    "Bb": 466.16,
    "B": 493.88,
}

INTERVALOS = {
    "maj": [0, 4, 7],  # Tônica, Terça Maior, Quinta Justa
    "min": [0, 3, 7],  # Tônica, Terça Menor, Quinta Justa
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "7": [0, 4, 7, 10],
}


class Sintetizador:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.mixer.init()
        pygame.init()
        self.cache_acordes = {}

    def criar_onda(self, freq, duracao=1.0, volume=0.5):
        sample_rate = 44100
        n_samples = int(sample_rate * duracao)
        t = np.linspace(0, duracao, n_samples, False)

        # Síntese Aditiva para um som mais "piano elétrico" e menos "apito"
        # Fundamental + Harmônicos
        onda = 0.6 * np.sin(2 * np.pi * freq * t)
        onda += 0.3 * np.sin(2 * np.pi * freq * 2 * t)  # Oitava acima
        onda += 0.1 * np.sin(2 * np.pi * freq * 3 * t)  # Quinta da oitava

        # Envelope ADSR simples (Ataque rápido, Decay suave)
        envelope = np.exp(-3 * t)
        onda = onda * envelope * volume

        # Converter para 16-bit PCM
        onda = (onda * 32767).astype(np.int16)
        return np.column_stack((onda, onda))

    def gerar_acorde(self, nome_acorde_full):
        # Ex: "G:maj" ou "A:min"
        if nome_acorde_full in self.cache_acordes:
            return self.cache_acordes[nome_acorde_full]

        try:
            if ":" in nome_acorde_full:
                tonica, tipo = nome_acorde_full.split(":")
            else:
                tonica = nome_acorde_full
                tipo = "maj"

            freq_base = NOTAS_BASE.get(tonica, 261.63)
            intervalos = INTERVALOS.get(tipo, INTERVALOS["maj"])

            # Misturar as notas do acorde
            audio_final = None

            for semi_tons in intervalos:
                # Calcular frequência da nota do intervalo (f = f0 * 2^(n/12))
                freq_nota = freq_base * (2 ** (semi_tons / 12.0))
                onda_nota = self.criar_onda(freq_nota)

                if audio_final is None:
                    audio_final = onda_nota
                else:
                    audio_final = audio_final + onda_nota  # Soma as ondas

            # Normalizar para evitar distorção (clipping)
            max_val = np.max(np.abs(audio_final))
            if max_val > 0:
                audio_final = (audio_final / max_val * 32767).astype(np.int16)

            som = pygame.sndarray.make_sound(audio_final)
            self.cache_acordes[nome_acorde_full] = som
            return som
        except Exception as e:
            print(f"Erro ao gerar acorde {nome_acorde_full}: {e}")
            return None


# --- VISÃO COMPUTACIONAL ---
class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
        self.last_pinch_time = 0

    def process(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        pinched = False
        pos = (0, 0)

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img, hand_lms, self.mp_hands.HAND_CONNECTIONS
                )

                h, w, c = img.shape
                # Pontas dos dedos: 4 (Polegar), 8 (Indicador)
                x4, y4 = (
                    int(hand_lms.landmark[4].x * w),
                    int(hand_lms.landmark[4].y * h),
                )
                x8, y8 = (
                    int(hand_lms.landmark[8].x * w),
                    int(hand_lms.landmark[8].y * h),
                )

                dist = math.hypot(x8 - x4, y8 - y4)
                pos = ((x4 + x8) // 2, (y4 + y8) // 2)

                if dist < 40:  # Limiar de toque
                    pinched = True
                    cv2.circle(img, pos, 15, (0, 255, 0), cv2.FILLED)
                else:
                    cv2.circle(img, pos, 10, (0, 255, 255), 2)

        return img, pinched, pos


# --- JOGO PRINCIPAL ---
class MusicGame:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chord Hero AI")
        self.clock = pygame.time.Clock()

        self.synth = Sintetizador()
        self.tracker = HandTracker()
        self.cap = cv2.VideoCapture(0)

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
        if os.path.exists("musica.mp3"):
            pygame.mixer.music.load("musica.mp3")
            pygame.mixer.music.set_volume(0.4)  # Música de fundo mais baixa
            pygame.mixer.music.play()
            self.usando_musica_real = True
            print("Música carregada.")
        else:
            print("Aviso: musica.mp3 não encontrada. Rodando apenas com clock interno.")
            self.usando_musica_real = False
            self.start_time = time.time()

    def pre_carregar_acordes(self):
        print("Sintetizando acordes...")
        # Cria os sons antes do jogo começar para não travar
        unique_chords = set(d["chord_majmin"] for d in DADOS_CHORDS)
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
        for i, dado in enumerate(DADOS_CHORDS):
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


if __name__ == "__main__":
    game = MusicGame()
    game.run()
