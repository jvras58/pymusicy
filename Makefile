# Makefile para o projeto pymusicy

.PHONY: install run clean build build-docker extract-binary

# Instalar dependências usando uv
install:
	uv sync

# Instalar dependências de desenvolvimento (inclui pyinstaller)
install-dev:
	uv sync --group dev

# Executar o jogo
run:
	uv run main.py

# Construir executável com PyInstaller (local - Windows)
build:
	@echo "Construindo executável..."
	uv run pyinstaller --onefile main.py --add-data "src/assets;assets" --collect-data mediapipe --hidden-import mediapipe --hidden-import cv2

# Construir executável com Docker (gera executável Linux)
build-docker:
	@echo "Construindo imagem Docker e executável Linux..."
	docker build -t pymusicy-builder .
	@echo "Build completo! Executável Linux dentro da imagem."

# Extrair executável Linux da imagem Docker
extract-binary:
	@echo "Extraindo executável da imagem Docker..."
	docker create --name pymusicy-temp pymusicy-builder
	docker cp pymusicy-temp:/app/main ./dist/main-linux
	docker rm pymusicy-temp
	@echo "Executável extraído para ./dist/main-linux"

# Build completo via Docker (build + extração)
build-docker-full: build-docker extract-binary
	@echo "Build Docker completo! Executável em ./dist/main-linux"

# Limpar arquivos temporários (se houver)
clean:
	@echo "Limpando arquivos temporários..."
	rm -rf build/ dist/ *.spec __pycache__
	# Adicione comandos de limpeza se necessário