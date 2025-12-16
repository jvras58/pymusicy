"""Configurações globais do Chord Hero AI.

Contém constantes de teoria musical, mapeamentos de acordes para gestos,
e parâmetros de configuração do jogo.
"""

# Dados padrão de acordes para demonstração
DADOS_CHORDS_PADRAO = [
    {
        "start": 0.27,
        "end": 11.66,
        "chord_majmin": "G:maj",
        "chord_simple_pop": "G",
    },
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
    {
        "start": 17.66,
        "end": 25.00,
        "chord_majmin": "D:maj",
        "chord_simple_pop": "D",
    },
]

# Frequências base das notas musicais (Hz)
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

# Intervalos em semitons para cada tipo de acorde
INTERVALOS = {
    "maj": [0, 4, 7],  # Tônica, Terça Maior, Quinta Justa
    "min": [0, 3, 7],  # Tônica, Terça Menor, Quinta Justa
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "7": [0, 4, 7, 10],
}

# --- CONFIGURAÇÕES DE PENALIDADE ---
FAIL_MODE_ENABLED = (
    True  # Ativar/desativar o modo de penalidade (True = ativado, False = desativado)
)
PENALTY_TIME_SECONDS = 3.0  # Tempo de penalidade quando erra (em segundos)
FAIL_COOLDOWN_SECONDS = (
    2.0  # Tempo de imunidade após sair de um FAIL (não dá FAIL novamente)
)
MIN_CHORD_DURATION = (
    1.0  # Duração mínima do acorde (em segundos) para contar como FAIL se não tocar
)

# --- CONFIGURAÇÕES DE GESTOS ---
GESTURE_TOLERANCE = 0.7  # Confiança mínima para aceitar gesto (0.0-1.0)
GESTURE_HOLD_TIME = 0.3  # Tempo que o gesto deve ser mantido (segundos)
SHOW_GESTURE_DEBUG = False  # Mostrar debug dos landmarks/detecção

# Mapeamento de acordes → gestos
# Gestos disponíveis: OPEN_HAND, FIST, PEACE, THUMB_UP, INDEX_POINT, ROCK
CHORD_GESTURE_MAP = {
    # Acordes maiores
    "G": "OPEN_HAND",       # Mão aberta ✋
    "C": "PEACE",           # Paz ✌️
    "D": "THUMB_UP",        # Joinha 👍
    "E": "ROCK",            # Rock 🤘
    "F": "INDEX_POINT",     # Apontar 👆
    "A": "PEACE",           # Paz ✌️
    "B": "THUMB_UP",        # Joinha 👍
    # Acordes menores
    "Am": "FIST",           # Punho ✊
    "Am7": "FIST",          # Punho ✊
    "Em": "FIST",           # Punho ✊
    "Dm": "INDEX_POINT",    # Apontar 👆
    "Bm": "ROCK",           # Rock 🤘
    "Fm": "INDEX_POINT",    # Apontar 👆
}

# --- CONFIGURAÇÕES DE ÁUDIO ---
SYNTH_ENABLED = True           # Som sintetizado ativo por padrão
REAL_AUDIO_ENABLED = True      # Som real (sample da música) ativo por padrão
REAL_SAMPLE_DURATION = 1.5     # Duração do sample real em segundos
SYNTH_DURATION = 0.3           # Duração do som sintetizado curto

# --- CONFIGURAÇÕES DE PREVIEW E DICAS ---
HINT_ENABLED = True            # Mostrar dica do próximo gesto (H para toggle)
PREVIEW_DURATION = 15.0        # Duração da tela de preview em segundos
