/* Styles for React chart components */
.chart-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-container h2 {
  color: #00796B;
  margin-bottom: 5px;
  font-size: 1.5rem;
  text-align: center;
}

.chart-description {
  color: #666;
  text-align: center;
  margin-bottom: 20px;
}

.chart-wrapper {
  background-color: #F5F5F5;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-insights {
  padding: 15px;
  background-color: #F5F5F5;
  border-radius: 8px;
  margin-top: 20px;
}

.chart-insights h3 {
  margin-top: 0;
  color: #00796B;
  font-size: 1.2rem;
}

.chart-insights ul {
  padding-left: 20px;
}

.chart-insights li {
  margin-bottom: 8px;
}

/* Custom Tooltip */
.custom-tooltip {
  background-color: white;
  border: 1px solid #B2DFDB;
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.tooltip-label {
  font-weight: bold;
  margin-bottom: 5px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.tooltip-volume {
  color: #3182CE;
}

.tooltip-price {
  color: #E53E3E;
}

.tooltip-value {
  color: #2F855A;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .chart-container {
    padding: 15px;
  }
  
  .chart-wrapper {
    padding: 10px;
  }
}