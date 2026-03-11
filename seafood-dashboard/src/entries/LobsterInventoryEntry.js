import React from 'react';
import ReactDOM from 'react-dom';
import LobsterInventoryAnalysis from '../components/charts/LobsterInventoryAnalysis';

document.addEventListener('DOMContentLoaded', function() {
  const container = document.getElementById('lobster-chart-container');
  if (container) {
    ReactDOM.render(<LobsterInventoryAnalysis />, container);
  }
});