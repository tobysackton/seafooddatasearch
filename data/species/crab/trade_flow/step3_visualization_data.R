# Step 3: Create Visualization Dataset
# Save this file as "step3_visualization_data.R"

library(readr)

create_visualization_data <- function(predictions_file, output_viz_file, start_year = 2019) {
  # Load the predictions
  predictions <- read.csv(predictions_file, na.strings = c("NA", ""))
  
  # Filter for visualization (typically 2019-2025)
  viz_data <- predictions[predictions$Year >= start_year & predictions$Year <= 2025, ]
  
  # Ensure data is properly sorted
  viz_data <- viz_data[order(viz_data$Year, viz_data$Month), ]
  
  # Write to CSV
  write.csv(viz_data, output_viz_file, row.names = FALSE)
  cat("Visualization data (", start_year, "-2025) saved to ", output_viz_file, "\n", sep="")
  
  # Basic summary of the visualization data
  cat("\nVisualization Data Summary:\n")
  cat("==========================\n")
  cat("Years included:", paste(sort(unique(viz_data$Year)), collapse=", "), "\n")
  cat("Total rows:", nrow(viz_data), "\n")
  cat("Predicted months (NA UBNL58_lb):", sum(is.na(viz_data$UBNL58_lb)), "\n")
  cat("Actual months (with UBNL58_lb):", sum(!is.na(viz_data$UBNL58_lb)), "\n\n")
  
  # Return the visualization data
  return(viz_data)
}

# Example usage:
# viz_data <- create_visualization_data("crab_price_full_predictions.csv", 
#                                       "crab_price_forecast_2019_2025.csv",
#                                       2019)