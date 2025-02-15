// App.jsx
import React from 'react';
import MusicPlayer from './components/MusicPlayer';
import SpotifyStatus from './components/SpotifyStatus';

const App = () => {
  return (
    <div className="min-h-screen bg-black">
      <SpotifyStatus />
      <MusicPlayer />
    </div>
  );
};

export default App;