import asyncio
import cv2
import base64
import json
import numpy as np
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from Server.State.state import room_state
from Server.AI.gesture import GestureRecognizer
from Server.AI.voice import VoiceRecognizer

app = FastAPI()

gesture_ai = GestureRecognizer()
voice_ai = VoiceRecognizer()

def apply_command_text(text: str, room: str = "living_room"):
    t = text.lower()
    command_executed = False

    def apply(key, value):
        nonlocal command_executed
        room_state.set_device(room, key, value)
        command_executed = True

    if "light on" in t or "lights on" in t:
        apply("light_on", True)
    elif "light off" in t or "lights off" in t:
        apply("light_on", False)
    elif "open door" in t:
        apply("door_open", True)
        apply("door_locked", False)
    elif "close door" in t:
        apply("door_open", False)
    elif "lock door" in t:
        apply("door_locked", True)
    elif "unlock door" in t:
        apply("door_locked", False)
    elif "oven on" in t or "start oven" in t:
        apply("oven_on", True)
    elif "oven off" in t or "stop oven" in t:
        apply("oven_on", False)
    elif "iron on" in t or "start iron" in t:
        apply("iron_on", True)
    elif "iron off" in t or "stop iron" in t:
        apply("iron_on", False)
    elif "open window" in t:
        apply("window_open", True)
    elif "close window" in t:
        apply("window_open", False)
    elif "computer on" in t or "start computer" in t:
        apply("computer_on", True)
    elif "computer off" in t or "stop computer" in t:
        apply("computer_on", False)
    elif "tv on" in t or "start tv" in t:
        apply("tv_on", True)
    elif "tv off" in t or "stop tv" in t:
        apply("tv_on", False)
    elif "music on" in t or "play music" in t:
        apply("music_on", True)
    elif "music off" in t or "stop music" in t:
        apply("music_on", False)
    elif "ac on" in t or "start ac" in t or "air conditioning on" in t:
        apply("ac_on", True)
    elif "ac off" in t or "stop ac" in t or "air conditioning off" in t:
        apply("ac_on", False)
    elif "ac temp" in t:
        import re
        m = re.search(r"(\d{2})", t)
        if m:
            apply("ac_temp", int(m.group(1)))
    elif "fan off" in t or "stop fan" in t:
        apply("fan_speed", 0)
    elif "fan speed" in t or "fan" in t:
        import re
        m = re.search(r"(\d)", t)
        if m:
            speed = int(m.group(1))
            if 0 <= speed <= 3:
                apply("fan_speed", speed)

    return command_executed

