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
        self.last_status = 'inactive'
        self.swipe_direction = None  # Add this line

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
    
    def get_hand_status(self, hand):
        """Determine hand status based on position"""
        # Get the hand position in the interaction box
        x = hand.palm.position.x
        y = hand.palm.position.y
        z = hand.palm.position.z
        
        # Define boundaries for the interaction box (in mm)
        X_LIMIT = 150  # More restrictive x limit
        Y_LIMIT = 150  # More restrictive y limit
        Z_LIMIT = 250  # More permissive z limit
        
        # Calculate distance from center of interaction box
        distance = (x*x + y*y + z*z) ** 0.5
        
        # Check if hand is in optimal position
        if abs(x) < X_LIMIT and y < Y_LIMIT and z < Z_LIMIT:
            return 'active'
        # Check if hand is near the edge but still usable
        elif abs(x) < X_LIMIT * 1.5 and y < Y_LIMIT * 1.5 and z < Z_LIMIT * 1.5:
            return 'warning'
        else:
            return 'inactive'

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

    def handle_spotify_action(self, action, value=None):
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
            elif action == "volume" and value is not None:
                volume = max(0, min(100, value))  
                self.sp.volume(volume)
                self.interface.update_volume(volume)
                print(f"🔊 Volume: {volume}%")
                
        except Exception as e:
            print(f"Spotify error: {e}")

    def update_playback_info(self):
        try:
        # Single API call to get current playback state
            current_playback = self.sp.current_playback()
        
            if current_playback and current_playback['item']:
                track = current_playback['item']
                album_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                duration_ms = track['duration_ms']
                progress_ms = current_playback['progress_ms']
            
            # Update main player info
                self.interface.update_song_info(
                track['name'],
                track['artists'][0]['name'],
                album_url,
                duration_ms / 1000
                )
                self.interface.update_progress(progress_ms / duration_ms)
                self.interface.update_time(progress_ms / 1000, duration_ms / 1000)
            
            # Update shuffle state if available
                #if 'shuffle_state' in current_playback:
                  #  self.interface.update_shuffle_state(current_playback['shuffle_state'])
            
            # Update queue less frequently (every 5 seconds)
                current_time = time.time()
                if not hasattr(self, 'last_queue_update') or current_time - self.last_queue_update >= 10.0:
                    try:
                        queue = self.sp.queue()
                        if queue and 'queue' in queue:
                            self.interface.update_queue(queue['queue'])
                        self.last_queue_update = current_time
                    except Exception as e:
                        print(f"Error updating queue: {e}")
                    
        except Exception as e:
            pass  # Silently handle any Spotify API errors
        
    #def toggle_shuffle(self):
     #   try:
        # Get current playback state
      #      playback = self.sp.current_playback()
      #      if playback:
            # Toggle shuffle state
       #         new_state = not playback['shuffle_state']
        #        self.sp.shuffle(new_state)
        #        print(f"🔀 Shuffle {'enabled' if new_state else 'disabled'}")
            # Update the interface
         #       self.interface.update_shuffle_state(new_state)
        #except Exception as e:
               # print(f"Shuffle error: {e}")
    

    def calculate_finger_distance(self, finger1, finger2):
        """Calculate the Euclidean distance between two finger tips in millimeters"""
        dx = finger1.distal.next_joint.x - finger2.distal.next_joint.x
        dy = finger1.distal.next_joint.y - finger2.distal.next_joint.y
        dz = finger1.distal.next_joint.z - finger2.distal.next_joint.z
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def is_pinch_gesture(self, hand):
        """Check if thumb and index are pinching while other fingers are extended"""
        thumb = hand.digits[0]
        index = hand.digits[1]
        
        # Check if other three fingers are extended
        other_fingers_extended = all(hand.digits[i].is_extended for i in range(2, 5))
        
        if not other_fingers_extended:
            return False
        
        # Calculate distance between thumb and index tips
        distance = self.calculate_finger_distance(thumb, index)
        
        # 30mm (3cm) threshold for pinch detection
        return distance < 30

    def handle_volume_control(self, hand, is_pinching):
        """
        Clutch-style volume control:
        - When pinch starts: record current hand height and volume
        - While pinching: adjust volume based on height difference
        - When pinch ends: maintain last volume
        """
        if is_pinching:
            # Initialize reference points if we just started pinching
            if not hasattr(self, 'pinch_reference'):
                self.pinch_reference = {
                    'height': hand.palm.position.y,
                    'volume': getattr(self, 'current_volume', 50)
                }
                print("\nVolume control engaged!")
                return

            # Calculate height difference from pinch start position
            height_diff = hand.palm.position.y - self.pinch_reference['height']
            
            # Scale the movement and round to nearest 10%
            volume_change = (height_diff / 200.0) * 100
            # Round to nearest 10%
            new_volume = round((self.pinch_reference['volume'] + volume_change) / 10.0) * 10
            new_volume = max(0, min(100, new_volume))
            
            # Only update if volume changed by 10%
            if abs(new_volume - getattr(self, 'current_volume', 0)) >= 10:
                self.current_volume = new_volume
                self.handle_spotify_action("volume", value=int(new_volume))
                
        else:
            # If we were previously pinching, clean up
            if hasattr(self, 'pinch_reference'):
                print("\nVolume control disengaged!")
                delattr(self, 'pinch_reference')

    def process_frame(self):
        event = leapc.ffi.new("LEAP_CONNECTION_MESSAGE *")
        result = leapc.libleapc.LeapPollConnection(self.controller, 1000, event)
        
        if result != 0 or event.type != leapc.libleapc.eLeapEventType_Tracking:
            # No hand detected
            if self.last_status != 'inactive':
                self.interface.update_hand_status('inactive')
                self.last_status = 'inactive'
            return
        
        tracking_event = leapc.ffi.cast("LEAP_TRACKING_EVENT *", event.tracking_event)
        if tracking_event.nHands == 0:
            # No hand detected
            if self.last_status != 'inactive':
                self.interface.update_hand_status('inactive')
                self.last_status = 'inactive'
            # Reset volume control state
            if hasattr(self, 'pinch_reference'):
                delattr(self, 'pinch_reference')
            return

        hand = tracking_event.pHands[0]
        current_time = time.time()

        # Update hand status for traffic light
        status = self.get_hand_status(hand)
        if status != self.last_status:
            self.interface.update_hand_status(status)
            self.last_status = status

        # Check for pinch gesture first
        is_pinching = self.is_pinch_gesture(hand)
        
        # Handle volume control with clutch behavior
        self.handle_volume_control(hand, is_pinching)
        
        # Only process other gestures if we're not in volume control mode
        if not is_pinching and not hasattr(self, 'pinch_reference'):
            velocity_x = hand.palm.velocity.x
            fingers_extended = sum(1 for i in range(5) if hand.digits[i].is_extended)
            hand_closed = fingers_extended <= 2
            
            # Original gesture handling code
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
            
            print(f"\rFingers: {fingers_extended}, Velocity: {velocity_x:>6.1f}, {'CLOSED' if hand_closed else 'OPEN '}", end="")
        else:
            # Show volume control status
            current_volume = getattr(self, 'current_volume', 0)
            print(f"\rVolume Control: {int(current_volume)}% {'[ACTIVE]' if is_pinching else '[RELEASED]'}", end="")

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
    playlist_uri = "spotify:playlist:37i9dQZF1DZ06evO03FbPP?si=fb191383fbc245d9"
    devices = controller.sp.devices()
    if devices['devices']:
        active_device_id = devices['devices'][0]['id']
        controller.sp.start_playback(device_id=active_device_id, context_uri=playlist_uri)
        print("Starting playlist...")
        # Update interface to show playing state immediately
        controller.interface.update_play_state(True)
        controller.run()