# 🎸 Chord Hero AI – Harmonia Ativa

O **Chord Hero AI** é um experimento interativo que transforma sua **webcam em um instrumento musical**.

Diferente de jogos de ritmo tradicionais, em que você só aperta botões para ganhar pontos, aqui **você realmente toca a harmonia da música**:

- Se você **não toca**, a música fica “vazia”.
- Se você **toca no ritmo**, o acorde correto é sintetizado em tempo real e **preenche a música**.

---

## 🧠 Como funciona

### 1. Conceito de “Harmonia Ativa”

A música é separada em duas camadas:

- **Backing Track (fundo)**  
  Bateria, baixo e vocais tocam continuamente a partir de um arquivo `.mp3`.

- **Harmonia (sintetizador)**  
  Os acordes de guitarra/piano/teclado **não estão** no `.mp3`.  
  Eles são gerados matematicamente pelo código (**Python + NumPy**) **apenas quando você ativa o gesto**.

Isso cria a ilusão de que **seus dedos estão produzindo o som**.

### 2. Fluxo de dados

1. **Leitura do JSON**  
   O jogo carrega um mapa da música (`chords.json`) que diz, por exemplo:  
   _“Dos 2.0s aos 4.0s, o acorde é Sol Maior (`G:maj`)”_.

2. **Visão computacional**  
   O **MediaPipe** rastreia sua mão ~30 vezes por segundo via webcam.

3. **Gesto de ativação**  
   O jogo mede a distância entre **Polegar** e **Indicador**:  
   - Distância `< 40px` → **PINÇA (toque)**.

4. **Síntese de áudio**  
   Se você fizer a pinça **dentro da janela de um acorde**, o código:
   - calcula as frequências das notas desse acorde  
     (ex.: G = 392 Hz, B = 493 Hz, D = 587 Hz),
   - mistura as ondas senoidais,
   - e toca o som em tempo real.

---

## 🏗️ Arquitetura do Projeto

O projeto segue uma estrutura modular organizada em pastas para facilitar a manutenção e expansão. Abaixo, uma visão geral dos diretórios e arquivos principais:

### Estrutura Geral

```
pymusicy/
├── .gitignore              # Arquivo para ignorar arquivos temporários no Git (ex.: __pycache__, .venv)
├── .python-version         # Especifica a versão do Python recomendada (3.12)
├── main.py                 # Ponto de entrada do jogo; inicializa e executa a classe MusicGame
├── Makefile                # Scripts de automação para instalação, execução e limpeza (usa uv)
├── pyproject.toml          # Configuração do projeto Python (dependências, versão, etc.)
├── README.md               # Este arquivo de documentação
└── src/                    # Código-fonte principal
    ├── assets/             # Recursos estáticos
    │   └── chords.json     # Dados JSON com os acordes e tempos da música (ex.: start, end, chord_majmin)
    │   └── musica.mp3      # Musica mp3
    ├── audio/              # Módulo de síntese de áudio
    │   └── synthesizer.py  # Classe Sintetizador: gera ondas sonoras para acordes usando NumPy e Pygame
    ├── game/               # Lógica principal do jogo
    │   └── engine.py       # Classe MusicGame: gerencia o loop do jogo, visão computacional, áudio e UI
    ├── utils/              # Utilitários e configurações
    │   ├── config.py       # Constantes musicais (notas base, intervalos) e dados de exemplo
    │   └── data_loader.py  # Função para carregar dados de acordes do JSON ou fallback para padrão
    └── vision/             # Módulo de visão computacional
        └── tracker.py      # Classe HandTracker: detecta gestos da mão via MediaPipe e OpenCV
```

### Descrição dos Módulos Principais
- **src/game/engine.py**: Núcleo do jogo. Integra todos os módulos (áudio, visão, dados) em um loop principal. Lida com entrada do usuário, renderização da UI e lógica de pontuação.
- **src/audio/synthesizer.py**: Responsável pela geração de sons. Usa síntese aditiva para criar acordes em tempo real, com cache para otimização.
- **src/vision/tracker.py**: Processa a webcam para detectar pinças (gestos de "toque"). Retorna posição e estado do gesto para o engine.
- **src/utils/data_loader.py**: Carrega os dados dos acordes do arquivo JSON ou usa um conjunto padrão se o arquivo não existir.
- **src/utils/config.py**: Contém definições musicais (frequências de notas, intervalos de acordes) e dados de exemplo para testes.
- **src/assets/chords.json**: Arquivo de dados com o mapa de acordes da música (tempos de início/fim e nomes dos acordes).

Essa estrutura permite fácil extensão, como adicionar novos modos de jogo ou sintetizadores alternativos.

## 🛠️ Instalação e requisitos

Você precisa de:

- **Python 3.12 ou superior**
- Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)**

Instale as dependências com:

