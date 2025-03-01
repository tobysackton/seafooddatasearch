# Master Script to Run All Steps
# Save this file as "run_crab_price_model.R"

# Load required libraries
library(readr)

# Set working directory (if needed)
# setwd("/Users/jtsackton/LocalProjects/github_seafood_datasearch/data/species/crab/trade_flow")

# Source the individual scripts
source("step1_model_building.R")
source("step2_future_predictions.R")
source("step3_visualization_data.R")

# Run the entire process
run_full_model <- function(input_file = "model3_improved_predictions.csv") {
  cat("CRAB PRICE PREDICTION MODEL\n")
  cat("==========================\n\n")
  
  # Step 1: Build the model
  cat("STEP 1: Building the model...\n")
  cat("-----------------------------\n")
  model <- build_crab_model(input_file, "crab_price_model.rds")
  cat("\n\n")
  
  # Step 2: Generate predictions
  cat("STEP 2: Generating predictions...\n")
  cat("--------------------------------\n")
  predictions <- generate_predictions(input_file, "crab_price_model.rds", 
                                      "crab_price_full_predictions.csv")
  cat("\n\n")
  
  # Step 3: Create visualization dataset
  cat("STEP 3: Creating visualization dataset...\n")
  cat("---------------------------------------\n")
  viz_data <- create_visualization_data("crab_price_full_predictions.csv", 
                                        "crab_price_forecast_2019_2025.csv", 2019)
  
  cat("\nProcess complete!\n")
  cat("=================\n")
  cat("Files created:\n")
  cat("1. crab_price_model.rds - The statistical model\n")
  cat("2. crab_price_full_predictions.csv - Complete dataset with predictions\n")
  cat("3. crab_price_forecast_2019_2025.csv - Filtered dataset for visualization\n\n")
  
  cat("You can now use the visualization dataset for further analysis.\n")
}

# Run the process
run_full_model()