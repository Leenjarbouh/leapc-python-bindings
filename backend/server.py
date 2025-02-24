from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import threading
import sys
import os
import time  # Add this import
import traceback

# Add the leapc-cffi directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
leapc_cffi_dir = os.path.join(parent_dir, 'leapc-cffi')
sys.path.append(leapc_cffi_dir)

try:
    import leapc_cffi as leapc
except ImportError as e:
    print(f"Error importing leapc_cffi: {e}")
    print(f"Looking for leapc_cffi in: {leapc_cffi_dir}")
    sys.exit(1)

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:
    print("Error: spotipy not found. Please install it using:")
    print("pip install spotipy")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

class SpotifyController:
    def __init__(self):
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5
        self.last_hand_state = None
        self.last_status = 'inactive'
        self.current_volume = 50

        print("Initializing Spotify connection...")
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id="fcb16fa2fada495990afc54f6cf1fbaa",
                client_secret="f732c00d54d7451cb13f969b612a6bb8",
                redirect_uri="http://localhost:3000",
                scope="user-modify-playback-state user-read-playback-state"
            ))
            print("Spotify connection successful!")
        except Exception as e:
            print(f"Error connecting to Spotify: {e}")
            raise

        print("Initializing Leap Motion controller...")
        try:
            self.controller = self.init_leap_controller()
            print("Leap Motion controller initialized successfully!")
        except Exception as e:
            print(f"Error initializing Leap Motion: {e}")
            raise

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
        
        other_fingers_extended = all(hand.digits[i].is_extended for i in range(2, 5))
        distance = self.calculate_finger_distance(thumb, index)
        
        print(f"\nPinch detection:")  # Debug print
        print(f"Other fingers extended: {other_fingers_extended}")
        print(f"Thumb-index distance: {distance:.2f}mm")
        
        return distance < 30 and other_fingers_extended

    def handle_volume_control(self, hand, is_pinching):
        if is_pinching:
            if not hasattr(self, 'pinch_reference'):
                self.pinch_reference = {
                    'height': hand.palm.position.y,
                    'volume': self.current_volume
                }
                return

            height_diff = hand.palm.position.y - self.pinch_reference['height']
            volume_change = (height_diff / 200.0) * 100
            new_volume = round((self.pinch_reference['volume'] + volume_change) / 10.0) * 10
            new_volume = max(0, min(100, new_volume))
            
            if abs(new_volume - self.current_volume) >= 10:
                self.current_volume = new_volume
                try:
                    self.sp.volume(int(new_volume))
                except Exception as e:
                    print(f"Error setting volume: {e}")
        else:
            if hasattr(self, 'pinch_reference'):
                delattr(self, 'pinch_reference')

    def handle_spotify_action(self, action):
        try:
            print(f"\nExecuting Spotify action: {action}")  # Debug print
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
            self.last_status = 'inactive'
            return
        
        tracking_event = leapc.ffi.cast("LEAP_TRACKING_EVENT *", event.tracking_event)
        if tracking_event.nHands == 0:
            self.last_status = 'inactive'
            if hasattr(self, 'pinch_reference'):
                delattr(self, 'pinch_reference')
            return

        hand = tracking_event.pHands[0]
        current_time = time.time()

        # Update hand status
        self.last_status = self.get_hand_status(hand)

        # Check for pinch gesture
        is_pinching = self.is_pinch_gesture(hand)
        
        # Handle volume control
        self.handle_volume_control(hand, is_pinching)
        
        # Only process other gestures if not in volume control mode
        if not is_pinching and not hasattr(self, 'pinch_reference'):
            velocity_x = hand.palm.velocity.x
            fingers_extended = sum(1 for i in range(5) if hand.digits[i].is_extended)
            hand_closed = fingers_extended <= 2
            
            # Track swipe gestures
            if abs(velocity_x) > 800:  # Velocity threshold
                if not hasattr(self, 'swipe_start_time'):
                    self.swipe_start_time = current_time
                    self.swipe_direction = 1 if velocity_x > 0 else -1
            else:
                if hasattr(self, 'swipe_start_time'):
                    if (current_time - self.swipe_start_time >= 0.1 and 
                        current_time - self.last_gesture_time >= self.gesture_cooldown):
                        self.handle_spotify_action("next" if self.swipe_direction > 0 else "previous")
                        self.last_gesture_time = current_time
                    delattr(self, 'swipe_start_time')
                    delattr(self, 'swipe_direction')

            # Handle play/pause
            if current_time - self.last_gesture_time >= self.gesture_cooldown:
                if self.last_hand_state is None:
                    self.last_hand_state = hand_closed
                elif hand_closed != self.last_hand_state:
                    self.handle_spotify_action("pause" if hand_closed else "play")
                    self.last_hand_state = hand_closed
                    self.last_gesture_time = current_time

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

   
    def get_hand_status(self, hand):
        """
        Determine hand status based on position in the interaction box
        Returns:
        - 'active': Hand is in optimal position
        - 'warning': Hand is at the edge of the interaction box
        - 'inactive': Hand is out of bounds or not detected
        """
        # Get the hand position in the interaction box
        x = hand.palm.position.x
        y = hand.palm.position.y
        z = hand.palm.position.z
        
        # Define optimal interaction box dimensions (in mm)
        OPTIMAL_X = 150  # Width from center
        OPTIMAL_Y = 200  # Height from device
        OPTIMAL_Z = 200  # Depth from device
        
        # Define warning boundaries (1.5x optimal)
        WARNING_X = OPTIMAL_X * 1.5
        WARNING_Y = OPTIMAL_Y * 1.5
        WARNING_Z = OPTIMAL_Z * 1.5
        
        # Calculate normalized position ratios
        x_ratio = abs(x) / OPTIMAL_X
        y_ratio = abs(y) / OPTIMAL_Y
        z_ratio = abs(z) / OPTIMAL_Z
        
        # Get the maximum ratio to determine the furthest boundary violation
        max_ratio = max(x_ratio, y_ratio, z_ratio)
        
        # Print position for debugging
        print(f"\rHand position - X: {x:.1f}mm ({x_ratio:.2f}), "
            f"Y: {y:.1f}mm ({y_ratio:.2f}), "
            f"Z: {z:.1f}mm ({z_ratio:.2f})", end="")
        
        # Determine status based on position ratios
        if max_ratio <= 1.0:
            return 'active'  # Hand is within optimal bounds
        elif max_ratio <= 1.5:
            return 'warning'  # Hand is at the edge
        else:
            return 'inactive'  # Hand is out of bounds
    

