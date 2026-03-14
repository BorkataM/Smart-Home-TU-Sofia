import asyncio
import cv2
import base64
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from Server.State.state import room_state
from Server.AI.gesture import GestureRecognizer
from Server.AI.voice import VoiceRecognizer

app = FastAPI()

gesture_ai = GestureRecognizer()
voice_ai = VoiceRecognizer()

async def background_voice_task(websocket: WebSocket):
    """Runs voice recognition in a background loop."""
    loop = asyncio.get_event_loop()
    while True:
        # Run the blocking voice recognition in a separate thread so it doesn't freeze the video
        text = await loop.run_in_executor(None, voice_ai.listen_and_recognize)
        
        if text:
            print(f"Voice Command Detected: {text}")
            command_executed = False
            
            # Map voice commands to state changes
            if "light on" in text or "lights on" in text:
                room_state.update_light(True)
                command_executed = True
            elif "light off" in text or "lights off" in text:
                room_state.update_light(False)
                command_executed = True
            elif "fan speed 1" in text:
                room_state.set_fan_speed(1)
                command_executed = True
            elif "fan off" in text:
                room_state.set_fan_speed(0)
                command_executed = True

            # If a command was valid, broadcast the new state to the frontend
            if command_executed:
                await websocket.send_json({"type": "state_update", "data": room_state.get_state()})

        await asyncio.sleep(0.1)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection from the frontend
    await websocket.accept()
    
    # Send the initial room state
    await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
    
    # Start listening for voice commands simultaneously
    voice_task = asyncio.create_task(background_voice_task(websocket))

    try:
        while True:
            # Receive base64 encoded image frames from the frontend
            data = await websocket.receive_text()
            
            # Decode the base64 string into an OpenCV image
            img_data = base64.b64decode(data.split(",")[1] if "," in data else data)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Check for gestures
            gesture = gesture_ai.process_frame(frame)
            
            if gesture:
                command_executed = False
                
                # Map gestures to state changes
                if gesture == "OPEN_PALM" and not room_state.get_state()["light_on"]:
                    room_state.update_light(True)
                    command_executed = True
                elif gesture == "CLOSED_FIST" and room_state.get_state()["light_on"]:
                    room_state.update_light(False)
                    command_executed = True
                elif gesture == "POINTING_UP" and room_state.get_state()["fan_speed"] != 1:
                    room_state.set_fan_speed(1)
                    command_executed = True
                elif gesture == "PEACE_SIGN" and room_state.get_state()["fan_speed"] != 2:
                    room_state.set_fan_speed(2)
                    command_executed = True

                # Broadcast new state if a gesture changed something
                if command_executed:
                    print(f"Gesture Detected: {gesture}")
                    await websocket.send_json({"type": "state_update", "data": room_state.get_state()})

    except WebSocketDisconnect:
        print("Frontend client disconnected")
    finally:
        voice_task.cancel() # Stop the voice loop when the user disconnects