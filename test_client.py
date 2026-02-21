import asyncio
import websockets
import cv2
import base64
import json

async def run_test():
    uri = "ws://127.0.0.1:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to the smart home server!")
            
            # Start the webcam
            cap = cv2.VideoCapture(0)
            
            async def listen_for_state_changes():
                while True:
                    try:
                        response = await websocket.recv()
                        print(f"\n💡 [ROOM STATE UPDATED]: {response}")
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed by server.")
                        break

            # Start listening for server updates in the background
            asyncio.create_task(listen_for_state_changes())
            
            print("📷 Sending camera frames and listening for voice... (Press Ctrl+C to stop)")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Compress and encode the frame just like a web browser would
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # Send the frame to the backend
                await websocket.send(f"data:image/jpeg;base64,{jpg_as_text}")
                
                # Send 10 frames per second
                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cap' in locals():
            cap.release()

if __name__ == "__main__":
    asyncio.run(run_test())