controller = SpotifyController()

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        playback = controller.sp.current_playback()
        if playback:
            controller.current_volume = playback['device']['volume_percent']
            
        response = make_response(jsonify({
            'hand_status': controller.last_status,
            'current_volume': controller.current_volume,
            'is_pinching': hasattr(controller, 'pinch_reference'),
            'last_hand_state': controller.last_hand_state,
            
        }))
        return response
    except Exception as e:
        print(f"Error getting status: {e}")
        return make_response(jsonify({
            'hand_status': controller.last_status,
            'current_volume': controller.current_volume,
            'is_pinching': False,
            'last_hand_state': None
        }))

@app.route('/api/playback', methods=['GET'])
def get_playback():
    try:
        playback = controller.sp.current_playback()
        if playback and playback['item']:
            response = make_response(jsonify({
                'track': playback['item']['name'],
                'artist': playback['item']['artists'][0]['name'],
                'album_url': playback['item']['album']['images'][0]['url'] if playback['item']['album']['images'] else None,
                'is_playing': playback['is_playing'],
                'progress_ms': playback['progress_ms'],
                'duration_ms': playback['item']['duration_ms']
            }))
            return response
    except Exception as e:
        print(f"Error getting playback: {e}")
    return jsonify({'error': 'No active playback'})

