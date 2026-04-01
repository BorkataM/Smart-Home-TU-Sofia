const wsUrl = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.hostname || "127.0.0.1";
const wsPort = 8000;
const wsPath = "/ws";
const wsStatusEl = document.getElementById("ws-status");
const cameraStatusEl = document.getElementById("camera-status");
const gestureStatusEl = document.getElementById("gesture-status");
const stateJsonEl = document.getElementById("state-json");
const roomSelect = document.getElementById("room-select");
let socket;
let stream;

function setStatus(text) {
    wsStatusEl.textContent = text;
}

function setCameraStatus(text) {
    if (cameraStatusEl) cameraStatusEl.textContent = text;
}

function renderState(state) {
    stateJsonEl.textContent = JSON.stringify(state, null, 2);
    renderRoomVisualization(state);
}

function renderRoomVisualization(state) {
    const cards = document.getElementById('room-cards');
    if (!cards) return;

    cards.innerHTML = '';

    for (const [roomName, roomState] of Object.entries(state)) {
        const card = document.createElement('div');
        card.className = 'room-card';

        const title = document.createElement('h3');
        title.textContent = roomName.replace('_', ' ').toUpperCase();
        card.appendChild(title);

        const features = [
            ['Light', 'light_on'],
            ['Door Open', 'door_open'],
            ['Door Locked', 'door_locked'],
            ['Oven', 'oven_on'],
            ['Iron', 'iron_on'],
            ['Window Open', 'window_open'],
            ['PC', 'computer_on'],
            ['TV', 'tv_on'],
            ['Music', 'music_on'],
            ['AC', 'ac_on']
        ];

        features.forEach(([label, key]) => {
            const row = document.createElement('div');
            row.className = 'room-feature';
            const name = document.createElement('span');
            name.textContent = label;
            const value = document.createElement('span');
            value.className = 'status ' + (roomState[key] ? 'on' : 'off');
            value.textContent = typeof roomState[key] === 'number' ? roomState[key] : (roomState[key] ? 'ON' : 'OFF');
            row.appendChild(name);
            row.appendChild(value);
            card.appendChild(row);
        });

        const acRow = document.createElement('div');
        acRow.className = 'room-feature';
        acRow.innerHTML = '<span>AC Temp</span><span class="status on">' + roomState.ac_temp + '°C</span>';
        card.appendChild(acRow);

        const fanRow = document.createElement('div');
        fanRow.className = 'room-feature';
        fanRow.innerHTML = '<span>Fan Speed</span><span class="status ' + (roomState.fan_speed > 0 ? 'on' : 'off') + '">' + roomState.fan_speed + '</span>';
        card.appendChild(fanRow);

        cards.appendChild(card);
    }
}

function sendCommand(payload) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket is not open");
        return;
    }
    socket.send(JSON.stringify(payload));
}

function toggleDevice(device) {
    sendCommand({ type: "toggle", room: roomSelect.value, device });
}

function setDevice(device, value) {
    sendCommand({ type: "control", room: roomSelect.value, device, value });
}

function startCameraLoop() {
    const video = document.getElementById("camera");
    const canvas = document.getElementById("capture-canvas");
    if (!video || !canvas) {
        console.warn("Camera loop aborted: element not found.");
        return;
    }

    const ctx = canvas.getContext("2d");

    const sendFrame = async () => {
        if (!socket || socket.readyState !== WebSocket.OPEN || !video.videoWidth || !video.videoHeight) return;
        try {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.6));
            const reader = new FileReader();
            reader.onloadend = () => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(reader.result);
                }
            };
            reader.readAsDataURL(blob);
        } catch (e) {
            console.warn("Failed to send camera frame:", e);
        }
    };

    setInterval(sendFrame, 150);
}

