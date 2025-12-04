# Makefile para o projeto pymusicy

.PHONY: install run clean build

# Instalar dependências usando uv
install:
	uv sync

# Instalar dependências de desenvolvimento (inclui pyinstaller)
install-dev:
	uv sync --group dev

# Executar o jogo
run:
	uv run main.py

# Construir executável com PyInstaller
build:
	@echo "Construindo executável..."
	uv run pyinstaller --onefile main.py --add-data "src/assets;assets" --collect-data mediapipe --hidden-import mediapipe --hidden-import cv2

# Limpar arquivos temporários (se houver)
clean:
	@echo "Limpando arquivos temporários..."
	# Adicione comandos de limpeza se necessário