def process_frames():
    print("Starting gesture processing...")
    while True:
        try:
            controller.process_frame()
            time.sleep(0.01)  # Small sleep to prevent CPU overuse
        except KeyboardInterrupt:
            print("\nGesture processing stopped by user")
            break
        except Exception as e:
            print(f"Error in frame processing: {str(e)}")
            print("Full error details:", traceback.format_exc())  # Add this line
            time.sleep(1)  # Longer sleep on error



@app.route('/api/queue', methods=['GET'])
def get_queue():
    try:
        # Get current playback to determine the current track
        current_playback = controller.sp.current_playback()
        if not current_playback:
            return jsonify({'error': 'No active playback'})

        # Get queue
        queue = controller.sp.queue()
        if not queue or 'queue' not in queue:
            return jsonify({'queue': []})

        # Format queue items
        formatted_queue = []
        for item in queue['queue']:
            formatted_queue.append({
                'name': item['name'],
                'artist': item['artists'][0]['name'] if item['artists'] else 'Unknown Artist',
                'duration_ms': item['duration_ms'],
                'album_art': item['album']['images'][-1]['url'] if item['album']['images'] else None,
                'id': item['id']  # Include track ID for better tracking
            })

        response = make_response(jsonify({
            'queue': formatted_queue,
            'current_track_id': current_playback['item']['id'] if current_playback['item'] else None
        }))
        return response
    except Exception as e:
        print(f"Error getting queue: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/start_playlist', methods=['POST'])
def start_playlist():
    try:
        # Get the playlist URI from the request
        playlist_uri = request.json.get('playlist_uri', "spotify:playlist:37i9dQZF1DZ06evO03FbPP")
        
        # Get available devices
        devices = controller.sp.devices()
        if not devices['devices']:
            return jsonify({'error': 'No available devices'})
            
        # Use the first available device
        device_id = devices['devices'][0]['id']
        
        # Start playback
        controller.sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        
        return jsonify({'success': True, 'message': 'Playlist started'})
    except Exception as e:
        print(f"Error starting playlist: {e}")
        return jsonify({'error': str(e)})
    
    # Add this to your server.py

@app.route('/api/spotify/init', methods=['GET'])
def init_spotify():
    try:
        # Check if Spotify is authenticated
        if not controller.sp.current_user():
            return jsonify({
                'status': 'error',
                'message': 'Not authenticated with Spotify'
            })

        # Get available devices
        devices = controller.sp.devices()
        if not devices['devices']:
            return jsonify({
                'status': 'error',
                'message': 'No available Spotify devices'
            })

        # Get the first available device
        device_id = devices['devices'][0]['id']

        # Start default playlist
        playlist_uri = "spotify:playlist:37i9dQZF1DZ06evO03FbPP"  # Your playlist URI
        controller.sp.start_playback(device_id=device_id, context_uri=playlist_uri)

        return jsonify({
            'status': 'success',
            'message': 'Spotify initialized successfully',
            'device': devices['devices'][0]['name']
        })
    except Exception as e:
        print(f"Error initializing Spotify: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/spotify/status', methods=['GET'])
def spotify_status():
    try:
        # Check if we can get the current user
        user = controller.sp.current_user()
        
        # Check devices
        devices = controller.sp.devices()
        active_device = next((device for device in devices['devices'] if device['is_active']), None)
        
        # Check current playback
        playback = controller.sp.current_playback()
        
        return jsonify({
            'status': 'success',
            'authenticated': True,
            'user': user['display_name'],
            'active_device': active_device['name'] if active_device else None,
            'is_playing': playback['is_playing'] if playback else False
        })
    except Exception as e:
        print(f"Error checking Spotify status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    import traceback  # Add this at the top with other imports
    
    try:
        # Initialize LeapC polling thread
        frame_thread = threading.Thread(target=process_frames)
        frame_thread.daemon = True
        frame_thread.start()
        
        # Run the Flask server
        print("Starting server on port 5001...")
        app.run(host='0.0.0.0', port=5001, debug=False)  # Set debug=False to avoid thread issues
    except Exception as e:
        print(f"Server error: {str(e)}")
        print("Full error details:", traceback.format_exc())