import json
import os
from src.utils.config import DADOS_CHORDS_PADRAO
from src.utils.paths import get_assets_path


def load_chords(json_path=None):
    if json_path is None:
        json_path = os.path.join(get_assets_path(), "chords.json")
    # Tenta carregar dados reais se você salvar o JSON que enviou num arquivo
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    else:
        return DADOS_CHORDS_PADRAO
