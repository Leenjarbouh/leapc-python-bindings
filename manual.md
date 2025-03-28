User Manual
Cookify: Gesture-Controlled Spotify Player
Welcome to Cookify, the hands-free solution for controlling your Spotify playback using intuitive hand gestures. This manual guides you through setting up and using the application.

Getting Started
First-Time Setup

After installing and building the application (see README.md):

Start the backend server: python server.py in the backend directory
Start the frontend application: npm start in the frontend directory

On first launch, you'll need to authenticate with Spotify:

A browser window will open for Spotify login
Grant the necessary permissions to Cookify
You'll be redirected back to the application once authentication is complete

Position your Leap Motion device:

Place it on a flat surface, ideally at the center of your workspace
Ensure there's clear space above the device for hand movements
The sensor should be pointing upward

Make sure a Spotify device is active:

Open Spotify on your computer, phone, or smart speaker
Start playing any track to activate the device
Cookify will connect to your active device

Interface Overview
Web Application Interface
The web interface is divided into three main sections:

Left Sidebar:
Navigation options (Home, Search, Library)
These are visual elements only in the current version

Main Content Area:
Displays welcome message and gesture instructions
Shows current playback status

Right Sidebar:
Shows the current queue of upcoming tracks
Displays the currently playing track at the top

Bottom Control Bar:
Displays current track information
Shows playback controls
Includes volume slider and progress bar

Hand Status Indicator:
A colored indicator at the bottom of the screen
Shows the current status of hand tracking

Gesture Controls:
Cookify recognizes the following hand gestures:
Basic Controls

Play/Pause:
Open Hand: Spread your fingers with palm facing down to play music
Closed Fist: Close your hand into a fist to pause playback

Skip Tracks:
Swipe Right: Move your hand quickly from left to right to play the next track
Swipe Left: Move your hand quickly from right to left to play the previous track

Volume Control:
Pinch Gesture: Pinch your thumb and index finger together while keeping other fingers extended
Move Up/Down: While pinching, move your hand up to increase volume or down to decrease volume
Release the pinch to set the volume at the current level

Advanced Tips:
For swipe gestures, make smooth, deliberate movements across the sensor
For best recognition, maintain a stable hand position before attempting gestures
Allow a brief pause between gestures for the system to recognize each action
Volume control uses a "clutch" mechanism - pinch to engage, move to adjust, release to set

Hand Positioning Guide
The hand status indicator provides real-time feedback on your hand position:

Green: Hand is in optimal position for gesture detection:
Keep your hand 15-20 cm (6-8 inches) above the sensor
Center your palm over the sensor
Fingers should be within the sensor's field of view

Yellow: Hand is at the edge of detection range:
Move your hand more toward the center of the sensor
Adjust height if needed
Ensure your entire hand is visible to the sensor

Red: No hand detected or hand is out of range:
Check that your hand is above the sensor
Ensure there are no obstructions
Verify the Leap Motion controller is connected and working

Troubleshooting
Gesture Recognition Issues

Gestures not detected:
Ensure your hand is within the optimal detection zone (green status)
Move slower and make more deliberate gestures
Check lighting conditions - avoid direct sunlight on the sensor
Restart the Leap Motion service if problems persist

Inconsistent volume control:
Make sure to fully extend your other fingers during the pinch gesture
Move your hand up/down slowly for more precise control
Stay within the green detection zone

Connection Issues

Spotify not connecting:
Verify your Spotify Premium subscription is active
Ensure you have an active Spotify playback device
Check that your client ID and secret are correctly entered
Try logging out and back into Spotify

Leap Motion not detected:
Verify the Ultraleap service is running
Reconnect the Leap Motion device
Try using the Ultraleap Visualizer to confirm device functionality
Reinstall the Ultraleap drivers if needed
