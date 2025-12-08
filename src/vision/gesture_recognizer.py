"""
Módulo de Reconhecimento de Gestos para o Jogo de Acordes.

Detecta gestos de mão usando landmarks do MediaPipe e compara
com o gesto esperado para cada acorde.
"""

import math
from enum import Enum
from typing import Optional
from src.utils.config import CHORD_GESTURE_MAP, GESTURE_TOLERANCE


class GestureType(Enum):
    """Tipos de gestos suportados."""
    UNKNOWN = "unknown"
    OPEN_HAND = "open_hand"      # Mão aberta, todos dedos estendidos
    FIST = "fist"                # Punho fechado
    PEACE = "peace"              # Paz (indicador + médio estendidos)
    THUMB_UP = "thumb_up"        # Polegar para cima
    INDEX_POINT = "index_point"  # Apontar com indicador
    ROCK = "rock"                # Rock (indicador + mindinho)


# Emojis para representar cada gesto na UI
GESTURE_EMOJI = {
    GestureType.UNKNOWN: "❓",
    GestureType.OPEN_HAND: "✋",
    GestureType.FIST: "✊",
    GestureType.PEACE: "✌",  # Sem variation selector para centralizar melhor
    GestureType.THUMB_UP: "👍",
    GestureType.INDEX_POINT: "👆",
    GestureType.ROCK: "🤘",
}

# Nomes amigáveis para UI
GESTURE_NAMES = {
    GestureType.UNKNOWN: "Desconhecido",
    GestureType.OPEN_HAND: "Mão Aberta",
    GestureType.FIST: "Punho Fechado",
    GestureType.PEACE: "Paz",
    GestureType.THUMB_UP: "Joinha",
    GestureType.INDEX_POINT: "Apontar",
    GestureType.ROCK: "Rock",
}


