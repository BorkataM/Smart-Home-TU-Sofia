class VirtualRoomState:
    DEFAULT_ROOM = "living_room"

    def __init__(self):
        base = {
            "light_on": False,
            "door_open": False,
            "door_locked": False,
            "oven_on": False,
            "iron_on": False,
            "window_open": False,
            "computer_on": False,
            "tv_on": False,
            "music_on": False,
            "ac_on": False,
            "ac_temp": 22,
            "fan_speed": 0  # 0 to 3
        }
        self.rooms = {
            "living_room": dict(base),
            "kitchen": dict(base),
            "bedroom": dict(base)
        }

    def ensure_room(self, room: str):
        if room not in self.rooms:
            self.rooms[room] = dict(self.rooms[self.DEFAULT_ROOM])

    def get_state(self, room: str = None):
        if room and room in self.rooms:
            return {room: self.rooms[room]}
        return self.rooms

    def set_device(self, room: str, key: str, value):
        self.ensure_room(room)
        if key in self.rooms[room]:
            if key == "ac_temp":
                self.rooms[room][key] = max(16, min(30, int(value)))
            elif key == "fan_speed":
                self.rooms[room][key] = max(0, min(3, int(value)))
            else:
                self.rooms[room][key] = bool(value)
        return self.rooms[room]

    def toggle_device(self, room: str, key: str):
        self.ensure_room(room)
        if key in self.rooms[room] and isinstance(self.rooms[room][key], bool):
            self.rooms[room][key] = not self.rooms[room][key]
        return self.rooms[room]

    def set_room(self, room: str, new_state: dict):
        self.ensure_room(room)
        for key, value in new_state.items():
            self.set_device(room, key, value)
        return self.rooms[room]

# Create a single instance to be used across the app
room_state = VirtualRoomState()