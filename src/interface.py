import tkinter as tk
from tkinter import ttk
import platform
from PIL import Image, ImageTk
import requests
from io import BytesIO

class LeapInterface(tk.Tk):
    def __init__(self):
        super().__init__()

        # Spotify colors
        self.BACKGROUND = '#121212'
        self.DARKER_BG = '#000000'
        self.LIGHTER_BG = '#282828'
        self.TEXT_COLOR = '#FFFFFF'
        self.SUBTEXT_COLOR = '#B3B3B3'
        self.ACCENT = '#1DB954'

        # Window setup
        self.title("Cookify")
        self.geometry("1000x800")
        self.configure(bg=self.BACKGROUND)
        
        if platform.system() == 'Darwin':
            self.tk.call('tk', 'scaling', 2.0)

        self.create_main_layout()

    def create_main_layout(self):
        # Main content area
        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=True, fill='both', padx=40, pady=30)

        # Album art
        self.album_frame = ttk.Frame(self.main_container)
        self.album_frame.pack(pady=20)
        
        self.album_canvas = tk.Canvas(self.album_frame,
                                    width=400,
                                    height=400,
                                    bg=self.LIGHTER_BG,
                                    highlightthickness=0)
        self.album_canvas.pack()

        # Track info
        self.track_name = ttk.Label(self.main_container,
                                  text="",
                                  font=('SF Pro Display', 24, 'bold'),
                                  foreground=self.TEXT_COLOR)
        self.track_name.pack(pady=(20, 5))

        self.artist_name = ttk.Label(self.main_container,
                                   text="",
                                   font=('SF Pro Display', 16),
                                   foreground=self.SUBTEXT_COLOR)
        self.artist_name.pack()

        # Player controls
        self.controls_frame = ttk.Frame(self.main_container)
        self.controls_frame.pack(pady=30)

        # Time and progress
        self.time_frame = ttk.Frame(self.controls_frame)
        self.time_frame.pack(fill='x', pady=(0, 20))

        self.current_time = ttk.Label(self.time_frame,
                                    text="0:00",
                                    font=('SF Pro Display', 12),
                                    foreground=self.SUBTEXT_COLOR)
        self.current_time.pack(side='left')

        self.progress_frame = ttk.Frame(self.time_frame)
        self.progress_frame.pack(fill='x', expand=True, padx=10)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill='x', expand=True)

        self.total_time = ttk.Label(self.time_frame,
                                  text="0:00",
                                  font=('SF Pro Display', 12),
                                  foreground=self.SUBTEXT_COLOR)
        self.total_time.pack(side='right')

        # Playback controls
        self.playback_frame = ttk.Frame(self.controls_frame)
        self.playback_frame.pack(pady=10)

        buttons = [
            ("previous", "⏮"),
            ("play", "⏸"),
            ("next", "⏭")
        ]

        for name, symbol in buttons:
            btn = tk.Label(self.playback_frame,
                         text=symbol,
                         font=('SF Pro Display', 20 if name != 'play' else 32),
                         fg=self.TEXT_COLOR,
                         bg=self.BACKGROUND,
                         padx=20)
            btn.pack(side='left', padx=10)
            
            if name == 'play':
                self.play_button = btn
                btn.configure(fg=self.ACCENT)

        # Volume control section
        self.volume_frame = ttk.Frame(self.controls_frame)
        self.volume_frame.pack(pady=(20, 0))
        
        # Create a container for volume controls to center them
        volume_container = ttk.Frame(self.volume_frame)
        volume_container.pack(expand=True)
        
        # Volume icon
        self.volume_icon = tk.Label(volume_container,
                                  text="🔊",
                                  font=('SF Pro Display', 16),
                                  fg=self.TEXT_COLOR,
                                  bg=self.BACKGROUND)
        self.volume_icon.pack(side='left', padx=(0, 10))
        
        # Volume progress bar
        self.volume_bar = ttk.Progressbar(
            volume_container,
            mode='determinate',
            length=200,
            style='Volume.Horizontal.TProgressbar'
        )
        self.volume_bar.pack(side='left')
        
        # Volume percentage
        self.volume_text = tk.Label(volume_container,
                                  text="50%",
                                  font=('SF Pro Display', 12),
                                  fg=self.SUBTEXT_COLOR,
                                  bg=self.BACKGROUND)
        self.volume_text.pack(side='left', padx=(10, 0))

        self.apply_styles()

    def apply_styles(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background=self.BACKGROUND)
        self.style.configure('TLabel', background=self.BACKGROUND)
        
        # Custom progress bar
        self.style.configure('Custom.Horizontal.TProgressbar',
                           troughcolor=self.LIGHTER_BG,
                           background=self.ACCENT,
                           thickness=4)
        
        # Volume progress bar style
        self.style.configure('Volume.Horizontal.TProgressbar',
                           troughcolor=self.LIGHTER_BG,
                           background=self.ACCENT,
                           thickness=3)

    def update_song_info(self, song_name, artist, album_url=None, duration=None):
        """Update track information and album art"""
        self.track_name.configure(text=song_name)
        self.artist_name.configure(text=artist)
        
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            self.total_time.configure(text=f"{minutes}:{seconds:02d}")
        
        if album_url:
            try:
                response = requests.get(album_url)
                img = Image.open(BytesIO(response.content))
                img = img.resize((400, 400), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.album_canvas.create_image(200, 200, image=photo)
                self.album_canvas.image = photo
            except Exception as e:
                print(f"Error loading album art: {e}")

    def update_play_state(self, is_playing):
        """Update play/pause button state"""
        self.play_button.configure(text="⏸" if is_playing else "▶")

    def update_status(self, status):
        """Update status message"""
        self.artist_name.configure(text=status)

    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar['value'] = progress * 100

    def update_time(self, current_time, total_time):
        """Update current time and total time displays"""
        current_min = int(current_time // 60)
        current_sec = int(current_time % 60)
        total_min = int(total_time // 60)
        total_sec = int(total_time % 60)
        
        self.current_time.configure(text=f"{current_min}:{current_sec:02d}")
        self.total_time.configure(text=f"{total_min}:{total_sec:02d}")

    def update_volume(self, volume_percent):
        """Update volume display"""
        self.volume_bar['value'] = volume_percent
        self.volume_text.configure(text=f"{int(volume_percent)}%")
        
        # Update volume icon based on level
        if volume_percent == 0:
            self.volume_icon.configure(text="🔇")
        elif volume_percent < 33:
            self.volume_icon.configure(text="🔈")
        elif volume_percent < 66:
            self.volume_icon.configure(text="🔉")
        else:
            self.volume_icon.configure(text="🔊")