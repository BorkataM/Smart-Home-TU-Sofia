import cv2

try:
    import mediapipe as mp
    print("✓ mediapipe imported")
    try:
        from mediapipe.solutions import hands as mp_hands
        print("✓ mediapipe.solutions.hands imported")
    except Exception as e1:
        print(f"ERROR: mediapipe.solutions.hands failed: {e1}")
        try:
            from mediapipe.python.solutions import hands as mp_hands
            print("✓ mediapipe.python.solutions.hands imported (fallback)")
        except Exception as e2:
            print(f"ERROR: mediapipe.python.solutions.hands failed: {e2}")
            mp_hands = None
except Exception as e:
    print(f"ERROR: mediapipe import failed: {e}")
    mp = None
    mp_hands = None

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp_hands
        self.hands = None

        if self.mp_hands is None:
            print("ERROR: MediaPipe hands module not available!")
            return
            
        try:
            self.hands = self.mp_hands.Hands(
                min_detection_confidence=0.3,
                min_tracking_confidence=0.1,
                max_num_hands=1
            )
            print("✓ MediaPipe hands initialized")
        except Exception as e:
            print(f"ERROR: MediaPipe hand model unavailable: {e}")
            self.hands = None


    def process_frame(self, frame):
        """
        Takes an OpenCV frame (BGR), processes it, and returns a recognized gesture string.
        Returns None if no gesture is recognized.
        """
        if self.hands is None:
            return None
        
        if frame is None:
            return None

        try:
            # Convert the image from BGR to RGB as required by MediaPipe
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)

            if not results.multi_hand_landmarks:
                return None

            # Get the first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            print(f"[Hand detected]")
            
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

            print(f"[Fingers up: {fingers_up}]")

            # Map finger counts to gestures
            if fingers_up == 4:
                return "OPEN_PALM" 
            elif fingers_up == 0:
                return "CLOSED_FIST"
            elif fingers_up == 1:
                return "POINTING_UP"
            elif fingers_up == 2:
                return "PEACE_SIGN" 
            
            return None
        except Exception as e:
            print(f"ERROR in gesture: {e}")
            import traceback
            traceback.print_exc()
            return None