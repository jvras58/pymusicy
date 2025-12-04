
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
uv run cv_rhythm_game.py
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

### 1. Áudio

Coloque o arquivo de áudio na pasta do projeto e renomeie para:

```text
musica.mp3
```

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

