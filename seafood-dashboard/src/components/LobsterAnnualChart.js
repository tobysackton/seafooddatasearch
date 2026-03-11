import React from 'react';
import { 
  ComposedChart, 
  Bar, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

// Annual data for 2012-2024 period
const annualData = [
  {year: 2012, volume: 18584701, avg_price: 11.41, volume_millions: 18.58, total_value_millions: 212.08},
  {year: 2013, volume: 17849644, avg_price: 11.07, volume_millions: 17.85, total_value_millions: 197.63},
  {year: 2014, volume: 18185660, avg_price: 12.13, volume_millions: 18.19, total_value_millions: 220.55},
  {year: 2015, volume: 18704357, avg_price: 13.97, volume_millions: 18.70, total_value_millions: 261.21},
  {year: 2016, volume: 21847928, avg_price: 14.71, volume_millions: 21.85, total_value_millions: 321.33},
  {year: 2017, volume: 18111349, avg_price: 15.73, volume_millions: 18.11, total_value_millions: 284.88},
  {year: 2018, volume: 16422371, avg_price: 14.61, volume_millions: 16.42, total_value_millions: 239.95},
  {year: 2019, volume: 18817286, avg_price: 13.69, volume_millions: 18.82, total_value_millions: 257.68},
  {year: 2020, volume: 15353417, avg_price: 14.75, volume_millions: 15.35, total_value_millions: 226.48},
  {year: 2021, volume: 25459445, avg_price: 20.56, volume_millions: 25.46, total_value_millions: 523.45},
  {year: 2022, volume: 17943025, avg_price: 18.53, volume_millions: 17.94, total_value_millions: 332.53},
  {year: 2023, volume: 18337789, avg_price: 16.52, volume_millions: 18.34, total_value_millions: 302.93},
  {year: 2024, volume: 19691199, avg_price: 19.51, volume_millions: 19.69, total_value_millions: 384.17}
];

const LobsterAnnualChart = () => {
  const formatYAxis = (value) => `${value}`;
  const formatPrice = (value) => `$${value}`;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-volume">Volume: {payload[0].value.toLocaleString()} lbs</p>
          <p className="tooltip-price">Avg Price: ${payload[1].value.toFixed(2)}/lb</p>
          <p className="tooltip-value">Total Value: ${(payload[0].value * payload[1].value / 1000000).toFixed(2)} million</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-container">
      <h2>Canadian Lobster Meat Exports to the US (2012-2024)</h2>
      <p className="chart-description">Annual volume (bars) and average price (line)</p>
      
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={annualData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis 
              yAxisId="left" 
              orientation="left" 
              tickFormatter={formatYAxis}
              label={{ value: 'Volume (lbs)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              domain={[0, 25]}
              tickFormatter={formatPrice}
              label={{ value: 'Price ($/lb)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar 
              yAxisId="left" 
              dataKey="volume" 
              name="Volume (lbs)" 
              fill="#3182CE" 
              barSize={40}
            />
            <Line 
              yAxisId="right" 
              type="monotone" 
              dataKey="avg_price" 
              name="Avg Price ($/lb)" 
              stroke="#E53E3E" 
              strokeWidth={3}
              dot={{ r: 6 }}
              activeDot={{ r: 8 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      <div className="chart-insights">
        <h3>Key Observations</h3>
        <ul>
          <li>Notable price spike in 2021 ($20.56/lb) coinciding with highest volume (25.5M lbs)</li>
          <li>Price has generally trended upward from 2012 ($11.41/lb) to 2024 ($19.51/lb)</li>
          <li>2021 was an exceptional year with both highest volume and highest price</li>
          <li>Volume has remained relatively stable between 15-20M lbs except for peaks in 2016 and 2021</li>
          <li>Despite volume variations, prices have generally shown an upward trend</li>
        </ul>
      </div>
    </div>
  );
};

export default LobsterAnnualChart;