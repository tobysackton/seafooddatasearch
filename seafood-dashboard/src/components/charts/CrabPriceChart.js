import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { loadCsvData } from '../../utils/dataLoader';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const CrabPriceChart = () => {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [],
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // This path should point to your CSV file location
        const csvData = await loadCsvData('/data/species/crab/crab_price_visualization_2019_2025.csv');
        
        if (csvData && csvData.length > 0) {
          // Get your x-axis labels (e.g., dates or years)
          const labels = csvData.map(item => item.year || item.date || item.month);
          
          // Create dataset(s) based on your CSV structure
          // This is just an example - adjust according to your actual data
          const datasets = [{
            label: 'Crab Price Forecast',
            data: csvData.map(item => item.price || item.value),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }];
          
          setChartData({ labels, datasets });
        }
      } catch (error) {
        console.error('Error fetching or processing data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return <div>Loading chart data...</div>;
  }

  return (
    <div className="chart-container" style={{ width: '80%', margin: '0 auto' }}>
      <h2>Crab Price Forecast (2019-2025)</h2>
      <Line data={chartData} options={{
        responsive: true,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Crab Price Trends and Forecast'
          }
        }
      }} />
    </div>
  );
};

export default CrabPriceChart;