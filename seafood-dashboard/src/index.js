import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// For React 18 - use createRoot API
const rootElement = document.getElementById('root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// Add support for embedded charts via window.chartConfig
if (window.chartConfig && window.chartConfig.containerId) {
  const container = document.getElementById(window.chartConfig.containerId);
  if (container) {
    console.log('Mounting chart in container:', window.chartConfig.containerId);
    const embeddedRoot = createRoot(container);
    embeddedRoot.render(<App />);
  }
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();