import cv2

try:
    import mediapipe as mp
    try:
        from mediapipe.solutions import hands as mp_hands
    except Exception:
        try:
            from mediapipe.python.solutions import hands as mp_hands
        except Exception:
            mp_hands = None
except Exception:
    mp = None
    mp_hands = None

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp_hands
        self.hands = None

        if self.mp_hands is not None:
            try:
                self.hands = self.mp_hands.Hands(
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.3,
                    max_num_hands=1
                )
            except Exception as e:
                print(f"MediaPipe hand model unavailable: {e}")
                self.hands = None


    def process_frame(self, frame):
        """
        Takes an OpenCV frame (BGR), processes it, and returns a recognized gesture string.
        Returns None if no gesture is recognized.
        """
        if self.hands is None:
            return None

        # Convert the image from BGR to RGB as required by MediaPipe
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        if not results.multi_hand_landmarks:
            return None

        # Get the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]
        print(f"[Gesture] Hand detected with {len(hand_landmarks.landmark)} landmarks")
        
        # Check finger positions (Tip vs PIP joint)
        # A lower Y coordinate means the point is higher up on the screen
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP].y
        index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP].y
        
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y

        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP].y
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP].y

        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP].y
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP].y

        fingers_up = 0
        if index_tip < index_pip: fingers_up += 1
        if middle_tip < middle_pip: fingers_up += 1
        if ring_tip < ring_pip: fingers_up += 1
        if pinky_tip < pinky_pip: fingers_up += 1

        print(f"[Gesture] Fingers up: {fingers_up}")

        # Map finger counts to gestures
        if fingers_up == 4:
            print("[Gesture] Detected: OPEN_PALM")
            return "OPEN_PALM" 
        elif fingers_up == 0:
            print("[Gesture] Detected: CLOSED_FIST")
            return "CLOSED_FIST"
        elif fingers_up == 1:
            print("[Gesture] Detected: POINTING_UP")
            return "POINTING_UP"
        elif fingers_up == 2:
            print("[Gesture] Detected: PEACE_SIGN")
            return "PEACE_SIGN" 
        
        print(f"[Gesture] Unknown finger count: {fingers_up}")
        return None