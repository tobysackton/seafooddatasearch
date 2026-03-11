console.log("Seafood charts loading...");

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log("DOM loaded, initializing chart");
  
  const container = document.getElementById('react-chart-container');
  console.log("Chart container found:", !!container);
  
  if (!container) {
    console.error("Chart container not found!");
    return;
  }
  
  // Verify libraries are loaded
  console.log("React available:", typeof React !== 'undefined');
  console.log("ReactDOM available:", typeof ReactDOM !== 'undefined');
  console.log("Recharts available:", typeof Recharts !== 'undefined');
console.log("Available global variables:", Object.keys(window).filter(key => key.includes('chart') || key.includes('Chart') || key.includes('Recharts')));
  
  if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {
    container.innerHTML = '<div style="color: red; padding: 10px;">Error: React or ReactDOM not loaded</div>';
    return;
  }
  
  try {
    // Simple chart data
    const data = [
      {year: 2012, volume: 18584701, avg_price: 11.41},
      {year: 2013, volume: 17849644, avg_price: 11.07},
      {year: 2014, volume: 18185660, avg_price: 12.13},
      {year: 2021, volume: 25459445, avg_price: 20.56},
      {year: 2024, volume: 19691199, avg_price: 19.51}
    ];
    
    if (typeof Recharts === 'undefined') {
      console.warn("Recharts not available, rendering basic React content");
      // Render basic React content if Recharts isn't available
      ReactDOM.render(
        React.createElement('div', null, [
          React.createElement('h3', {style: {color: 'red'}}, 'Recharts Library Not Available'),
          React.createElement('p', null, 'The chart library could not be loaded.'),
          React.createElement('p', null, 'Simple data display:'),
          React.createElement('ul', null, 
            data.map(item => 
              React.createElement('li', {key: item.year}, 
                `${item.year}: Volume ${(item.volume/1000000).toFixed(2)}M lbs, Price $${item.avg_price.toFixed(2)}/lb`
              )
            )
          )
        ]),
        container
      );
      console.log("Basic React content rendered");
    } else {
      console.log("Attempting to render Recharts");
      
      // Extract Recharts components
      const { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } = Recharts;
      console.log("Recharts components extracted:", !!ComposedChart);
      
      // Create chart element
      const chartElement = React.createElement(
        ResponsiveContainer,
        { width: "100%", height: 400 },
        React.createElement(
          ComposedChart,
          {
            data: data,
            margin: { top: 20, right: 30, left: 20, bottom: 20 }
          },
          [
            React.createElement(CartesianGrid, { strokeDasharray: "3 3", key: "grid" }),
            React.createElement(XAxis, { dataKey: "year", key: "xAxis" }),
            React.createElement(YAxis, { 
              yAxisId: "left", 
              orientation: "left",
              label: { value: 'Volume (lbs)', angle: -90, position: 'insideLeft' },
              key: "yAxis1"
            }),
            React.createElement(YAxis, { 
              yAxisId: "right", 
              orientation: "right",
              domain: [0, 25],
              label: { value: 'Price ($/lb)', angle: 90, position: 'insideRight' },
              key: "yAxis2"
            }),
            React.createElement(Tooltip, { key: "tooltip" }),
            React.createElement(Legend, { key: "legend" }),
            React.createElement(Bar, { 
              yAxisId: "left", 
              dataKey: "volume", 
              fill: "#3182CE", 
              name: "Volume (lbs)",
              key: "bar"
            }),
            React.createElement(Line, { 
              yAxisId: "right", 
              type: "monotone", 
              dataKey: "avg_price", 
              stroke: "#E53E3E", 
              name: "Avg Price ($/lb)",
              strokeWidth: 3,
              dot: { r: 5 },
              key: "line"
            })
          ]
        )
      );
      
      console.log("Chart element created, attempting to render");
      ReactDOM.render(chartElement, container);
      console.log("Chart rendering complete");
    }
  } catch (e) {
    console.error("Error rendering chart:", e);
    container.innerHTML = `<div style="color: red; padding: 20px;">
      <h3>Error Rendering Chart</h3>
      <p>${e.message}</p>
      <p>Stack: ${e.stack}</p>
    </div>`;
  }
});