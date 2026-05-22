import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { initTheme } from './stores/theme';
import './index.css';

// Bootstrap theme BEFORE first paint so the user doesn't see a flash.
initTheme();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
