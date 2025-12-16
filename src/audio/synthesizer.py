"""
Sintetizador de áudio aprimorado com múltiplos timbres.

Suporta diferentes tipos de instrumentos (piano, guitarra, synth, pad)
e sons de feedback específicos por gesto.
"""

import pygame
import numpy as np
from enum import Enum
from src.utils.config import NOTAS_BASE, INTERVALOS


class Timbre(Enum):
    """Tipos de timbre disponíveis."""
    PIANO = "piano"           # Piano elétrico clássico
    GUITAR = "guitar"         # Guitarra acústica
    SYNTH = "synth"           # Sintetizador lead
    PAD = "pad"               # Pad suave e atmosférico
    ORGAN = "organ"           # Órgão elétrico


class Sintetizador:
    """Sintetizador de acordes com múltiplos timbres."""
    
    def __init__(self, timbre: Timbre = Timbre.PIANO):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.mixer.init()
        pygame.init()
        
        self.sample_rate = 44100
        self.cache_acordes = {}
        self.timbre_atual = timbre
        
        # Sons de feedback
        self.som_erro = None
        self.sons_gesto = {}  # Sons específicos por gesto
        
        # Criar sons de feedback
        self._criar_som_erro()
        self._criar_sons_gesto()
    
    def set_timbre(self, timbre: Timbre):
        """Muda o timbre e limpa o cache."""
        if timbre != self.timbre_atual:
            self.timbre_atual = timbre
            self.cache_acordes.clear()
            print(f"Timbre alterado para: {timbre.value}")
    
    def _criar_som_erro(self):
        """Cria um som dissonante de erro (acorde diminuto + ruído)."""
        duracao = 0.8
        n_samples = int(self.sample_rate * duracao)
        t = np.linspace(0, duracao, n_samples, False)

        # Frequências dissonantes (intervalo de segunda menor - muito feio)
        freq1, freq2, freq3, freq4 = 100, 106, 150, 159

        # Criar ondas com distorção
        onda = 0.4 * np.sin(2 * np.pi * freq1 * t)
        onda += 0.3 * np.sin(2 * np.pi * freq2 * t)
        onda += 0.2 * np.sin(2 * np.pi * freq3 * t)
        onda += 0.2 * np.sin(2 * np.pi * freq4 * t)

        # Adicionar ruído para parecer "raspado"
        ruido = np.random.uniform(-0.1, 0.1, n_samples)
        onda += ruido

        # Envelope com ataque rápido e decay
        envelope = np.exp(-2 * t)
        onda = onda * envelope * 0.7

        # Clipping para distorção
        onda = np.clip(onda, -0.8, 0.8)

        # Converter para 16-bit PCM
        onda = (onda * 32767).astype(np.int16)
        audio_stereo = np.column_stack((onda, onda))

        self.som_erro = pygame.sndarray.make_sound(audio_stereo)
    
    def _criar_sons_gesto(self):
        """Cria sons de feedback para cada tipo de gesto (sons curtos e satisfatórios)."""
        # Som de acerto genérico (bleep agudo)
        self.sons_gesto["acerto"] = self._criar_som_bleep(880, 0.1, tipo="acerto")
        
        # Sons específicos para cada gesto (tons diferentes)
        self.sons_gesto["open_hand"] = self._criar_som_bleep(523.25, 0.15, tipo="major")  # C5
        self.sons_gesto["fist"] = self._criar_som_bleep(392.00, 0.15, tipo="power")       # G4
        self.sons_gesto["peace"] = self._criar_som_bleep(659.25, 0.15, tipo="bright")     # E5
        self.sons_gesto["thumb_up"] = self._criar_som_bleep(784.00, 0.12, tipo="click")   # G5
        self.sons_gesto["index_point"] = self._criar_som_bleep(587.33, 0.12, tipo="tap")  # D5
        self.sons_gesto["rock"] = self._criar_som_bleep(440.00, 0.2, tipo="rock")         # A4
    
    def _criar_som_bleep(self, freq: float, duracao: float, tipo: str = "acerto"):
        """Cria um som curto de feedback."""
        n_samples = int(self.sample_rate * duracao)
        t = np.linspace(0, duracao, n_samples, False)
        
        if tipo == "acerto" or tipo == "major":
            # Som limpo com harmônicos suaves
            onda = 0.7 * np.sin(2 * np.pi * freq * t)
            onda += 0.2 * np.sin(2 * np.pi * freq * 2 * t)
            envelope = np.exp(-6 * t) * (1 - np.exp(-30 * t))  # Ataque rápido
        
        elif tipo == "power":
            # Som mais "pesado" com oitava abaixo
            onda = 0.5 * np.sin(2 * np.pi * freq * t)
            onda += 0.3 * np.sin(2 * np.pi * freq * 0.5 * t)
            onda += 0.2 * np.sin(2 * np.pi * freq * 1.5 * t)
            envelope = np.exp(-4 * t) * (1 - np.exp(-50 * t))
        
        elif tipo == "bright":
            # Som brilhante com harmônicos altos
            onda = 0.5 * np.sin(2 * np.pi * freq * t)
            onda += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
            onda += 0.15 * np.sin(2 * np.pi * freq * 3 * t)
            onda += 0.05 * np.sin(2 * np.pi * freq * 4 * t)
            envelope = np.exp(-8 * t) * (1 - np.exp(-40 * t))
        
        elif tipo == "click":
            # Som de "click" curto
            onda = 0.8 * np.sin(2 * np.pi * freq * t)
            # Adicionar ataque de ruído
            click = np.random.uniform(-0.3, 0.3, min(500, n_samples))
            onda[:len(click)] += click
            envelope = np.exp(-15 * t) * (1 - np.exp(-100 * t))
        
        elif tipo == "tap":
            # Som de "tap" percussivo
            onda = 0.6 * np.sin(2 * np.pi * freq * t)
            # Pitch descendo rapidamente
            pitch_mod = np.exp(-20 * t)
            onda = 0.6 * np.sin(2 * np.pi * freq * t * (1 + 0.5 * pitch_mod))
            envelope = np.exp(-10 * t) * (1 - np.exp(-100 * t))
        
        elif tipo == "rock":
            # Som distorcido estilo rock
            onda = 0.6 * np.sin(2 * np.pi * freq * t)
            onda += 0.4 * np.sin(2 * np.pi * freq * 1.5 * t)  # Quinta
            # Distorção suave
            onda = np.tanh(onda * 2) * 0.7
            envelope = np.exp(-3 * t) * (1 - np.exp(-50 * t))
        
        else:
            onda = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-5 * t)
        
        onda = onda * envelope * 0.6
        onda = (onda * 32767).astype(np.int16)
        audio_stereo = np.column_stack((onda, onda))
        
        return pygame.sndarray.make_sound(audio_stereo)
    
    def tocar_som_erro(self):
        """Toca o som de erro/penalidade."""
        if self.som_erro:
            self.som_erro.set_volume(0.8)
            self.som_erro.play()
    
    def tocar_som_gesto(self, gesto: str):
        """Toca o som de feedback para um gesto específico."""
        gesto_lower = gesto.lower()
        if gesto_lower in self.sons_gesto:
            self.sons_gesto[gesto_lower].set_volume(0.5)
            self.sons_gesto[gesto_lower].play()
        elif "acerto" in self.sons_gesto:
            self.sons_gesto["acerto"].set_volume(0.5)
            self.sons_gesto["acerto"].play()

    def criar_onda(self, freq: float, duracao: float = 1.0, volume: float = 0.5):
        """Cria uma onda sonora com o timbre atual."""
        n_samples = int(self.sample_rate * duracao)
        t = np.linspace(0, duracao, n_samples, False)
        
        if self.timbre_atual == Timbre.PIANO:
            onda = self._onda_piano(freq, t, volume)
        elif self.timbre_atual == Timbre.GUITAR:
            onda = self._onda_guitar(freq, t, volume)
        elif self.timbre_atual == Timbre.SYNTH:
            onda = self._onda_synth(freq, t, volume)
        elif self.timbre_atual == Timbre.PAD:
            onda = self._onda_pad(freq, t, volume)
        elif self.timbre_atual == Timbre.ORGAN:
            onda = self._onda_organ(freq, t, volume)
        else:
            onda = self._onda_piano(freq, t, volume)
        
        # Converter para 16-bit PCM
        onda = (onda * 32767).astype(np.int16)
        return np.column_stack((onda, onda))
    
    def _onda_piano(self, freq: float, t: np.ndarray, volume: float):
        """Timbre de piano elétrico."""
        # Síntese aditiva com harmônicos de piano
        onda = 0.6 * np.sin(2 * np.pi * freq * t)
        onda += 0.25 * np.sin(2 * np.pi * freq * 2 * t)
        onda += 0.1 * np.sin(2 * np.pi * freq * 3 * t)
        onda += 0.05 * np.sin(2 * np.pi * freq * 4 * t)
        
        # Envelope ADSR do piano (ataque rápido, decay longo)
        envelope = np.exp(-2.5 * t) * (1 - np.exp(-50 * t))
        return onda * envelope * volume
    
    def _onda_guitar(self, freq: float, t: np.ndarray, volume: float):
        """Timbre de guitarra acústica."""
        # Mais harmônicos ímpares para som mais "rico"
        onda = 0.5 * np.sin(2 * np.pi * freq * t)
        onda += 0.2 * np.sin(2 * np.pi * freq * 2 * t)
        onda += 0.15 * np.sin(2 * np.pi * freq * 3 * t)
        onda += 0.08 * np.sin(2 * np.pi * freq * 4 * t)
        onda += 0.05 * np.sin(2 * np.pi * freq * 5 * t)
        
        # Pequena inharmonicidade para realismo
        onda += 0.02 * np.sin(2 * np.pi * freq * 2.01 * t)
        
        # Envelope com pico de ataque (como uma corda)
        envelope = np.exp(-3 * t) * (1 - np.exp(-100 * t))
        return onda * envelope * volume
    
    def _onda_synth(self, freq: float, t: np.ndarray, volume: float):
        """Timbre de sintetizador lead."""
        # Onda dente de serra (rica em harmônicos)
        onda = np.zeros_like(t)
        for harm in range(1, 8):
            onda += (1 / harm) * np.sin(2 * np.pi * freq * harm * t)
        onda = onda / 3  # Normalizar
        
        # Envelope sustentado
        duracao = len(t) / self.sample_rate
        envelope = np.ones_like(t)
        attack_samples = int(0.05 * self.sample_rate)
        release_samples = int(0.1 * self.sample_rate)
        
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)
        
        return onda * envelope * volume
    
    def _onda_pad(self, freq: float, t: np.ndarray, volume: float):
        """Timbre de pad atmosférico."""
        # Onda suave com poucas harmônicas
        onda = 0.7 * np.sin(2 * np.pi * freq * t)
        onda += 0.2 * np.sin(2 * np.pi * freq * 2 * t)
        
        # Leve chorus/detune
        onda += 0.1 * np.sin(2 * np.pi * freq * 1.005 * t)
        
        # Envelope lento (fade in/out)
        duracao = len(t) / self.sample_rate
        attack_time = 0.2
        release_time = 0.3
        
        attack_samples = int(attack_time * self.sample_rate)
        release_samples = int(release_time * self.sample_rate)
        
        envelope = np.ones_like(t) * np.exp(-0.5 * t)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples) * envelope[:attack_samples]
        
        return onda * envelope * volume * 0.8
    
    def _onda_organ(self, freq: float, t: np.ndarray, volume: float):
        """Timbre de órgão elétrico (drawbars)."""
        # Simular drawbars do Hammond
        onda = 0.5 * np.sin(2 * np.pi * freq * t)          # 8'
        onda += 0.3 * np.sin(2 * np.pi * freq * 2 * t)     # 4'
        onda += 0.2 * np.sin(2 * np.pi * freq * 3 * t)     # 2 2/3'
        onda += 0.15 * np.sin(2 * np.pi * freq * 4 * t)    # 2'
        onda += 0.1 * np.sin(2 * np.pi * freq * 0.5 * t)   # 16'
        
        # Envelope sustentado (órgão não decai)
        envelope = np.ones_like(t)
        attack_samples = int(0.02 * self.sample_rate)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        return onda * envelope * volume * 0.7

    def gerar_acorde(self, nome_acorde_full: str):
        """Gera um acorde completo. Ex: 'G:maj' ou 'A:min'."""
        cache_key = f"{nome_acorde_full}_{self.timbre_atual.value}"
        
        if cache_key in self.cache_acordes:
            return self.cache_acordes[cache_key]

        try:
            if ":" in nome_acorde_full:
                tonica, tipo = nome_acorde_full.split(":")
            else:
                tonica = nome_acorde_full
                tipo = "maj"

            freq_base = NOTAS_BASE.get(tonica, 261.63)
            intervalos = INTERVALOS.get(tipo, INTERVALOS["maj"])

            # Misturar as notas do acorde
            audio_final = None

            for semi_tons in intervalos:
                freq_nota = freq_base * (2 ** (semi_tons / 12.0))
                onda_nota = self.criar_onda(freq_nota)

                if audio_final is None:
                    audio_final = onda_nota
                else:
                    audio_final = audio_final + onda_nota

            # Normalizar para evitar distorção
            max_val = np.max(np.abs(audio_final))
            if max_val > 0:
                audio_final = (audio_final / max_val * 32767).astype(np.int16)

            som = pygame.sndarray.make_sound(audio_final)
            self.cache_acordes[cache_key] = som
            return som
        except Exception as e:
            print(f"Erro ao gerar acorde {nome_acorde_full}: {e}")
            return None

    def gerar_acorde_curto(self, nome_acorde_full: str, duracao: float = 0.3):
        """
        Gera uma versão curta do acorde para feedback imediato.
        
        Args:
            nome_acorde_full: Nome do acorde (ex: 'G:maj', 'A:min')
            duracao: Duração do som em segundos (padrão: 0.3s)
        
        Returns:
            pygame.Sound ou None
        """
        cache_key = f"{nome_acorde_full}_{self.timbre_atual.value}_short_{duracao}"
        
        if cache_key in self.cache_acordes:
            return self.cache_acordes[cache_key]

        try:
            if ":" in nome_acorde_full:
                tonica, tipo = nome_acorde_full.split(":")
            else:
                tonica = nome_acorde_full
                tipo = "maj"

            freq_base = NOTAS_BASE.get(tonica, 261.63)
            intervalos = INTERVALOS.get(tipo, INTERVALOS["maj"])

            # Criar acorde curto
            n_samples = int(self.sample_rate * duracao)
            t = np.linspace(0, duracao, n_samples, False)
            
            audio_final = np.zeros((n_samples, 2), dtype=np.float64)

            for semi_tons in intervalos:
                freq_nota = freq_base * (2 ** (semi_tons / 12.0))
                
                # Onda simples com harmônicos
                onda = 0.6 * np.sin(2 * np.pi * freq_nota * t)
                onda += 0.25 * np.sin(2 * np.pi * freq_nota * 2 * t)
                onda += 0.1 * np.sin(2 * np.pi * freq_nota * 3 * t)
                
                # Envelope com ataque rápido e decay
                envelope = np.exp(-3 * t) * (1 - np.exp(-50 * t))
                onda = onda * envelope * 0.5
                
                audio_final[:, 0] += onda
                audio_final[:, 1] += onda

            # Normalizar
            max_val = np.max(np.abs(audio_final))
            if max_val > 0:
                audio_final = (audio_final / max_val * 32767 * 0.8).astype(np.int16)
            else:
                audio_final = audio_final.astype(np.int16)

            som = pygame.sndarray.make_sound(audio_final)
            self.cache_acordes[cache_key] = som
            return som
        except Exception as e:
            print(f"Erro ao gerar acorde curto {nome_acorde_full}: {e}")
            return None
