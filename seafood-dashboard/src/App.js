import React, { useState, useEffect } from 'react';
// Import the fixed component instead of the original one
import LobsterInventoryAnalysis from './components/charts/LobsterInventoryAnalysis';
// Keep any other imports you have
import CrabPriceChart from './components/charts/CrabPriceChart';

// Keep the rest of your App.js the same

function App() {
  const [chartType, setChartType] = useState('lobsterInventory');
  const [isEmbedded, setIsEmbedded] = useState(false);
  
  useEffect(() => {
    // Check for window.chartConfig first
    if (window.chartConfig) {
      if (window.chartConfig.chart) {
        setChartType(window.chartConfig.chart);
        console.log('Using chart type from window.chartConfig:', window.chartConfig.chart);
      }
      
      if (window.chartConfig.embed) {
        setIsEmbedded(true);
        console.log('Embedded mode enabled from window.chartConfig');
      }
    } else {
      // Fallback to URL parameters
      const params = new URLSearchParams(window.location.search);
      const chartParam = params.get('chart');
      if (chartParam) {
        setChartType(chartParam);
        console.log('Using chart type from URL parameters:', chartParam);
      }
      
      const embedParam = params.get('embed');
      if (embedParam === 'true') {
        setIsEmbedded(true);
        console.log('Embedded mode enabled from URL parameters');
      }
    }
  }, []);

  // Render the appropriate chart based on the chartType
  const renderChart = () => {
    console.log('Rendering chart type:', chartType);
    
    switch (chartType) {
      case 'lobsterInventory':
        return <LobsterInventoryAnalysis />;
      case 'crabPrice':
        // For now, we'll just use our fixed lobster chart for all types
        return <LobsterInventoryAnalysis />;
      default:
        console.log('Unknown chart type, defaulting to lobsterInventory');
        return <LobsterInventoryAnalysis />;
    }
  };

  return (
    <div className="App">
      {!isEmbedded && (
        <header className="App-header">
          <h1>Seafood Analytics Dashboard</h1>
        </header>
      )}
      <div className="chart-wrapper" style={{ width: '100%', height: '100%' }}>
        {renderChart()}
      </div>
    </div>
  );
}

export default App;