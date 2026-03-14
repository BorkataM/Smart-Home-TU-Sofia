class VirtualRoomState:
    def __init__(self):
        # Simulated functions: Light and Fan
        self.state = {
            "light_on": False,
            "fan_speed": 0 # 0 to 3
        }

    def update_light(self, status: bool):
        self.state["light_on"] = status
        return self.state

    def set_fan_speed(self, speed: int):
        self.state["fan_speed"] = max(0, min(3, speed))
        return self.state

    def get_state(self):
        return self.state

# Create a single instance to be used across the app
room_state = VirtualRoomState()