async def background_voice_task(websocket: WebSocket, current_room):
    """Runs voice recognition in a background loop."""
    loop = asyncio.get_event_loop()
    while True:
        text = await loop.run_in_executor(None, voice_ai.listen_and_recognize)

        if text:
            if apply_command_text(text, room=current_room["value"]):
                await websocket.send_json({"type": "state_update", "data": room_state.get_state()})

        await asyncio.sleep(0.1)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection from the frontend
    await websocket.accept()
    
    # Send the initial room state
    await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
    
    # Track the current room selected in frontend (mutable dict for reference sharing)
    current_room = {"value": "living_room"}
    
    # Gesture debouncing
    last_gesture = None
    last_gesture_time = 0
    gesture_hold_time = 0.3  # Hold gesture for 300ms before triggering
    gesture_cooldown = 2.0  # Wait 2 seconds between gesture commands
    
    # Start listening for voice commands simultaneously
    voice_task = asyncio.create_task(background_voice_task(websocket, current_room))

    try:
        frame_count = 0
        while True:
            try:
                message = await websocket.receive()
            except RuntimeError:
                # Connection closed
                break
            
            # Handle both text and binary messages
            if "text" in message:
                data = message["text"]
            elif "bytes" in message:
                data = message["bytes"]
            else:
                continue
            
            # Count frames for debugging
            if isinstance(data, str) and data.startswith("data:image"):
                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"[Frames] Received {frame_count} frames so far")
                
                # Process frame for gesture recognition
                try:
                    # Data URL format: "data:image/jpeg;base64,XXXXX"
                    img_data = base64.b64decode(data.split(",")[1])
                    nparr = np.frombuffer(img_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        gesture = gesture_ai.process_frame(frame)
                        
                        # Debouncing: only act on gesture if held consistently
                        current_time = time.time()
                        
                        if gesture:
                            # If same gesture detected, track hold time
                            if gesture == last_gesture:
                                hold_duration = current_time - last_gesture_time
                                # Trigger command only if gesture held long enough and cooldown passed
                                if hold_duration > gesture_hold_time and (current_time - last_gesture_time) > gesture_cooldown:
                                    print(f"[Gesture Command] {gesture} held for {hold_duration:.2f}s")
                                    command_executed = False
                                    room = current_room["value"]

                                    if gesture == "OPEN_PALM":
                                        room_state.set_device(room, "light_on", True)
                                        command_executed = True
                                    elif gesture == "CLOSED_FIST":
                                        room_state.set_device(room, "light_on", False)
                                        command_executed = True
                                    elif gesture == "POINTING_UP":
                                        room_state.set_device(room, "oven_on", True)
                                        command_executed = True
                                    elif gesture == "PEACE_SIGN":
                                        room_state.set_device(room, "oven_on", False)
                                        command_executed = True

                                    if command_executed:
                                        await websocket.send_json({"type": "gesture_detected", "data": gesture})
                                        await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
                                        last_gesture_time = current_time  # Reset cooldown
                            else:
                                # New gesture detected, start tracking
                                last_gesture = gesture
                                last_gesture_time = current_time
                                print(f"[New Gesture] {gesture} detected")
                        else:
                            # No gesture, reset
                            last_gesture = None
                            
                except Exception as e:
                    print(f"ERROR processing gesture frame: {e}")
                continue

            # If frontend sends JSON-style commands, apply them
            if isinstance(data, str) and data.strip().startswith("{"):
                try:
                    payload = json.loads(data)
                    # Update current room if specified in payload
                    if "room" in payload:
                        current_room["value"] = payload["room"]
                    
                    if payload.get("type") == "room_change":
                        # Just update the room and continue
                        continue
                    elif payload.get("type") == "control":
                        room = payload.get("room", "living_room")
                        key = payload.get("device")
                        val = payload.get("value")
                        if key == "__voice__" and isinstance(val, str):
                            if apply_command_text(val, room=room):
                                await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
                            continue
                        if key is not None:
                            room_state.set_device(room, key, val)
                            await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
                            continue
                    elif payload.get("type") == "toggle":
                        room = payload.get("room", "living_room")
                        key = payload.get("device")
                        if key is not None:
                            room_state.toggle_device(room, key)
                            await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
                            continue
                    elif payload.get("type") == "gesture_test":
                        gesture = payload.get("data")
                        if gesture:
                            print(f"Gesture simulated: {gesture}")
                            command_executed = False
                            room = current_room["value"]
                            if gesture == "OPEN_PALM":
                                room_state.set_device(room, "light_on", True)
                                command_executed = True
                            elif gesture == "CLOSED_FIST":
                                room_state.set_device(room, "light_on", False)
                                command_executed = True
                            elif gesture == "POINTING_UP":
                                room_state.set_device(room, "oven_on", True)
                                command_executed = True
                            elif gesture == "PEACE_SIGN":
                                room_state.set_device(room, "oven_on", False)
                                command_executed = True
                            if command_executed:
                                await websocket.send_json({"type": "gesture_detected", "data": gesture})
                                await websocket.send_json({"type": "state_update", "data": room_state.get_state()})
                            continue
                except Exception as e:
                    print(f"Invalid command payload: {e}")
                    continue

            # Otherwise, treat received data as camera frame (gesture input)
            if isinstance(data, str):
                if not data.startswith("data:image"):
                    # Unknown text message
                    continue
            try:
                if isinstance(data, str) and data.startswith("data:image"):
                    # Data URL format: "data:image/jpeg;base64,XXXXX"
                    img_data = base64.b64decode(data.split(",")[1])
                elif isinstance(data, bytes):
                    img_data = data
                else:
                    continue
                    
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
            except Exception as e:
                print(f"ERROR decoding frame: {e}")
                continue

            try:
                gesture = gesture_ai.process_frame(frame)
            except Exception as e:
                print(f"ERROR processing gesture: {e}")
                continue
                
            if gesture:
                print(f"✓ Gesture: {gesture} in {current_room['value']}")
                command_executed = False
                room = current_room["value"]

                if gesture == "OPEN_PALM":
                    room_state.set_device(room, "light_on", True)
                    command_executed = True
                elif gesture == "CLOSED_FIST":
                    room_state.set_device(room, "light_on", False)
                    command_executed = True
                elif gesture == "POINTING_UP":
                    room_state.set_device(room, "oven_on", True)
                    command_executed = True
                elif gesture == "PEACE_SIGN":
                    room_state.set_device(room, "oven_on", False)
                    command_executed = True

                if command_executed:
                    print(f"Gesture Detected: {gesture}")
                    await websocket.send_json({"type": "gesture_detected", "data": gesture})
                    await websocket.send_json({"type": "state_update", "data": room_state.get_state()})

    except WebSocketDisconnect:
        print("Frontend client disconnected")
    finally:
        voice_task.cancel() # Stop the voice loop when the user disconnects

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)