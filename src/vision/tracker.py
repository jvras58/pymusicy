import cv2
import mediapipe as mp
import math


class HandTracker:
    def __init__(self, draw_landmarks=True):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
        self.last_pinch_time = 0
        self.draw_landmarks = draw_landmarks
        
        # Estilo customizado para os landmarks (mais sutil)
        self.landmark_style = self.mp_draw.DrawingSpec(
            color=(100, 100, 100),  # Cinza escuro
            thickness=1,
            circle_radius=2
        )
        self.connection_style = self.mp_draw.DrawingSpec(
            color=(150, 150, 150),  # Cinza claro
            thickness=1
        )

    def process(self, img):
        """
        Processa uma imagem e detecta mãos.
        
        Returns:
            Tuple de (imagem_processada, is_pinching, posição_pinch, landmarks)
            landmarks é uma lista de 21 pontos ou None se não houver mão
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        pinched = False
        pos = (0, 0)
        landmarks = None

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # Desenhar landmarks com estilo customizado (mais sutil)
                if self.draw_landmarks:
                    self.mp_draw.draw_landmarks(
                        img, hand_lms, self.mp_hands.HAND_CONNECTIONS,
                        self.landmark_style,
                        self.connection_style
                    )
                
                # Guardar landmarks para reconhecimento de gestos
                landmarks = hand_lms.landmark

                h, w, c = img.shape
                # Pontas dos dedos: 4 (Polegar), 8 (Indicador)
                x4, y4 = (
                    int(hand_lms.landmark[4].x * w),
                    int(hand_lms.landmark[4].y * h),
                )
                x8, y8 = (
                    int(hand_lms.landmark[8].x * w),
                    int(hand_lms.landmark[8].y * h),
                )

                dist = math.hypot(x8 - x4, y8 - y4)
                pos = ((x4 + x8) // 2, (y4 + y8) // 2)

                if dist < 40:  # Limiar de toque
                    pinched = True

        return img, pinched, pos, landmarks