class GestureRecognizer:
    """
    Reconhecedor de gestos de mão usando landmarks do MediaPipe.
    
    Landmarks importantes:
    - 0: Pulso
    - 4: Ponta do polegar
    - 8: Ponta do indicador
    - 12: Ponta do médio
    - 16: Ponta do anelar
    - 20: Ponta do mindinho
    
    Articulações (base de cada dedo):
    - 2: Base polegar
    - 5: Base indicador (MCP)
    - 9: Base médio (MCP)
    - 13: Base anelar (MCP)
    - 17: Base mindinho (MCP)
    """
    
    def __init__(self, tolerance: float = None):
        self.tolerance = tolerance if tolerance is not None else GESTURE_TOLERANCE
        self.chord_gesture_map = CHORD_GESTURE_MAP
        
        # Histórico para detecção estável (evita flickering)
        self.gesture_history = []
        self.history_size = 5
    
    def _is_finger_extended(self, landmarks, finger_tip_idx: int, finger_pip_idx: int, 
                            finger_mcp_idx: int, is_thumb: bool = False) -> bool:
        """
        Verifica se um dedo está estendido.
        
        Para dedos normais: ponta acima (menor Y) que a articulação PIP
        Para polegar: ponta mais longe do pulso que a articulação
        """
        if landmarks is None or len(landmarks) < 21:
            return False
        
        tip = landmarks[finger_tip_idx]
        pip = landmarks[finger_pip_idx]
        mcp = landmarks[finger_mcp_idx]
        wrist = landmarks[0]
        
        if is_thumb:
            # Polegar: verificar distância horizontal do pulso
            tip_dist = abs(tip.x - wrist.x)
            pip_dist = abs(pip.x - wrist.x)
            return tip_dist > pip_dist
        else:
            # Outros dedos: ponta deve estar acima da articulação PIP
            return tip.y < pip.y
    
    def _get_extended_fingers(self, landmarks) -> dict:
        """
        Retorna um dicionário com o estado de cada dedo (estendido ou não).
        """
        if landmarks is None:
            return {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False
            }
        
        return {
            "thumb": self._is_finger_extended(landmarks, 4, 3, 2, is_thumb=True),
            "index": self._is_finger_extended(landmarks, 8, 6, 5),
            "middle": self._is_finger_extended(landmarks, 12, 10, 9),
            "ring": self._is_finger_extended(landmarks, 16, 14, 13),
            "pinky": self._is_finger_extended(landmarks, 20, 18, 17)
        }
    
    def detect_gesture(self, landmarks) -> tuple[GestureType, float]:
        """
        Detecta o gesto atual baseado nos landmarks da mão.
        
        Returns:
            Tuple de (GestureType, confiança 0.0-1.0)
        """
        if landmarks is None:
            return GestureType.UNKNOWN, 0.0
        
        fingers = self._get_extended_fingers(landmarks)
        extended_count = sum(fingers.values())
        
        # Regras de detecção baseadas em dedos estendidos
        gesture = GestureType.UNKNOWN
        confidence = 0.0
        
        # MÃO ABERTA: todos os dedos estendidos
        if all(fingers.values()):
            gesture = GestureType.OPEN_HAND
            confidence = 1.0
        
        # PUNHO: nenhum dedo estendido
        elif extended_count == 0:
            gesture = GestureType.FIST
            confidence = 1.0
        
        # POLEGAR PARA CIMA: apenas polegar
        elif fingers["thumb"] and extended_count == 1:
            gesture = GestureType.THUMB_UP
            confidence = 1.0
        
        # PAZ: indicador + médio estendidos
        elif (fingers["index"] and fingers["middle"] and 
              not fingers["ring"] and not fingers["pinky"]):
            gesture = GestureType.PEACE
            confidence = 0.95 if not fingers["thumb"] else 0.85
        
        # APONTAR: apenas indicador estendido
        elif fingers["index"] and extended_count == 1:
            gesture = GestureType.INDEX_POINT
            confidence = 1.0
        elif fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            gesture = GestureType.INDEX_POINT
            confidence = 0.9
        
        # ROCK: indicador + mindinho
        elif (fingers["index"] and fingers["pinky"] and 
              not fingers["middle"] and not fingers["ring"]):
            gesture = GestureType.ROCK
            confidence = 0.95
        
        # Gestos parciais (menor confiança)
        elif extended_count >= 4:
            gesture = GestureType.OPEN_HAND
            confidence = extended_count / 5.0
        elif extended_count <= 1:
            gesture = GestureType.FIST
            confidence = 0.7
        
        # Estabilizar detecção usando histórico
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)
        
        # Retorna o gesto mais comum no histórico
        if len(self.gesture_history) >= 3:
            from collections import Counter
            most_common = Counter(self.gesture_history).most_common(1)[0]
            if most_common[1] >= 2:  # Pelo menos 2 ocorrências
                gesture = most_common[0]
        
        return gesture, confidence
    
    def get_expected_gesture(self, chord_name: str) -> GestureType:
        """
        Retorna o gesto esperado para um acorde.
        
        Args:
            chord_name: Nome simples do acorde (ex: "G", "Am", "C")
        """
        gesture_str = self.chord_gesture_map.get(chord_name, "OPEN_HAND")
        
        # Converter string para enum
        gesture_map = {
            "OPEN_HAND": GestureType.OPEN_HAND,
            "FIST": GestureType.FIST,
            "PEACE": GestureType.PEACE,
            "THUMB_UP": GestureType.THUMB_UP,
            "INDEX_POINT": GestureType.INDEX_POINT,
            "ROCK": GestureType.ROCK,
        }
        
        return gesture_map.get(gesture_str, GestureType.OPEN_HAND)
    
    def is_gesture_correct(self, landmarks, chord_name: str) -> tuple[bool, float, GestureType]:
        """
        Verifica se o gesto atual corresponde ao esperado para o acorde.
        
        Args:
            landmarks: Landmarks da mão do MediaPipe
            chord_name: Nome do acorde atual
            
        Returns:
            Tuple de (está_correto, confiança, gesto_detectado)
        """
        detected_gesture, confidence = self.detect_gesture(landmarks)
        expected_gesture = self.get_expected_gesture(chord_name)
        
        is_correct = (detected_gesture == expected_gesture and 
                      confidence >= self.tolerance)
        
        return is_correct, confidence, detected_gesture
    
    def get_gesture_emoji(self, gesture: GestureType) -> str:
        """Retorna o emoji para um gesto."""
        return GESTURE_EMOJI.get(gesture, "❓")
    
    def get_gesture_name(self, gesture: GestureType) -> str:
        """Retorna o nome amigável para um gesto."""
        return GESTURE_NAMES.get(gesture, "Desconhecido")
