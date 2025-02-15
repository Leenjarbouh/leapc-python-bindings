import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

const SpotifyStatus = () => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initSpotify = async () => {
      try {
        // First check status
        const statusResponse = await fetch('http://localhost:5001/api/spotify/status');
        const statusData = await statusResponse.json();
        
        if (statusData.status === 'error') {
          setError(statusData.message);
          return;
        }
        
        setStatus(statusData);
        
        // If no active device or not playing, initialize
        if (!statusData.is_playing) {
          const initResponse = await fetch('http://localhost:5001/api/spotify/init');
          const initData = await initResponse.json();
          
          if (initData.status === 'error') {
            setError(initData.message);
          }
        }
      } catch (err) {
        setError('Failed to connect to Spotify server');
        console.error('Spotify initialization error:', err);
      }
    };

    initSpotify();
  }, []);

  if (error) {
    return (
      <div className="fixed top-6 right-6 bg-red-500/10 border border-red-500 text-red-500 px-4 py-2 rounded-lg flex items-center gap-2">
        <AlertCircle size={16} />
        <span>{error}</span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="fixed top-6 right-6 bg-green-500/10 border border-green-500 text-green-500 px-4 py-2 rounded-lg flex items-center gap-2">
      <CheckCircle size={16} />
      <span>Connected to Spotify ({status.user})</span>
    </div>
  );
};

export default SpotifyStatus;