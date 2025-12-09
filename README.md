# 🎸 Chord Hero AI – Jogo de Gestos Musicais

O **Chord Hero AI** é um jogo interativo que transforma sua **webcam em um instrumento musical**.

Diferente de jogos de ritmo tradicionais, aqui **você faz gestos com a mão para tocar acordes**:

- A música **pausa** no início de cada acorde
- Você deve fazer o **gesto correto** correspondente ao acorde
- Quando acerta, o acorde é sintetizado e a **música avança**

---

## 🎮 Como Jogar

### 1. Execute o jogo

```bash
make run
```

Ou diretamente:

```bash
uv run main.py
```

### 2. Tela Inicial

- Pressione **ESPAÇO** para iniciar
- Veja os **5 gestos disponíveis** com seus emojis

### 3. Gameplay

1. A música pausa e mostra o **acorde atual** com o **gesto esperado**
2. Faça o gesto correspondente com sua mão na frente da câmera
3. Mantenha o gesto por ~0.3 segundos (o arco verde mostra o progresso)
4. Quando aceito, você vê "CORRETO!" e a música toca
5. Repita para cada acorde até o fim!

### 4. Gestos Disponíveis

| Gesto | Emoji | Descrição | Acordes |
|-------|-------|-----------|---------|
| **Mão Aberta** | ✋ | Todos os dedos estendidos | G, E |
| **Punho** | ✊ | Mão fechada | Am, Em |
| **Paz** | ✌ | Indicador + médio estendidos | C, A |
| **Joinha** | 👍 | Polegar para cima | D, B |
| **Apontar** | 👆 | Indicador estendido | F, Dm |

### 5. Interface

- **Círculo central**: Mostra o gesto esperado
  - 🔵 **Azul**: Aguardando gesto
  - 🟢 **Verde**: Gesto correto detectado
- **Arco de progresso**: Mostra quanto tempo falta para confirmar o gesto
- **Canto inferior direito**: Seu gesto atual + nível de confiança
- **Preview**: Mostra o próximo acorde e gesto

### 6. Controles do Teclado

| Tecla | Ação |
|-------|------|
| `ESPAÇO` | Iniciar jogo / Reiniciar após fim |
| `M` | Toggle Fail Mode (liga/desliga penalidade por tempo) |
| `T` | Trocar Timbre do sintetizador |
| `ESC` | Sair do jogo |

### 7. Timbres Disponíveis

Pressione **T** para alternar entre os timbres:

| Timbre | Descrição |
|--------|-----------|
| **Piano** | Som clássico de piano elétrico (padrão) |
| **Guitar** | Guitarra acústica com harmônicos ricos |
| **Synth** | Sintetizador lead estilo dente de serra |
| **Pad** | Som atmosférico e suave com chorus |
| **Organ** | Órgão elétrico estilo Hammond |

### 8. Fail Mode

Quando **ativado** (padrão), você tem um tempo limite para fazer cada gesto:
- Uma barra de tempo mostra quanto tempo resta (verde → amarelo → vermelho)
- Se o tempo acabar, você entra no modo **ERROU!** com penalidade
- Pressione **M** para desativar e jogar sem pressão de tempo

---

## 🧠 Como Funciona

### Fluxo do Jogo

```
INTRO → [ESPAÇO] → AGUARDANDO GESTO → [gesto correto] → CORRETO! → TOCANDO → próximo acorde...
```

### Detecção de Gestos

O jogo usa **MediaPipe Hands** para detectar landmarks da mão e classifica gestos baseado em quais dedos estão estendidos:

- **Mão aberta**: 5 dedos estendidos
- **Punho**: 0 dedos estendidos
- **Paz**: Indicador + médio
- **Joinha**: Apenas polegar
- **Apontar**: Apenas indicador

### Síntese de Acordes

Quando você acerta o gesto, o sintetizador gera o acorde em tempo real usando **síntese aditiva**:

1. Calcula as frequências das notas do acorde
2. Gera ondas senoidais com harmônicos
3. Aplica envelope ADSR para som natural

---

## 🏗️ Arquitetura do Projeto

```
pymusicy/
├── main.py                 # Ponto de entrada
├── Makefile                # Scripts de automação
├── pyproject.toml          # Configuração Python
└── src/
    ├── assets/
    │   ├── chords.json     # Mapa de acordes da música
    │   └── musica.mp3      # Arquivo de áudio
    ├── audio/
    │   └── synthesizer.py  # Síntese de acordes
    ├── game/
    │   └── engine.py       # Lógica principal e UI
    ├── utils/
    │   ├── config.py       # Configurações e mapeamentos
    │   ├── data_loader.py  # Carregamento de dados
    │   └── paths.py        # Caminhos de arquivos
    └── vision/
        ├── tracker.py          # Detecção de mãos via MediaPipe
        └── gesture_recognizer.py  # Classificação de gestos
```

---

## ⚙️ Configuração

### Mapeamento de Gestos

Edite `src/utils/config.py` para personalizar qual gesto corresponde a cada acorde:

```python
CHORD_GESTURE_MAP = {
    "G": "OPEN_HAND",       # ✋
    "Am": "FIST",           # ✊
    "C": "PEACE",           # ✌
    "D": "THUMB_UP",        # 👍
    "F": "INDEX_POINT",     # 👆
    # Adicione mais...
}
```

### Sensibilidade

```python
GESTURE_TOLERANCE = 0.7   # Confiança mínima (0.0-1.0)
GESTURE_HOLD_TIME = 0.3   # Tempo para confirmar gesto (segundos)
```

---

## 🛠️ Instalação

### Requisitos

- **Python 3.12 ou superior**
- Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)**
- Webcam

### Instalação

```bash
make install
```

Ou:

```bash
uv sync
```

Isso instalará:
- `pygame` (áudio e gráficos)
- `opencv-python` (captura de vídeo)
- `mediapipe` (detecção de mãos)
- `numpy` (síntese de áudio)

---

## 🎵 Personalizando

### Usando sua própria música

1. **Áudio**: Coloque seu arquivo em `src/assets/musica.mp3`

2. **Acordes**: Crie `src/assets/chords.json` com a estrutura:

```json
[
  {
    "start": 0.0,
    "end": 4.5,
    "chord_majmin": "C:maj",
    "chord_simple_pop": "C"
  },
  {
    "start": 4.5,
    "end": 8.0,
    "chord_majmin": "G:min",
    "chord_simple_pop": "Gm"
  }
]
```

Você pode usar ferramentas de **Music AI** para extrair acordes automaticamente.

---

## 🏗️ Construindo Executável

```bash
make install-dev
make build
```

O executável será gerado em `dist/main.exe`.

---

## 🎧 Exemplo Incluído

O projeto inclui uma versão karaokê de **"Anunciação" (Alceu Valença)** com:

- `musica.mp3`
- `chords.json` correspondente

Pronto para testar! 🎶

---

## 🚀 Dicas

- Use um ambiente **bem iluminado**
- Mantenha a mão **visível e estável** na frente da câmera
- Pratique os gestos antes de jogar
- O arco verde ao redor do círculo mostra o progresso do gesto
