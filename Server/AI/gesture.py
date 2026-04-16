import cv2
import numpy as np

class GestureRecognizer:
    def __init__(self):
        """Hand gesture recognizer using OpenCV skin detection and contour analysis."""
        print("[OK] Gesture recognizer initialized (OpenCV-based)")
        
        # Define skin color range in HSV
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        self.lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
        self.upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)

    def process_frame(self, frame):
        """
        Detects hand gestures using OpenCV skin detection and contour analysis.
        Returns a gesture string or None if no clear gesture is detected.
        """
        if frame is None:
            return None

        try:
            # Convert BGR to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for skin color
            mask1 = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
            mask2 = cv2.inRange(hsv, self.lower_skin2, self.upper_skin2)
            skin_mask = cv2.bitwise_or(mask1, mask2)
            
            # Apply morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(skin_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Get the largest contour (likely the hand)
            hand_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(hand_contour)
            
            # Minimum area threshold to avoid noise
            if area < 1000:
                return None
            
            print(f"[Hand detected] Area: {int(area)}")
            
            # Calculate hand properties
            perimeter = cv2.arcLength(hand_contour, True)
            if perimeter == 0:
                return None
            
            # Get convex hull
            hull = cv2.convexHull(hand_contour)
            hull_area = cv2.contourArea(hull)
            
            if hull_area == 0:
                return None
            
            # Solidity: ratio of contour area to convex hull area
            solidity = area / hull_area
            
            # Count hand vertices using approx contour
            epsilon = 0.02 * perimeter
            approx = cv2.approxPolyDP(hand_contour, epsilon, True)
            vertices = len(approx)
            
            # Classify gesture based on solidity and vertices
            if solidity > 0.85 and vertices < 8:
                # Closed, circular = CLOSED_FIST
                return "CLOSED_FIST"
            elif solidity < 0.65 and vertices > 10:
                # Open, low solidity = OPEN_PALM
                return "OPEN_PALM"
            elif 0.65 <= solidity <= 0.85:
                if vertices < 10:
                    # Less complex, semi-closed
                    return "POINTING_UP"
                else:
                    # More complex, semi-open
                    return "PEACE_SIGN"
            
            return None
            
        except Exception as e:
            print(f"ERROR in gesture processing: {e}")
            return None
            import traceback
            traceback.print_exc()
            return None