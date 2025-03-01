# Reliable Crab Price Prediction Script with Updated Assumptions
# This script includes specific assumptions about dock costs and exchange rates

library(readr)

predict_crab_prices <- function(input_file, output_file) {
  cat("CRAB PRICE PREDICTION MODEL WITH UPDATED ASSUMPTIONS\n")
  cat("===================================================\n\n")
  
  # Load the data
  cat("Loading input data from:", input_file, "\n")
  model_data <- read.csv(input_file, na.strings = c("NA", ""))
  
  # STEP 1: Build the model using historical data
  cat("\nSTEP 1: Building the model...\n")
  training_data <- model_data[!is.na(model_data$UBNL58_lb), ]
  cat("- Using", nrow(training_data), "rows of historical data with actual UBNL58_lb values\n")
  
  model3_improved <- lm(log_UBNL58_lb ~ log_CAUS_Total + log_USD_Cost + CADUSDEXCH + 
                          Season_Factor_1 + Pandemic_Shock + Market_Shock_Factor + 
                          Extra_Demand_Factor + Tariff_Shock + Market_Shock_2025 +
                          log_USD_Cost:CADUSDEXCH, 
                        data = training_data)
  
  model_summary <- summary(model3_improved)
  cat("- Model R-squared:", model_summary$r.squared, "\n")
  
  # STEP 2: Prepare data for predictions
  cat("\nSTEP 2: Preparing data for predictions...\n")
  
  # Extract data from 2025 that has actual values (Jan-Feb)
  actual_2025 <- model_data[model_data$Year == 2025 & model_data$Month %in% c(1, 2), ]
  cat("- Found", nrow(actual_2025), "months with actual data in 2025\n")
  
  # Create template for future months (Mar-Dec 2025) from 2024 data
  template_2025 <- model_data[model_data$Year == 2024 & model_data$Month >= 3 & model_data$Month <= 12, ]
  template_2025$Year <- 2025
  template_2025$Dateyyymm <- paste0(template_2025$Month, "/1/25")
  
  # Set UBNL58_lb to NA for future predictions
  template_2025$UBNL58_lb <- NA
  template_2025$log_UBNL58_lb <- NA
  
  cat("- Created", nrow(template_2025), "future month templates for 2025\n")
  
  # STEP 3: Apply specific assumptions for 2025
  cat("\nSTEP 3: Applying assumptions for 2025...\n")
  cat("- Carrying forward Feb 2025 USD_Cost for all future months\n")
  feb_2025_cost <- actual_2025[actual_2025$Month == 2, "USD_Cost"]
  template_2025$USD_Cost <- feb_2025_cost
  
  # Set Pack_Year according to industry standard (April-March cycle)
  cat("- Setting Pack_Year values (April-March cycle)\n")
  # Jan-Mar 2025 belongs to pack year 2024
  january_march <- template_2025$Month >= 1 & template_2025$Month <= 3
  # April-Dec 2025 belongs to pack year 2025
  april_december <- template_2025$Month >= 4 & template_2025$Month <= 12
  
  template_2025$Pack_Year[january_march] <- 2024
  template_2025$Pack_Year[april_december] <- 2025
  
  cat("- Setting CAD Dock Cost to $3.00 for March 2025 (Pack_Year 2024)\n")
  march_row <- template_2025$Month == 3
  template_2025$Dock_Cost_CAD[march_row] <- 3.00
  
  cat("- Setting CAD Dock Cost to $3.30 for April-December 2025 (Pack_Year 2025)\n")
  later_months <- template_2025$Month >= 4
  template_2025$Dock_Cost_CAD[later_months] <- 3.30
  
  # Calculate USD dock cost based on exchange rate
  cat("- Calculating USD Dock Cost based on exchange rates\n")
  template_2025$USD_Cost <- template_2025$Dock_Cost_CAD / template_2025$CADUSDEXCH
  
  # Recalculate log values
  template_2025$log_USD_Cost <- log(template_2025$USD_Cost)
  template_2025$log_Dock_Cost_CAD <- log(template_2025$Dock_Cost_CAD)
  
  # Set shock factors for future months
  template_2025$Tariff_Shock <- 1  # Assuming tariff shock continues
  template_2025$Market_Shock_2025 <- 1  # Assuming 2025 market shock continues
  
  # STEP 4: Combine data - historical + actual 2025 + predicted 2025
  cat("\nSTEP 4: Combining datasets...\n")
  historical_data <- model_data[model_data$Year < 2025, ]
  combined_data <- rbind(historical_data, actual_2025, template_2025)
  combined_data <- combined_data[order(combined_data$Year, combined_data$Month), ]
  
  # STEP 5: Generate predictions
  cat("\nSTEP 5: Generating predictions...\n")
  predictions <- predict(model3_improved, newdata = combined_data, 
                         interval = "confidence", level = 0.95)
  
  # Add predictions to the dataset
  combined_data$Predicted_Price <- exp(predictions[,"fit"])
  combined_data$Lower_CI <- exp(predictions[,"lwr"])
  combined_data$Upper_CI <- exp(predictions[,"upr"])
  
  # Update New_Predicted columns
  combined_data$New_Predicted_Price <- combined_data$Predicted_Price
  combined_data$New_Lower_CI <- combined_data$Lower_CI
  combined_data$New_Upper_CI <- combined_data$Upper_CI
  
  # STEP 6: Save results
  cat("\nSTEP 6: Saving results...\n")
  write.csv(combined_data, output_file, row.names = FALSE)
  cat("- Full dataset with predictions saved to:", output_file, "\n")
  
  # Create visualization dataset (2019-2025)
  viz_data <- combined_data[combined_data$Year >= 2019 & combined_data$Year <= 2025, ]
  viz_output_file <- sub("\\.csv$", "_visualization_2019_2025.csv", output_file)
  write.csv(viz_data, viz_output_file, row.names = FALSE)
  cat("- Visualization dataset (2019-2025) saved to:", viz_output_file, "\n")
  
  # STEP 7: Display results
  cat("\nSTEP 7: Prediction results for 2025\n")
  cat("====================================\n")
  predictions_2025 <- combined_data[combined_data$Year == 2025, ]
  predictions_2025 <- predictions_2025[order(predictions_2025$Month), ]
  
  display_cols <- c("Dateyyymm", "Month", "Pack_Year", "UBNL58_lb", "USD_Cost", "Dock_Cost_CAD", 
                    "CADUSDEXCH", "New_Predicted_Price", "New_Lower_CI", "New_Upper_CI")
  display_table <- predictions_2025[, display_cols]
  display_table$Price_Type <- ifelse(is.na(display_table$UBNL58_lb), "PREDICTED", "ACTUAL")
  
  print(display_table)
  
  cat("\nASSUMPTIONS SUMMARY:\n")
  cat("- Used historical data to build model (R-squared:", round(model_summary$r.squared, 4), ")\n")
  cat("- Pack_Year 2024: January-March 2025\n")
  cat("- Pack_Year 2025: April-December 2025\n")
  cat("- CAD Dock Cost in March 2025 (Pack_Year 2024): $3.00\n")
  cat("- CAD Dock Cost in April-December 2025 (Pack_Year 2025): $3.30\n")
  cat("- USD Dock Cost calculated from CAD cost and monthly exchange rates\n")
  cat("- Tariff Shock factor: 1 (Assuming tariff shock continues in 2025)\n")
  cat("- Market Shock 2025 factor: 1 (Assuming market shock continues in 2025)\n")
  
  cat("\nProcess complete!\n")
  
  return(combined_data)
}

# Example usage:
# result <- predict_crab_prices("model3_improved_predictions.csv", "crab_price_predictions_updated.csv")