async function setupCamera() {
    const video = document.getElementById("camera");
    if (!video) {
        console.warn("No camera element available.");
        setCameraStatus("Camera element missing");
        return;
    }

    setCameraStatus("Requesting camera...");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraStatus("Camera API not supported");
        console.error("No camera API available.");
        return;
    }

    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cams = devices.filter((d) => d.kind === "videoinput");
        console.log("Video devices found", cams);
        if (cams.length === 0) {
            setCameraStatus("No camera devices found");
            return;
        }

        const constraints = {
            video: { deviceId: cams[0].deviceId },
            audio: false
        };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;

        await new Promise((resolve) => {
            video.onloadedmetadata = resolve;
        });

        setCameraStatus("Camera ready");
        startCameraLoop();

    } catch (err) {
        console.error("Camera access error", err);
        if (err.name === "NotAllowedError" || err.name === "SecurityError") {
            setCameraStatus("Camera permission denied");
        } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
            setCameraStatus("Camera busy / not available");
        } else {
            setCameraStatus("Camera error: " + err.message);
        }
    }
}

function initWebSocket() {
    const fullWsUrl = `${wsUrl}://${wsHost}:${wsPort}${wsPath}`;
    console.log("Connecting WebSocket:", fullWsUrl);

    socket = new WebSocket(fullWsUrl);

    socket.onopen = () => {
        setStatus("Connected");
        console.log("WebSocket opened");
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === "state_update") {
                renderState(msg.data);
            } else if (msg.type === "gesture_detected") {
                gestureStatusEl.textContent = msg.data;
                setTimeout(() => { if (gestureStatusEl.textContent === msg.data) gestureStatusEl.textContent = 'None'; }, 1500);
            }
        } catch (err) {
            console.log("Non-JSON message", event.data);
        }
    };

    socket.onclose = (event) => {
        console.warn(`WebSocket closed (code=${event.code} reason=${event.reason})`);
        setStatus("Disconnected");
        setTimeout(initWebSocket, 2000);
    };

    socket.onerror = (err) => {
        console.error("WebSocket error", err);
        setStatus("Error");
    };
}

document.addEventListener("DOMContentLoaded", () => {
    initWebSocket();
    setupCamera();

    document.getElementById("refresh-state").addEventListener("click", () => {
        sendCommand({ type: "control", room: roomSelect.value, device: "light_on", value: false });
        setTimeout(() => sendCommand({ type: "control", room: roomSelect.value, device: "light_on", value: false }), 50);
    });

    document.querySelectorAll(".toggle-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            toggleDevice(btn.dataset.device);
        });
    });

    document.getElementById("set-ac-temp").addEventListener("click", () => {
        const t = parseInt(document.getElementById("ac-temp").value, 10);
        setDevice("ac_temp", Math.min(30, Math.max(16, t)));
    });

    document.getElementById("send-voice").addEventListener("click", () => {
        const text = document.getElementById("voice-text").value.trim().toLowerCase();
        if (!text) return;
        sendCommand({ type: "control", room: roomSelect.value, device: "__voice__", value: text });
        document.getElementById("voice-text").value = "";
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            const spoken = event.results[0][0].transcript.toLowerCase();
            console.log('Spoken command:', spoken);
            document.getElementById('voice-text').value = spoken;
            setStatus('Voice recognized: ' + spoken);
            sendCommand({ type: 'control', room: roomSelect.value, device: '__voice__', value: spoken });
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            setStatus('Voice error: ' + event.error);
        };

        recognition.onend = () => {
            document.getElementById('start-voice-listen').textContent = 'Start Voice Listen';
        };

        document.getElementById('start-voice-listen').addEventListener('click', () => {
            try {
                recognition.start();
                setStatus('Listening...');
                document.getElementById('start-voice-listen').textContent = 'Stop Voice Listen';
            } catch (err) {
                console.warn('Recognition start error', err);
            }
        });

    document.getElementById('simulate-open-palm').addEventListener('click', () => {
        sendCommand({ type: 'gesture_test', data: 'OPEN_PALM' });
    });
    document.getElementById('simulate-closed-fist').addEventListener('click', () => {
        sendCommand({ type: 'gesture_test', data: 'CLOSED_FIST' });
    });
    document.getElementById('simulate-pointing-up').addEventListener('click', () => {
        sendCommand({ type: 'gesture_test', data: 'POINTING_UP' });
    });
    document.getElementById('simulate-peace-sign').addEventListener('click', () => {
        sendCommand({ type: 'gesture_test', data: 'PEACE_SIGN' });
    });
    } else {
        document.getElementById('start-voice-listen').disabled = true;
        document.getElementById('start-voice-listen').textContent = 'Voice not supported';
        console.warn('SpeechRecognition API is not supported in this browser.');
    }
});