```bash
make install
````

Ou diretamente:

```bash
uv sync
```

Isso instalará as bibliotecas necessárias:

* `pygame`
* `opencv-python`
* `mediapipe`
* `numpy`

---

## 🏗️ Construindo um Executável

Para criar um executável standalone do jogo (útil para distribuição sem instalar Python), use o PyInstaller.

### 1. Instalar dependências de desenvolvimento

```bash
make install-dev
```

Ou diretamente:

```bash
uv sync --group dev
```

### 2. Construir o executável

```bash
make build
```

Ou diretamente:

```bash
uv run pyinstaller --onefile main.py --add-data "src/assets;assets" --collect-data mediapipe --hidden-import mediapipe --hidden-import cv2
```

O executável será gerado em `dist/main.exe` (no Windows).

**Nota:** Os arquivos estáticos em `src/assets/` (como `chords.json` e `musica.mp3`) são incluídos automaticamente no executável.

---

## 🎮 Como jogar

### 1. Prepare o ambiente

* Vá para um local **bem iluminado**.
* Certifique-se de que a **webcam enxerga sua mão claramente**.

### 2. Arquivos necessários

Na pasta do projeto:

* `chord_hero.py` (script principal)
* (Opcional, mas recomendado) `musica.mp3`
* (Opcional) `chords.json` com os tempos da música

> Se não houver `chords.json`, o jogo usa um **padrão de demonstração**.

### 3. Executando o jogo

Com `make`:

```bash
make run
```

Ou diretamente com `uv`:

```bash
uv run main.py
```

### 4. Interface

* **Círculo central**: pulsa no ritmo

  * 🔵 **Azul**: aguardando toque
  * 🟢 **Verde**: toque confirmado (acorde soando)

* **Barra inferior**: mostra quanto tempo falta para o acorde mudar.

* **Texto central**: exibe o nome do acorde atual (ex.: `Cm`, `G`, `A#`).

### 5. Movimento da mão

* Use movimentos de **“pinça”** ou **“bicar”**:

  * Juntar e separar **polegar e indicador** no ritmo da batida.
* Você pode:

  * **Dedilhar várias vezes** dentro do mesmo acorde (criar ritmo), ou
  * **Segurar o gesto** para um som mais longo
    (dependendo do envelope do sintetizador).

---

## 🎵 Personalizando (sua própria música)

Para usar **qualquer música** no jogo, você precisa de dois passos:

### 1. Áudio (`musica.mp3`)

Coloque o arquivo de áudio na pasta do projeto e renomeie para:

```text
musica.mp3
```

#### Escolha da faixa: original vs. backing track

Para a experiência ser máxima (aquela sensação de **“uau, sou eu quem está tocando!”**), o ideal é que o arquivo `musica.mp3` seja uma **Backing Track**: uma faixa de fundo **sem o instrumento harmônico principal** (guitarra/piano/teclado).

* **Se você usar a música original completa** (com a guitarra/piano original tocando):

  * **Funciona?** Sim, perfeitamente.
  * **Sensação:** vira um **reforço**. Você sente que está tocando junto com a banda, como uma segunda guitarra ou dobrando o piano. Ainda é divertido, mas a música não “morre” se você parar.

* **Se você usar uma Backing Track** (só bateria, baixo, etc.):

  * **Sensação:** é de **autoria total**.

    * Se você parar, a harmonia some e fica só a “cozinha” (bateria/baixo).
    * Quando você acerta, a música fica completa.

### 2. Acordes (`chords.json`)

Crie um arquivo `chords.json` com a estrutura abaixo.
Você pode usar ferramentas de Music AI para extrair automaticamente **acordes e tempos** de uma música.

#### Exemplo de estrutura

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

* `start` / `end`: segundos onde o acorde começa e termina.
* `chord_majmin`: nota fundamental + tipo (`:maj`, `:min`).

  * O sintetizador entende esses sufixos para calcular terças e quintas.
* `chord_simple_pop`: texto amigável exibido na tela para o jogador.

---

## 🎧 Exemplo: música de demonstração

O projeto já inclui uma versão karaokê de **“Anunciação” (Alceu Valença)** com:

* `musica.mp3`
* `chords.json` correspondente

Tudo pronto para você testar o fluxo completo logo de cara.

---

## 🧪 Detalhes técnicos do sintetizador

O motor de som usa **síntese aditiva simples**:

1. Para cada nota do acorde:

   * é gerada uma **onda senoidal fundamental**.

2. São adicionados **harmônicos**:

   * 2× e 3× a frequência fundamental,
   * com volume menor para dar **timbre** ao som.

3. É aplicado um **envelope ADSR** simplificado:

   * **Ataque rápido**,
   * **decay** exponencial,
   * para que o som não pareça um “bip” estático de computador,
   * mas sim algo próximo a **uma corda vibrando**.

---

## 🚀 Próximos passos

* Trocar a música e o `chords.json` para testar diferentes estilos.
* Refinar gestos, envelopes e timbres para aproximar ainda mais de um instrumento real.
* Integrar novos modos de jogo (ex.: treino de progressões, modos de improviso, etc.).
