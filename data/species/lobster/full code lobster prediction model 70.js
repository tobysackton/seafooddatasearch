import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area } from 'recharts';

const LobsterPricePredictionModel = () => {
  const [activeTab, setActiveTab] = useState('chart');
  
  // Helper function to format price
  const formatPrice = (value) => `$${Number(value).toFixed(2)}`;
  
  // Full visualization data from our analysis (complete dataset 2012-2023)
  const fullData = [
    {"date":"2012-01","actual":5.7,"predicted":6.77,"lower":4.14,"upper":9.41},
    {"date":"2012-02","actual":6.64,"predicted":8.33,"lower":5.69,"upper":10.97},
    {"date":"2012-03","actual":7.42,"predicted":8.45,"lower":5.81,"upper":11.09},
    {"date":"2012-04","actual":7.08,"predicted":8.20,"lower":5.56,"upper":10.84},
    {"date":"2012-05","actual":6.32,"predicted":6.61,"lower":3.97,"upper":9.25},
    {"date":"2012-06","actual":5.91,"predicted":5.31,"lower":2.67,"upper":7.95},
    {"date":"2012-07","actual":3.96,"predicted":5.11,"lower":2.47,"upper":7.75},
    {"date":"2012-08","actual":3.94,"predicted":5.52,"lower":2.88,"upper":8.16},
    {"date":"2012-09","actual":4.29,"predicted":5.98,"lower":3.34,"upper":8.62},
    {"date":"2012-10","actual":4.07,"predicted":6.34,"lower":3.70,"upper":8.98},
    {"date":"2012-12","actual":4.40,"predicted":5.01,"lower":2.37,"upper":7.65},
    {"date":"2013-01","actual":5.72,"predicted":6.49,"lower":3.85,"upper":9.13},
    {"date":"2013-02","actual":6.32,"predicted":8.09,"lower":5.45,"upper":10.73},
    {"date":"2013-03","actual":9.66,"predicted":8.76,"lower":6.12,"upper":11.40},
    {"date":"2013-04","actual":8.02,"predicted":8.56,"lower":5.92,"upper":11.20},
    {"date":"2013-05","actual":5.33,"predicted":5.71,"lower":3.07,"upper":8.35},
    {"date":"2016-04","actual":8.39,"predicted":8.00,"lower":5.36,"upper":10.64},
    {"date":"2016-05","actual":6.14,"predicted":6.70,"lower":4.06,"upper":9.34},
    {"date":"2016-06","actual":7.33,"predicted":6.99,"lower":4.36,"upper":9.63},
    {"date":"2016-07","actual":7.88,"predicted":6.61,"lower":3.97,"upper":9.25},
    {"date":"2016-08","actual":8.11,"predicted":7.61,"lower":4.97,"upper":10.25},
    {"date":"2016-09","actual":8.50,"predicted":7.75,"lower":5.11,"upper":10.39},
    {"date":"2016-10","actual":8.28,"predicted":7.67,"lower":5.03,"upper":10.31},
    {"date":"2017-05","actual":7.44,"predicted":6.79,"lower":4.15,"upper":9.43},
    {"date":"2017-06","actual":6.77,"predicted":7.25,"lower":4.61,"upper":9.88},
    {"date":"2017-07","actual":7.97,"predicted":7.20,"lower":4.56,"upper":9.84},
    {"date":"2017-08","actual":8.70,"predicted":7.08,"lower":4.44,"upper":9.72},
    {"date":"2017-09","actual":8.21,"predicted":7.34,"lower":4.70,"upper":9.98},
    {"date":"2017-10","actual":7.54,"predicted":7.65,"lower":5.01,"upper":10.29},
    {"date":"2017-11","actual":6.93,"predicted":8.01,"lower":5.37,"upper":10.65},
    {"date":"2017-12","actual":6.73,"predicted":7.02,"lower":4.38,"upper":9.66},
    {"date":"2018-01","actual":7.58,"predicted":8.22,"lower":5.58,"upper":10.86},
    {"date":"2018-05","actual":7.06,"predicted":6.53,"lower":3.89,"upper":9.17},
    {"date":"2018-06","actual":6.57,"predicted":6.71,"lower":4.07,"upper":9.35},
    {"date":"2018-07","actual":7.75,"predicted":6.57,"lower":3.93,"upper":9.21},
    {"date":"2018-08","actual":8.16,"predicted":7.51,"lower":4.87,"upper":10.15},
    {"date":"2018-09","actual":8.50,"predicted":7.92,"lower":5.28,"upper":10.55},
    {"date":"2020-03","actual":7.22,"predicted":5.46,"lower":2.82,"upper":8.09},
    {"date":"2020-04","actual":6.44,"predicted":6.03,"lower":3.39,"upper":8.66},
    {"date":"2020-10","actual":9.11,"predicted":8.32,"lower":5.68,"upper":10.95},
    {"date":"2020-11","actual":8.18,"predicted":8.74,"lower":6.10,"upper":11.38},
    {"date":"2020-12","actual":8.00,"predicted":7.88,"lower":5.24,"upper":10.51},
    {"date":"2021-01","actual":8.11,"predicted":8.17,"lower":5.53,"upper":10.81},
    {"date":"2021-03","actual":11.59,"predicted":13.08,"lower":10.44,"upper":15.72},
    {"date":"2021-04","actual":11.22,"predicted":11.95,"lower":9.31,"upper":14.59},
    {"date":"2021-05","actual":8.67,"predicted":7.70,"lower":5.06,"upper":10.33},
    {"date":"2021-06","actual":8.55,"predicted":8.20,"lower":5.56,"upper":10.84},
    {"date":"2021-10","actual":12.56,"predicted":10.33,"lower":7.69,"upper":12.97},
    {"date":"2022-01","actual":11.28,"predicted":9.78,"lower":7.14,"upper":12.42},
    {"date":"2022-02","actual":13.75,"predicted":11.08,"lower":8.44,"upper":13.72},
    {"date":"2022-03","actual":15.76,"predicted":12.29,"lower":9.65,"upper":14.93},
    {"date":"2022-08","actual":8.96,"predicted":7.74,"lower":5.10,"upper":10.38},
    {"date":"2022-09","actual":9.94,"predicted":8.23,"lower":5.59,"upper":10.87},
    {"date":"2022-10","actual":9.09,"predicted":8.19,"lower":5.55,"upper":10.83},
    {"date":"2022-11","actual":8.33,"predicted":8.77,"lower":6.13,"upper":11.41},
    {"date":"2022-12","actual":8.50,"predicted":8.05,"lower":5.41,"upper":10.69},
    {"date":"2023-01","actual":8.67,"predicted":12.32,"lower":9.68,"upper":14.96},
    {"date":"2023-02","actual":11.24,"predicted":13.73,"lower":11.09,"upper":16.37}
  ];
  
  // Model parameters from our analysis
  const modelData = {
    coefficients: [
      { variable: "Intercept", value: 8.589 },
      { variable: "CA_Landings_MT", value: -0.00014 },
      { variable: "Inventory_lbs", value: -0.00000007095 },
      { variable: "CA_Export_Total_MT", value: 0.000466 },
      { variable: "Weighted_Shore_Price_USD", value: 0.963 },
      { variable: "Seasonal_Factor", value: -5.063 }
    ],
    r_squared: 0.692,
    adjusted_r_squared: 0.663,
    mae: 1.026,
    rmse: 1.277,
    standard_error: 1.347
  };
  
  // Summary statistics
  const summaryStats = {
    periodStart: "2012-01",
    periodEnd: "2023-02",
    totalObservations: 60,
    averageActualPrice: 7.82,
    averagePredictedPrice: 7.82,
    percentWithinInterval: 95
  };
  
  // Seasonal factors
  const seasonalFactors = [
    {"month":1,"monthName":"January","factor":1.019},
    {"month":2,"monthName":"February","factor":1.154},
    {"month":3,"monthName":"March","factor":1.308},
    {"month":4,"monthName":"April","factor":1.276},
    {"month":5,"monthName":"May","factor":0.958},
    {"month":6,"monthName":"June","factor":0.912},
    {"month":7,"monthName":"July","factor":0.992},
    {"month":8,"monthName":"August","factor":0.945},
    {"month":9,"monthName":"September","factor":1.004},
    {"month":10,"monthName":"October","factor":0.977},
    {"month":11,"monthName":"November","factor":0.951},
    {"month":12,"monthName":"December","factor":0.984}
  ];
  
  // For easier rendering, create data in chronological order by year
  const chartData = [...fullData].sort((a, b) => {
    const dateA = new Date(a.date);
    const dateB = new Date(b.date);
    return dateA - dateB;
  });
  
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Lobster Price Prediction Model (2012-2023)</h1>
      
      <div className="mb-6">
        <div className="flex space-x-4 mb-4">
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'chart' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('chart')}
          >
            Price Chart
          </button>
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'model' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('model')}
          >
            Model Parameters
          </button>
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'seasonal' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('seasonal')}
          >
            Seasonal Factors
          </button>
        </div>
        
        {activeTab === 'chart' && (
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">Historical vs. Predicted Prices with 95% Confidence Intervals</h2>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    angle={-45}
                    textAnchor="end"
                    height={70}
                    tick={{ fontSize: 12 }}
                    interval={2}
                  />
                  <YAxis 
                    label={{ value: 'Price (USD/lb)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                    domain={[2, 18]}
                  />
                  <Tooltip 
                    formatter={(value) => `$${Number(value).toFixed(2)}`} 
                    labelFormatter={(label) => {
                      const [year, month] = label.split('-');
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                      return `${monthNames[parseInt(month) - 1]} ${year}`;
                    }}
                  />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="lower" 
                    strokeOpacity={0}
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.1} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="upper" 
                    strokeOpacity={0}
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.1} 
                    name="95% Confidence Interval"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="actual" 
                    stroke="#ff7300" 
                    dot={{ r: 4 }} 
                    activeDot={{ r: 6 }}
                    name="Actual Price" 
                    strokeWidth={2} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="predicted" 
                    stroke="#0088fe" 
                    strokeDasharray="5 5"
                    dot={false}
                    name="Predicted Price" 
                    strokeWidth={2} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h3 className="font-semibold">Summary Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-2">
                <div>
                  <p className="text-sm text-gray-600">Period</p>
                  <p className="font-medium">{summaryStats.periodStart} to {summaryStats.periodEnd}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Observations</p>
                  <p className="font-medium">{summaryStats.totalObservations}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg. Actual Price</p>
                  <p className="font-medium">{formatPrice(summaryStats.averageActualPrice)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg. Predicted Price</p>
                  <p className="font-medium">{formatPrice(summaryStats.averagePredictedPrice)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Within 95% CI</p>
                  <p className="font-medium">{summaryStats.percentWithinInterval}%</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'model' && (
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">Model Parameters and Performance</h2>
            <div className="mb-6">
              <h3 className="font-semibold mb-2">Model Coefficients</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Variable</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Coefficient</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interpretation</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {modelData.coefficients.map((coef, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{coef.variable}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {coef.variable === "Intercept" || coef.variable === "Weighted_Shore_Price_USD" || coef.variable === "Seasonal_Factor"
                            ? coef.value.toFixed(3)
                            : coef.value.toExponential(3)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {coef.variable === "Intercept" && "Base price when all other factors are zero"}
                          {coef.variable === "CA_Landings_MT" && "Price decreases as landings increase (supply effect)"}
                          {coef.variable === "Inventory_lbs" && "Price decreases as inventory increases"}
                          {coef.variable === "CA_Export_Total_MT" && "Price increases as exports increase (demand effect)"}
                          {coef.variable === "Weighted_Shore_Price_USD" && "Strong positive relationship with shore price"}
                          {coef.variable === "Seasonal_Factor" && "Adjusts for monthly seasonal effects"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold mb-2">Model Performance Metrics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600">R²</p>
                  <p className="text-lg font-medium">{modelData.r_squared.toFixed(3)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600">Adjusted R²</p>
                  <p className="text-lg font-medium">{modelData.adjusted_r_squared.toFixed(3)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600">MAE</p>
                  <p className="text-lg font-medium">{formatPrice(modelData.mae)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600">RMSE</p>
                  <p className="text-lg font-medium">{formatPrice(modelData.rmse)}</p>
                </div>
              </div>
              <div className="mt-4 p-3 bg-blue-50 rounded text-sm">
                <p><strong>R² (0.692):</strong> The model explains 69.2% of the variance in wholesale lobster prices.</p>
                <p><strong>MAE ($1.03):</strong> On average, predictions are within $1.03/lb of actual prices.</p>
                <p><strong>RMSE ($1.28):</strong> Higher than MAE indicates some larger prediction errors.</p>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'seasonal' && (
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">Seasonal Factors</h2>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
              {seasonalFactors.map(factor => (
                <div 
                  key={factor.month} 
                  className={`p-3 rounded ${factor.factor > 1 ? 'bg-green-50' : 'bg-red-50'}`}
                >
                  <p className="text-sm text-gray-600">{factor.monthName}</p>
                  <p className="text-lg font-medium">{factor.factor.toFixed(3)}</p>
                  <p className="text-xs text-gray-500">
                    {((factor.factor - 1) * 100).toFixed(1)}% {factor.factor > 1 ? 'above' : 'below'} avg
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 bg-gray-50 rounded">
              <h3 className="font-semibold mb-2">Seasonal Price Pattern Insights</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium">Peak Season (Highest Prices)</h4>
                  <ul className="list-disc pl-5 text-sm">
                    <li>March: 30.8% above average</li>
                    <li>April: 27.6% above average</li>
                    <li>February: 15.4% above average</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium">Low Season (Lowest Prices)</h4>
                  <ul className="list-disc pl-5 text-sm">
                    <li>June: 8.8% below average</li>
                    <li>November: 4.9% below average</li>
                    <li>August: 5.5% below average</li>
                  </ul>
                </div>
              </div>
              <p className="mt-3 text-sm">Winter and early spring show consistently higher prices, while summer months typically have lower prices, reflecting the seasonal availability of lobster.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LobsterPricePredictionModel;