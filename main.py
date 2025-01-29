import leapc_cffi as leapc
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from enum import Enum

class SpotifyGestureController:
    def __init__(self):
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.0  
        self.last_hand_state = None
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="fcb16fa2fada495990afc54f6cf1fbaa",
            client_secret="f732c00d54d7451cb13f969b612a6bb8",
            redirect_uri="http://localhost:3000",
            scope="user-modify-playback-state user-read-playback-state"
        ))
        self.controller = self.init_leap_controller()

    def init_leap_controller(self):
        config = leapc.ffi.new("struct _LEAP_CONNECTION_CONFIG *")
        config.size = leapc.ffi.sizeof("struct _LEAP_CONNECTION_CONFIG")
        connection = leapc.ffi.new("LEAP_CONNECTION *")
        result = leapc.libleapc.LeapCreateConnection(config, connection)
        if result != 0:
            raise RuntimeError(f"Failed to create LeapC connection: {result}")
        result = leapc.libleapc.LeapOpenConnection(connection[0])
        if result != 0:
            raise RuntimeError(f"Failed to open LeapC connection: {result}")
        return connection[0]

    def handle_spotify_action(self, action):
        try:
            if action == "play":
                self.sp.start_playback()
                print("▶️ Playing")
            elif action == "pause":
                self.sp.pause_playback()
                print("⏸️ Paused")
            elif action == "next":
                self.sp.next_track()
                print("⏭️ Next track")
            elif action == "previous":
                self.sp.previous_track()
                print("⏮️ Previous track")
        except Exception as e:
            print(f"Spotify error: {e}")

    def process_frame(self):
        event = leapc.ffi.new("LEAP_CONNECTION_MESSAGE *")
        result = leapc.libleapc.LeapPollConnection(self.controller, 1000, event)
        
        if result != 0 or event.type != leapc.libleapc.eLeapEventType_Tracking:
            return

        tracking_event = leapc.ffi.cast("LEAP_TRACKING_EVENT *", event.tracking_event)
        if tracking_event.nHands == 0:
            return

        hand = tracking_event.pHands[0]
        
        
        velocity_x = hand.palm.velocity.x
        fingers_extended = sum(1 for i in range(5) if hand.digits[i].is_extended)
        hand_closed = fingers_extended <= 2
        current_time = time.time()

        print(f"\rFingers: {fingers_extended}, Velocity: {velocity_x:>6.1f}, {'CLOSED' if hand_closed else 'OPEN '}", end="")

        
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return
        

        
        if abs(velocity_x) > 800:  
            self.handle_spotify_action("next" if velocity_x > 0 else "previous")
            self.last_gesture_time = current_time
            return

        # Handle play/pause (hand open/close)
        if self.last_hand_state is None:
            self.last_hand_state = hand_closed
        elif hand_closed != self.last_hand_state:
            self.handle_spotify_action("pause" if hand_closed else "play")
            self.last_hand_state = hand_closed
            self.last_gesture_time = current_time

    def run(self):
        print("Starting gesture control. Press Ctrl+C to exit.")
        try:
            while True:
                self.process_frame()
                time.sleep(0.01)  
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    controller = SpotifyGestureController()
    playlist_uri = "spotify:playlist:4OZdhHHYS3YpjNP2GieUA4"
    devices = controller.sp.devices()
    if devices['devices']:
        active_device_id = devices['devices'][0]['id']
        controller.sp.start_playback(device_id=active_device_id, context_uri=playlist_uri)
        print("Starting playlist...")
    controller.run()
