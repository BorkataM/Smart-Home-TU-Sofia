Backend Architecture Overview
The backend for the Multimodal Smart Home project is built entirely in Python. It acts as the central brain of the system, handling real-time data streams, processing AI models for multimodal inputs (voice and gestures), and managing the state of the simulated virtual room.

1. Core Technologies Used:

Server & Communication: FastAPI paired with WebSockets. WebSockets were chosen over standard HTTP requests because gesture recognition requires a continuous, real-time stream of video frames with zero latency.

Gesture Recognition (Computer Vision): OpenCV (for image handling) and Google's MediaPipe (mediapipe==0.10.14). MediaPipe maps 21 3D landmarks on the human hand.

Voice Recognition (NLP): The SpeechRecognition library utilizing the Google Web Speech API to transcribe live audio from the microphone into text.

2. How the Logic Flows:

The State Manager (state.py): This file holds the current "truth" of the virtual room in a simple dictionary (e.g., is the light on? What is the fan speed?).

The AI Modules (gesture.py & voice.py): * The gesture module calculates the Y-coordinates of the finger tips versus the lower finger joints. If the tips are higher, the finger is "up." It counts the fingers to determine the gesture (e.g., 4 fingers = Open Palm, 0 fingers = Closed Fist).

The voice module runs in an asynchronous background loop, continuously listening for specific trigger phrases (like "light on" or "fan off") without freezing the video feed.

The Main Server (main.py): The FastAPI server opens a two-way WebSocket connection. The frontend continuously fires Base64-encoded webcam frames to this socket. The server decodes the frame, runs it through the MediaPipe gesture logic, and simultaneously checks the background voice loop. If either modality triggers a valid command, the server updates the state.py variables and immediately blasts the new state back to the frontend as a JSON object.

3. Meeting the Project Requirements:
This architecture directly satisfies the multimodality requirement of the assignment. It successfully combines two distinct input methods (voice and visual gestures) to control simulated device functions (a virtual light and a virtual fan) seamlessly and in real-time.