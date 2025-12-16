"""
Gerenciador de samples reais de acordes extraídos da música.

Usa arquivo WAV para extrair samples específicos nos timestamps
dos acordes definidos no chords.json.
"""

import pygame
import numpy as np
import wave
import os
import threading


class ChordSampler:
    """
    Gerencia a reprodução de samples reais da música.
    
    Carrega um arquivo WAV e extrai samples em timestamps específicos.
    Cada sample é convertido em pygame.Sound para reprodução.
    """
    
    def __init__(self, music_path: str, sample_duration: float = 1.5):
        """
        Inicializa o sampler de acordes.
        
        Args:
            music_path: Caminho para o arquivo de música (WAV preferido)
            sample_duration: Duração padrão do sample em segundos
        """
        self.music_path = music_path
        self.sample_duration = sample_duration
        self.music_loaded = False
        self.is_playing = False
        self._current_sound = None
        self._sample_channel = None
        
        # Dados do áudio carregado
        self._audio_data = None
        self._sample_rate = 44100
        self._num_channels = 2
        
        # Cache de samples (evita recriar)
        self._sample_cache = {}
        
        # Reservar um canal para samples
        pygame.mixer.set_num_channels(16)
        self._sample_channel = pygame.mixer.Channel(15)
        
        self._carregar_musica()
    
    def _carregar_musica(self):
        """Carrega a música WAV para sampling."""
        # Tentar WAV primeiro, depois MP3
        wav_path = self.music_path.replace('.mp3', '.wav')
        
        if os.path.exists(wav_path):
            try:
                self._load_wav(wav_path)
                return
            except Exception as e:
                print(f"ChordSampler: Erro ao carregar WAV: {e}")
        
        if os.path.exists(self.music_path):
            print(f"ChordSampler: Música encontrada: {self.music_path}")
            print("ChordSampler: Para samples reais, converta para WAV:")
            print(f"  -> {wav_path}")
            self.music_loaded = False
        else:
            print(f"ChordSampler: Nenhuma música encontrada")
            self.music_loaded = False
    
    def _load_wav(self, wav_path: str):
        """Carrega arquivo WAV na memória."""
        print(f"ChordSampler: Carregando WAV: {wav_path}")
        
        with wave.open(wav_path, 'rb') as wf:
            self._sample_rate = wf.getframerate()
            self._num_channels = wf.getnchannels()
            n_frames = wf.getnframes()
            
            # Ler todos os frames
            raw_data = wf.readframes(n_frames)
            
            # Converter para numpy array
            if wf.getsampwidth() == 2:  # 16-bit
                self._audio_data = np.frombuffer(raw_data, dtype=np.int16)
            elif wf.getsampwidth() == 1:  # 8-bit
                self._audio_data = np.frombuffer(raw_data, dtype=np.uint8).astype(np.int16) * 256 - 32768
            else:
                raise ValueError(f"Formato não suportado: {wf.getsampwidth()} bytes por sample")
            
            # Reshape para stereo se necessário
            if self._num_channels == 2:
                self._audio_data = self._audio_data.reshape(-1, 2)
            elif self._num_channels == 1:
                # Converter mono para stereo
                self._audio_data = np.column_stack((self._audio_data, self._audio_data))
        
        duration = len(self._audio_data) / self._sample_rate
        print(f"ChordSampler: WAV carregado! {duration:.1f}s, {self._sample_rate}Hz, {self._num_channels}ch")
        self.music_loaded = True
    
    def _extract_sample(self, start_time: float, duration: float) -> pygame.mixer.Sound:
        """
        Extrai um sample do áudio carregado.
        
        Args:
            start_time: Tempo de início em segundos
            duration: Duração do sample em segundos
            
        Returns:
            pygame.Sound com o sample extraído
        """
        if self._audio_data is None:
            return None
        
        # Calcular índices
        start_frame = int(start_time * self._sample_rate)
        end_frame = int((start_time + duration) * self._sample_rate)
        
        # Garantir que não ultrapasse o final
        end_frame = min(end_frame, len(self._audio_data))
        start_frame = max(0, start_frame)
        
        if start_frame >= end_frame:
            return None
        
        # Extrair segmento
        sample_data = self._audio_data[start_frame:end_frame].copy()
        
        # Aplicar fade in/out para evitar cliques
        fade_samples = min(int(0.02 * self._sample_rate), len(sample_data) // 4)  # 20ms fade
        if fade_samples > 0:
            # Fade in
            fade_in = np.linspace(0, 1, fade_samples)
            sample_data[:fade_samples, 0] = (sample_data[:fade_samples, 0] * fade_in).astype(np.int16)
            sample_data[:fade_samples, 1] = (sample_data[:fade_samples, 1] * fade_in).astype(np.int16)
            
            # Fade out
            fade_out = np.linspace(1, 0, fade_samples)
            sample_data[-fade_samples:, 0] = (sample_data[-fade_samples:, 0] * fade_out).astype(np.int16)
            sample_data[-fade_samples:, 1] = (sample_data[-fade_samples:, 1] * fade_out).astype(np.int16)
        
        # Criar Sound object
        sound = pygame.sndarray.make_sound(sample_data)
        return sound
    
    def tocar_sample(self, start_time: float, duration: float = None):
        """
        Toca um sample da música a partir do timestamp especificado.
        
        Args:
            start_time: Tempo de início do sample em segundos
            duration: Duração do sample (usa sample_duration se None)
        """
        if not self.music_loaded or self._audio_data is None:
            return
        
        if duration is None:
            duration = self.sample_duration
        
        # Parar sample anterior
        self.parar_sample()
        
        # Verificar cache
        cache_key = f"{start_time:.2f}_{duration:.2f}"
        if cache_key not in self._sample_cache:
            sound = self._extract_sample(start_time, duration)
            if sound:
                self._sample_cache[cache_key] = sound
        
        if cache_key in self._sample_cache:
            self._current_sound = self._sample_cache[cache_key]
            self._current_sound.set_volume(0.8)
            self._sample_channel.play(self._current_sound)
            self.is_playing = True
    
    def parar_sample(self):
        """Para o sample atual se estiver tocando."""
        if self._sample_channel:
            self._sample_channel.stop()
        self.is_playing = False
    
    def set_sample_duration(self, duration: float):
        """Define a duração padrão dos samples."""
        self.sample_duration = max(0.1, min(5.0, duration))
    
    def get_sample_duration(self) -> float:
        """Retorna a duração atual dos samples."""
        return self.sample_duration
    
    def is_sample_playing(self) -> bool:
        """Retorna True se um sample está tocando."""
        if self._sample_channel:
            return self._sample_channel.get_busy()
        return False
