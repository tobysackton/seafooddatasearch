# Step 1: Build and Validate Historical Model
# Save this file as "step1_model_building.R"

library(readr)

build_crab_model <- function(input_file, output_model_file) {
  # Load the data
  model_data <- read.csv(input_file, na.strings = c("NA", ""))
  
  # Print basic data info
  cat("Dataset has", nrow(model_data), "rows and", ncol(model_data), "columns\n")
  cat("Years in data:", paste(sort(unique(model_data$Year[!is.na(model_data$Year)])), collapse=", "), "\n\n")
  
  # Extract only historical data with actual UBNL58_lb values for model training
  training_data <- model_data[!is.na(model_data$UBNL58_lb), ]
  cat("Training data has", nrow(training_data), "rows\n")
  
  # Build the model
  model3_improved <- lm(log_UBNL58_lb ~ log_CAUS_Total + log_USD_Cost + CADUSDEXCH + 
                          Season_Factor_1 + Pandemic_Shock + Market_Shock_Factor + 
                          Extra_Demand_Factor + Tariff_Shock + Market_Shock_2025 +
                          log_USD_Cost:CADUSDEXCH, 
                        data = training_data)
  
  # Print model summary
  cat("\nModel Summary:\n")
  model_summary <- summary(model3_improved)
  cat("R-squared:", model_summary$r.squared, "\n")
  cat("Adjusted R-squared:", model_summary$adj.r.squared, "\n\n")
  
  # Save the model to an RDS file for later use
  saveRDS(model3_improved, output_model_file)
  cat("Model saved to", output_model_file, "\n")
  
  # Return the model object
  return(model3_improved)
}

# Example usage:
# model <- build_crab_model("model3_improved_predictions.csv", "crab_price_model.rds")