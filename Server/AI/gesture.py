import cv2
import mediapipe as mp

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        # Initialize the MediaPipe Hands model
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.5,
            max_num_hands=1
        )

    def process_frame(self, frame):
        """
        Takes an OpenCV frame (BGR), processes it, and returns a recognized gesture string.
        Returns None if no gesture is recognized.
        """
        # Convert the image from BGR to RGB as required by MediaPipe
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        if not results.multi_hand_landmarks:
            return None

        # Get the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]
        
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