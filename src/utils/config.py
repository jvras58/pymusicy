# --- DADOS DE EXEMPLO ---
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

# --- TEORIA MUSICAL ---
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
