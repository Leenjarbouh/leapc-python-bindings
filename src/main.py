import leapc_cffi as leapc
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from enum import Enum
from interface import LeapInterface
import sys

class SpotifyGestureController:
    def __init__(self):
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  
        self.last_hand_state = None
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="fcb16fa2fada495990afc54f6cf1fbaa",
            client_secret="f732c00d54d7451cb13f969b612a6bb8",
            redirect_uri="http://localhost:3000",
            scope="user-modify-playback-state user-read-playback-state"
        ))
        self.controller = self.init_leap_controller()
        
        # Initialize interface
        self.interface = LeapInterface()
        self.interface.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

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
                self.interface.update_play_state(True)
            elif action == "pause":
                self.sp.pause_playback()
                print("⏸️ Paused")
                self.interface.update_play_state(False)
            elif action == "next":
                self.sp.next_track()
                print("⏭️ Next track")
            elif action == "previous":
                self.sp.previous_track()
                print("⏮️ Previous track")
            elif action == "volume":
                volume = max(0, min(100, value))  
                self.sp.volume(volume)
                self.interface.update_volume(volume)
                print(f"🔊 Volume: {volume}%")
                
        except Exception as e:
            print(f"Spotify error: {e}")

    def update_playback_info(self):
        try:
            current_playback = self.sp.current_playback()
            if current_playback and current_playback['item']:
                track = current_playback['item']
                album_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                duration_ms = track['duration_ms']
                progress_ms = current_playback['progress_ms']
                
                self.interface.update_song_info(
                    track['name'],
                    track['artists'][0]['name'],
                    album_url,
                    duration_ms / 1000
                )
                self.interface.update_progress(progress_ms / duration_ms)
                self.interface.update_time(progress_ms / 1000, duration_ms / 1000)
        except Exception as e:
            pass

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
    
        self.velocity_history = getattr(self, 'velocity_history', [])
        self.velocity_history.append(velocity_x)
        if len(self.velocity_history) > 5:  
            self.velocity_history.pop(0)
    
        avg_velocity = sum(self.velocity_history) / len(self.velocity_history)
    
        VELOCITY_THRESHOLD = 800  
        MIN_GESTURE_DURATION = 0.1  
    # Track the start of a potential swipe
        if abs(avg_velocity) > VELOCITY_THRESHOLD:
            if not hasattr(self, 'swipe_start_time'):
                self.swipe_start_time = current_time
                self.swipe_direction = 1 if avg_velocity > 0 else -1
        else:
            if hasattr(self, 'swipe_start_time'):
            # Check if the swipe was maintained long enough
                if (current_time - self.swipe_start_time >= MIN_GESTURE_DURATION and 
                    current_time - self.last_gesture_time >= self.gesture_cooldown):
                    self.handle_spotify_action("next" if self.swipe_direction > 0 else "previous")
                    self.last_gesture_time = current_time
                delattr(self, 'swipe_start_time')
                delattr(self, 'swipe_direction')

    # Handle play/pause with minimal delay
        if current_time - self.last_gesture_time >= self.gesture_cooldown:
            if self.last_hand_state is None:
                self.last_hand_state = hand_closed
            elif hand_closed != self.last_hand_state:
                self.handle_spotify_action("pause" if hand_closed else "play")
                self.last_hand_state = hand_closed
                self.last_gesture_time = current_time

    def run(self):
        print("Starting gesture control. Press Ctrl+C to exit.")
        last_update = 0
        try:
            while True:
                self.process_frame()
                
                # Update interface less frequently
                current_time = time.time()
                if current_time - last_update >= 1.0:
                    self.update_playback_info()
                    last_update = current_time
                
                self.interface.update()
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    controller = SpotifyGestureController()
    playlist_uri = "spotify:playlist:37i9dQZF1DX8qqIDAkKiQg?si=0ec542b8c5bd42dc"
    devices = controller.sp.devices()
    if devices['devices']:
        active_device_id = devices['devices'][0]['id']
        controller.sp.start_playback(device_id=active_device_id, context_uri=playlist_uri)
        print("Starting playlist...")
        # Update interface to show playing state immediately
        controller.interface.update_play_state(True)
        controller.run()