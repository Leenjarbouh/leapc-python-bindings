Cookify: Interaction for Music Exploration
A hands-free music control system that uses Leap Motion hand tracking to control Spotify playback. Use natural gestures to play, pause, skip tracks, and adjust volume without touching any physical control

The project consists of two main components:
Backend (Python): Handles Leap Motion tracking and Spotify API integration
Frontend (React): Provides a responsive web interface

Build instructions
Requirements

Python 3.8+
Node.js 14+
Spotify Premium account
Leap Motion Controller hardware
Ultraleap Gemini tracking software installed and running
Python packages:

Flask
Flask-CORS
spotipy
Pillow (PIL)
leapc_cffi


Tested on macOS
Build steps:

Install Leap Motion Software
Download and install Ultraleap Gemini tracking software
Connect your Leap Motion device
Verify it works using the Ultraleap Visualizer


Set up Spotify Developer credentials
Create an application at Spotify Developer Dashboard
Note your client_id and client_secret
Add http://localhost:3000 as a redirect URI


Backend setup
Navigate to the backend directory: cd backend
Create a virtual environment: python -m venv venv
Activate the virtual environment:

Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate

Install requirements: pip install flask flask-cors spotipy Pillow leapc_cffi
Update Spotify credentials in server.py with your own client ID and secret

Frontend setup
Navigate to the frontend directory: cd frontend
Install dependencies: npm install


Test steps

Start the backend server:
Navigate to the backend directory: cd backend
Run: python server.py
The server should start on http://localhost:5001

Start the frontend application:
In a new terminal, navigate to the frontend directory: cd frontend
Run: npm start
The application should open in your browser at http://localhost:3000

Alternatively, test the standalone application:
Navigate to the backend directory: cd backend
Run: python main.py
A Tkinter window should appear with the Cookify interface


Test the gesture controls:
Position your hand above the Leap Motion device
Open palm: Play music
Closed fist: Pause music
Swipe right: Next track
Swipe left: Previous track
Pinch and move up/down: Adjust volume
