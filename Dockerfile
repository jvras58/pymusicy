# syntax = docker/dockerfile:1.2
# Dockerfile para build do PyMusicy com PyInstaller
# NOTA: Este build gera um executável LINUX, não Windows

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Instalar dependências de sistema necessárias para OpenCV, MediaPipe, Pygame e PyInstaller
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    # Dependências para OpenCV
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    # Dependências para Pygame/SDL
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    # Dependências para PyInstaller
    binutils \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Use a writable cache directory inside the image to avoid buildkit writing to /root
ENV UV_CACHE_DIR=/app/.cache/uv

# Ensure cache dir exists
RUN mkdir -p /app/.cache/uv

# Copiar arquivos de dependências primeiro (melhor cache de layers)
COPY uv.lock pyproject.toml /app/

# Instalar dependências incluindo grupo dev (pyinstaller)
RUN uv sync --locked --no-install-project

# Copiar código fonte
COPY . /app

# Instalar o projeto
RUN uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

# Build com PyInstaller
RUN uv run pyinstaller --onefile main.py \
    --add-data "src/assets:assets" \
    --collect-data mediapipe \
    --hidden-import mediapipe \
    --hidden-import cv2 \
    --distpath /app/dist \
    --workpath /app/build \
    --specpath /app

# Estágio final (opcional - imagem menor só com o executável)
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar apenas o executável do estágio de build
COPY --from=0 /app/dist/main /app/main

ENTRYPOINT ["/app/main"]