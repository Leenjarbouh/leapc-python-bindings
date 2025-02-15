import tkinter as tk
from tkinter import ttk
import platform
from PIL import Image, ImageTk
import requests
from io import BytesIO

class HandStatusIndicator(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#121212')
        
        # Create a single indicator light
        self.indicator = tk.Canvas(
            self, 
            width=15,  # Smaller size
            height=15,  # Smaller size
            bg='#121212', 
            highlightthickness=0
        )
        self.indicator.pack(side='left', padx=5)
        
        # Create the indicator circle
        self.circle = self.indicator.create_oval(2, 2, 13, 13, fill='#404040')  # Gray by default
        
        # Add status text next to the light
        self.status_text = tk.Label(
            self,
            text="No Hand",
            font=('SF Pro Display', 10),  # Smaller font
            fg='#FFFFFF',
            bg='#121212'
        )
        self.status_text.pack(side='left', padx=5)
    
    def update_status(self, status):
        if status == 'active':
            color = '#2ECC40'  # Green
            text = "Hand Detected"
        elif status == 'warning':
            color = '#FFB700'  # Amber
            text = "Hand at Edge"
        else:  # inactive
            color = '#FF4136'  # Red
            text = "No Hand"
            
        self.indicator.itemconfig(self.circle, fill=color)
        self.status_text.config(text=text)
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
        self.geometry("1200x800")
        self.configure(bg=self.BACKGROUND)
        
        if platform.system() == 'Darwin':
            self.tk.call('tk', 'scaling', 2.0)

        self.create_main_layout()
        
        self.hand_status = HandStatusIndicator(self.player_frame)
        self.hand_status.pack(side='top', pady=10)  # Move to top
    
    def update_hand_status(self, status):
        """Update the hand status indicator
        status can be: 'active', 'warning', or 'inactive'
        """
        self.hand_status.update_status(status)

    def create_main_layout(self):
    # Split into left (player) and right (queue) panels
        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=True, fill='both', padx=20, pady=20)

    # Left panel - Player
        self.player_frame = ttk.Frame(self.main_container)
        self.player_frame.pack(side='left', padx=(0, 20), fill='both', expand=True)

    # Right panel - Queue
        self.queue_frame = ttk.Frame(self.main_container, width=300)  
        self.queue_frame.pack(side='right', fill='both', padx=(20, 0))
        self.queue_frame.pack_propagate(False)  

    # Queue header
        self.queue_header = ttk.Label(
            self.queue_frame,
            text="Queue",
            font=('SF Pro Display', 18, 'bold'),
            foreground=self.TEXT_COLOR
    )
        self.queue_header.pack(anchor='w', pady=(0, 10))

        
        self.queue_canvas = tk.Canvas(
            self.queue_frame,
            bg=self.BACKGROUND,
            highlightthickness=0
        )
        self.queue_canvas.pack(side='left', fill='both', expand=True)

        self.queue_scrollbar = ttk.Scrollbar(
            self.queue_frame,
            orient='vertical',
            command=self.queue_canvas.yview
        )
        self.queue_scrollbar.pack(side='right', fill='y')

        self.queue_list = ttk.Frame(self.queue_canvas)
        self.queue_canvas.create_window((0, 0), window=self.queue_list, anchor='nw')
        
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        self.queue_list.bind('<Configure>', lambda e: self.queue_canvas.configure(
            scrollregion=self.queue_canvas.bbox('all')
        ))

        # Create the player content
        self.create_player_content()
        self.apply_styles()

    def create_player_content(self):
        # Album art
        self.album_frame = ttk.Frame(self.player_frame)
        self.album_frame.pack(pady=20)
        
        self.album_canvas = tk.Canvas(
            self.album_frame,
            width=400,
            height=400,
            bg=self.LIGHTER_BG,
            highlightthickness=0
        )
        self.album_canvas.pack()

        # Track info
        self.track_name = ttk.Label(
            self.player_frame,
            text="",
            font=('SF Pro Display', 24, 'bold'),
            foreground=self.TEXT_COLOR
        )
        self.track_name.pack(pady=(20, 5))

        self.artist_name = ttk.Label(
            self.player_frame,
            text="",
            font=('SF Pro Display', 16),
            foreground=self.SUBTEXT_COLOR
        )
        self.artist_name.pack()

        # Controls section
        self.controls_frame = ttk.Frame(self.player_frame)
        self.controls_frame.pack(pady=30)

        # Time and progress
        self.time_frame = ttk.Frame(self.controls_frame)
        self.time_frame.pack(fill='x', pady=(0, 20))

        self.current_time = ttk.Label(
            self.time_frame,
            text="0:00",
            font=('SF Pro Display', 12),
            foreground=self.SUBTEXT_COLOR
        )
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

        self.total_time = ttk.Label(
            self.time_frame,
            text="0:00",
            font=('SF Pro Display', 12),
            foreground=self.SUBTEXT_COLOR
        )
        self.total_time.pack(side='right')

        # Playback controls
        self.playback_frame = ttk.Frame(self.controls_frame)
        self.playback_frame.pack(pady=10)

        # Add shuffle button
        #self.shuffle_button = tk.Label(
          #  self.playback_frame,
          #  text="🔀",
          #  font=('SF Pro Display', 20),
          #  fg=self.SUBTEXT_COLOR,
          #  bg=self.BACKGROUND,
           # padx=20
        #)
       #self.shuffle_button.pack(side='left', padx=10)

        buttons = [
            ("previous", "⏮"),
            ("play", "⏸"),
            ("next", "⏭")
        ]

        for name, symbol in buttons:
            btn = tk.Label(
                self.playback_frame,
                text=symbol,
                font=('SF Pro Display', 20 if name != 'play' else 32),
                fg=self.TEXT_COLOR,
                bg=self.BACKGROUND,
                padx=20
            )
            btn.pack(side='left', padx=10)
            
            if name == 'play':
                self.play_button = btn
                btn.configure(fg=self.ACCENT)

        # Volume control
        self.volume_frame = ttk.Frame(self.controls_frame)
        self.volume_frame.pack(pady=(20, 0))
        
        volume_container = ttk.Frame(self.volume_frame)
        volume_container.pack(expand=True)
        
        self.volume_icon = tk.Label(
            volume_container,
            text="🔊",
            font=('SF Pro Display', 16),
            fg=self.TEXT_COLOR,
            bg=self.BACKGROUND
        )
        self.volume_icon.pack(side='left', padx=(0, 10))
        
        self.volume_bar = ttk.Progressbar(
            volume_container,
            mode='determinate',
            length=200,
            style='Volume.Horizontal.TProgressbar'
        )
        self.volume_bar.pack(side='left')
        
        self.volume_text = tk.Label(
            volume_container,
            text="50%",
            font=('SF Pro Display', 12),
            fg=self.SUBTEXT_COLOR,
            bg=self.BACKGROUND
        )
        self.volume_text.pack(side='left', padx=(10, 0))

    def create_queue_item(self, title, artist, duration, album_art_url=None):
        item_frame = ttk.Frame(self.queue_list)
        item_frame.pack(fill='x', pady=2, padx=5)
    
    # Album art thumbnail
        if album_art_url:
            try:
                response = requests.get(album_art_url)
                img = Image.open(BytesIO(response.content))
                img = img.resize((40, 40), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                thumbnail = ttk.Label(item_frame, image=photo)
                thumbnail.image = photo
                thumbnail.pack(side='left', padx=(0, 10))
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
    
    # Info frame with fixed width
        info_frame = ttk.Frame(item_frame)
        info_frame.pack(side='left', fill='both', expand=True)
    
    # Title with ellipsis if too long
        title_label = ttk.Label(
        info_frame,
        text=title[:30] + ('...' if len(title) > 30 else ''),
        font=('SF Pro Display', 12),
        foreground=self.TEXT_COLOR,
        wraplength=200  # Set a maximum wrap length
        )
        title_label.pack(anchor='w')
    
    # Artist with ellipsis if too long
        artist_label = ttk.Label(
        info_frame,
        text=artist[:25] + ('...' if len(artist) > 25 else ''),
        font=('SF Pro Display', 10),
        foreground=self.SUBTEXT_COLOR
        )
        artist_label.pack(anchor='w')
    
    # Duration stays on the right
        duration_label = ttk.Label(
        item_frame,
        text=duration,
        font=('SF Pro Display', 12),
        foreground=self.SUBTEXT_COLOR
        )
        duration_label.pack(side='right', padx=10)
    
    # Add hover effect for the entire item
    def on_enter(e):
        item_frame.configure(style='Hover.TFrame')
        title_label.configure(foreground=self.ACCENT)
    
    def on_leave(e):
        item_frame.configure(style='TFrame')
        title_label.configure(foreground=self.TEXT_COLOR)
    
        item_frame.bind('<Enter>', on_enter)
        item_frame.bind('<Leave>', on_leave)

    def apply_styles(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background=self.BACKGROUND)
        self.style.configure('TLabel', background=self.BACKGROUND)
        
        self.style.configure('Custom.Horizontal.TProgressbar',
                           troughcolor=self.LIGHTER_BG,
                           background=self.ACCENT,
                           thickness=4)
        
        self.style.configure('Volume.Horizontal.TProgressbar',
                           troughcolor=self.LIGHTER_BG,
                           background=self.ACCENT,
                           thickness=3)
        self.style.configure('Hover.TFrame', background=self.LIGHTER_BG)

    def update_song_info(self, song_name, artist, album_url=None, duration=None):
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
        self.play_button.configure(text="⏸" if is_playing else "▶")

    def update_progress(self, progress):
        self.progress_bar['value'] = progress * 100

    def update_time(self, current_time, total_time):
        current_min = int(current_time // 60)
        current_sec = int(current_time % 60)
        total_min = int(total_time // 60)
        total_sec = int(total_time % 60)
        
        self.current_time.configure(text=f"{current_min}:{current_sec:02d}")
        self.total_time.configure(text=f"{total_min}:{total_sec:02d}")

    def update_volume(self, volume_percent):
        self.volume_bar['value'] = volume_percent
        self.volume_text.configure(text=f"{int(volume_percent)}%")
        
        if volume_percent == 0:
            self.volume_icon.configure(text="🔇")
        elif volume_percent < 33:
            self.volume_icon.configure(text="🔈")
        elif volume_percent < 66:
            self.volume_icon.configure(text="🔉")
        else:
            self.volume_icon.configure(text="🔊")

    def update_shuffle_state(self, is_shuffle_on):
        self.shuffle_button.configure(fg=self.ACCENT if is_shuffle_on else self.SUBTEXT_COLOR)

    def update_queue(self, queue_items):
        for widget in self.queue_list.winfo_children():
            widget.destroy()
        
        for item in queue_items:
            self.create_queue_item(
                title=item['name'],
                artist=item['artists'][0]['name'],
                duration=self.format_duration(item['duration_ms']),
                album_art_url=item['album']['images'][-1]['url'] if item['album']['images'] else None
            )

    def format_duration(self, ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    