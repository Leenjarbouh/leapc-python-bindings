import React, { useState, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, Shuffle, Repeat, Mic2, MonitorSpeaker, ListMusic } from 'lucide-react';

const HandStatusIndicator = ({ status }) => {
  const getStatusDetails = (status) => {
    switch (status) {
      case 'active':
        return {
          color: 'bg-green-500',
          text: 'Hand in Position',
          ringColor: 'ring-green-500/50'
        };
      case 'warning':
        return {
          color: 'bg-yellow-500',
          text: 'Hand at Edge',
          ringColor: 'ring-yellow-500/50'
        };
      default:
        return {
          color: 'bg-red-500',
          text: 'Hand Out of Range',
          ringColor: 'ring-red-500/50'
        };
    }
  };

  const { color, text, ringColor } = getStatusDetails(status);

  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2">
      <div className={`bg-zinc-900/90 px-6 py-3 rounded-full border border-zinc-800 shadow-xl 
                      ring-4 ${ringColor} transition-all duration-300`}>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${color} 
                          animate-pulse transition-colors duration-300`} />
          <span className="text-sm text-zinc-300">
            {text}
          </span>
        </div>
      </div>
    </div>
  );
};
const QueueList = () => {
  const [queue, setQueue] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/queue');
        const data = await response.json();
        if (!data.error) {
          setQueue(data.queue || []);
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return <div className="text-zinc-400">Loading queue...</div>;
  }

  return (
    <div className="space-y-2">
      {queue.map((track, index) => (
        <div 
          key={`${track.name}-${index}`}
          className="flex items-center space-x-3 p-2 rounded hover:bg-zinc-800/50 transition-colors group"
        >
          {track.album_art && (
            <img 
              src={track.album_art} 
              alt={track.name}
              className="w-10 h-10 rounded"
            />
          )}
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate group-hover:text-green-500">
              {track.name}
            </div>
            <div className="text-xs text-zinc-400 truncate">
              {track.artist}
            </div>
          </div>
          <div className="text-xs text-zinc-500">
            {Math.floor(track.duration_ms / 60000)}:
            {String(Math.floor((track.duration_ms % 60000) / 1000)).padStart(2, '0')}
          </div>
        </div>
      ))}
    </div>
  );
};

const MusicPlayer = () => {
  const [playbackState, setPlaybackState] = useState({
    track: '',
    artist: '',
    album_url: '',
    is_playing: false,
    progress_ms: 0,
    duration_ms: 0,
    description: '' // New field for optional description
  });
  const [handStatus, setHandStatus] = useState('inactive');
  const [volume, setVolume] = useState(50);
  const [isPinching, setIsPinching] = useState(false);
  const [gestureState, setGestureState] = useState({
    handClosed: false,
    swipeDirection: null
  });

  

  useEffect(() => {
    const fetchPlayback = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/playback');
        const data = await response.json();
        if (!data.error) {
          setPlaybackState(data);
        }
      } catch (error) {
        console.error('Error fetching playback:', error);
      }
    };

    const fetchHandStatus = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/status');
        const data = await response.json();
        if (!data.error) {
          setHandStatus(data.hand_status);
          setVolume(data.current_volume);
          setIsPinching(data.is_pinching);
          
          // Update playback state if hand state changed
          if (data.last_hand_state !== undefined && 
              data.last_hand_state !== gestureState.handClosed) {
            setGestureState(prev => ({
              ...prev,
              handClosed: data.last_hand_state
            }));
          }
        }
      } catch (error) {
        console.error('Error fetching hand status:', error);
      }
    };
    fetchPlayback();
    fetchHandStatus();

    const playbackInterval = setInterval(fetchPlayback, 1000);
    const statusInterval = setInterval(fetchHandStatus, 100);

    return () => {
      clearInterval(playbackInterval);
      clearInterval(statusInterval);
    };
  }, []);

  const formatTime = (ms) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black">
      {/* Main Content */}
      <div className="flex h-screen">
        {/* Left Sidebar */}
        <div className="w-64 bg-black p-6">
          <div className="space-y-4">
            <div className="text-white text-2xl font-bold">Cookify</div>
            <nav className="space-y-2">
              <button className="text-zinc-400 hover:text-white block py-2 w-full text-left">Home</button>
              <button className="text-zinc-400 hover:text-white block py-2 w-full text-left">Search</button>
              <button className="text-zinc-400 hover:text-white block py-2 w-full text-left">Your Library</button>
            </nav>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
          {/* Now Playing View */}
          <div className="p-8 flex flex-col items-center">
            {/* Album Art */}
            <img 
              src={playbackState.album_url || '/api/placeholder/400/400'} 
              alt="Album Cover"
              className="w-64 h-64 shadow-2xl rounded mb-4"
            />
            
            {/* Track Info */}
            <div className="text-center mb-4">
              <h1 className="text-5xl font-bold text-white mb-2">{playbackState.track}</h1>
              <p className="text-xl text-zinc-400 mb-2">{playbackState.artist}</p>
              {playbackState.description && (
                <p className="text-md text-zinc-500">
                  {playbackState.description}
                </p>
              )}
            </div>
            
            {/* Instructions */}
            <p className="text-white text-sm leading-relaxed max-w-2xl text-center">
              Welcome to Cookify. Swipe right to go to the next song, left to the previous song. 
              Close your palm to pause the music and open your palm to resume it. 
              Pinch your index finger and your thumb while keeping the other fingers open and 
              swipe vertically up to increase the volume and down to decrease it. 
              Let go of the pinching if you're satisfied with the volume!
            </p>
          </div>
        </div>

        {/* Right Sidebar - Queue */}
        <div className="w-96 bg-black p-6 overflow-y-auto">
          <h2 className="text-white text-xl font-bold mb-4">Queue</h2>
          <QueueList />
        </div>
      </div>

      {/* Playback Controls - Fixed Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 border-t border-zinc-800 backdrop-blur-sm">
        <div className="flex items-center justify-between px-4 py-3">
          {/* Track Info */}
          <div className="flex items-center space-x-4 w-72">
            <img 
              src={playbackState.album_url || '/api/placeholder/40/40'} 
              alt="Mini Album Art"
              className="w-14 h-14 rounded"
            />
            <div>
              <div className="text-sm text-white font-medium">{playbackState.track}</div>
              <div className="text-xs text-zinc-400">{playbackState.artist}</div>
            </div>
          </div>

          {/* Main Controls */}
          <div className="flex flex-col items-center max-w-2xl w-full">
            <div className="flex items-center space-x-6 mb-2">
              <Shuffle className="w-5 h-5 text-zinc-400 hover:text-white" />
              <SkipBack className="w-5 h-5 text-zinc-400 hover:text-white" />
              <button className="rounded-full bg-white p-2">
                {playbackState.is_playing ? (
                  <Pause className="w-6 h-6 text-black" />
                ) : (
                  <Play className="w-6 h-6 text-black ml-0.5" />
                )}
              </button>
              <SkipForward className="w-5 h-5 text-zinc-400 hover:text-white" />
              <Repeat className="w-5 h-5 text-zinc-400 hover:text-white" />
            </div>
            
            {/* Progress Bar */}
            <div className="flex items-center space-x-2 w-full">
              <span className="text-xs text-zinc-400 w-10 text-right">
                {formatTime(playbackState.progress_ms)}
              </span>
              <div className="flex-1 h-1 bg-zinc-800 rounded-full">
                <div 
                  className="h-full bg-white rounded-full hover:bg-green-500"
                  style={{ width: `${(playbackState.progress_ms / playbackState.duration_ms) * 100}%` }}
                />
              </div>
              <span className="text-xs text-zinc-400 w-10">
                {formatTime(playbackState.duration_ms)}
              </span>
            </div>
          </div>

          {/* Volume & Extra Controls */}
          <div className="flex items-center space-x-4 w-72 justify-end">
            <Mic2 className="w-5 h-5 text-zinc-400 hover:text-white" />
            <ListMusic className="w-5 h-5 text-zinc-400 hover:text-white" />
            <MonitorSpeaker className="w-5 h-5 text-zinc-400 hover:text-white" />
            <div className="flex items-center space-x-2">
              <Volume2 
                className={`w-5 h-5 ${isPinching ? 'text-green-500' : 'text-zinc-400'}`} 
              />
              <div className="w-24 h-1 bg-zinc-800 rounded-full">
                <div 
                  className={`h-full rounded-full transition-all duration-200 ${
                    isPinching ? 'bg-green-500' : 'bg-white hover:bg-green-500'
                  }`}
                  style={{ width: `${volume}%` }}
                />
              </div>
              <span className="text-xs text-zinc-400">{volume}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hand Status Indicator */}
      <HandStatusIndicator status={handStatus} />
    </div>
  );
};

export default MusicPlayer;