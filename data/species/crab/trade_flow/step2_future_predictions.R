# Step 2: Generate Future Predictions
# Save this file as "step2_future_predictions.R"

library(readr)

generate_predictions <- function(input_file, model_file, output_predictions_file) {
  # Load the data and model
  model_data <- read.csv(input_file, na.strings = c("NA", ""))
  model3_improved <- readRDS(model_file)
  
  # STEP 1: Extract Jan-Feb 2025 with actual data
  actual_2025 <- model_data[model_data$Year == 2025 & model_data$Month %in% c(1, 2), ]
  cat("Jan-Feb 2025 actual data:", nrow(actual_2025), "rows\n")
  
  # STEP 2: Create template for Mar-Dec 2025 from 2024 data
  template_2025 <- model_data[model_data$Year == 2024 & model_data$Month >= 3 & model_data$Month <= 12, ]
  template_2025$Year <- 2025
  template_2025$Dateyyymm <- paste0(template_2025$Month, "/1/25")
  
  # STEP 3: Ensure UBNL58_lb is NA for future predictions
  template_2025$UBNL58_lb <- NA
  template_2025$log_UBNL58_lb <- NA
  
  # STEP 4: Carry forward certain values from Feb 2025
  feb_2025 <- actual_2025[actual_2025$Month == 2, ]
  template_2025$USD_Cost <- feb_2025$USD_Cost[1]
  template_2025$log_USD_Cost <- log(template_2025$USD_Cost)
  
  # STEP 5: Set shock factors for 2025
  template_2025$Tariff_Shock <- 1  # Assuming tariff shock continues
  template_2025$Market_Shock_2025 <- 1  # Assuming 2025 market shock continues
  
  # STEP 6: Use CADUSDEXCH values from original data if available
  for (i in 1:nrow(template_2025)) {
    month <- template_2025$Month[i]
    date_pattern <- paste0(month, "/1/25")
    matching_rows <- model_data[grepl(date_pattern, model_data$Dateyyymm), ]
    
    if (nrow(matching_rows) > 0 && !is.na(matching_rows$CADUSDEXCH[1])) {
      template_2025$CADUSDEXCH[i] <- matching_rows$CADUSDEXCH[1]
      template_2025$log_CADUSDEXCH[i] <- log(matching_rows$CADUSDEXCH[1])
    }
  }
  
  # STEP 7: Combine data - historical + actual 2025 + predicted 2025
  historical_data <- model_data[model_data$Year < 2025, ]
  combined_data <- rbind(historical_data, actual_2025, template_2025)
  
  # STEP 8: Generate predictions for all data
  predictions <- predict(model3_improved, newdata = combined_data, 
                         interval = "confidence", level = 0.95)
  
  # STEP 9: Add predictions to the dataset
  combined_data$Predicted_Price <- exp(predictions[,"fit"])
  combined_data$Lower_CI <- exp(predictions[,"lwr"])
  combined_data$Upper_CI <- exp(predictions[,"upr"])
  
  # STEP 10: Update New_Predicted columns
  combined_data$New_Predicted_Price <- combined_data$Predicted_Price
  combined_data$New_Lower_CI <- combined_data$Lower_CI
  combined_data$New_Upper_CI <- combined_data$Upper_CI
  
  # Sort by date
  combined_data <- combined_data[order(combined_data$Year, combined_data$Month), ]
  
  # Save to file
  write.csv(combined_data, output_predictions_file, row.names = FALSE)
  cat("Full predictions saved to", output_predictions_file, "\n")
  
  # Display 2025 predictions
  predictions_2025 <- combined_data[combined_data$Year == 2025, ]
  predictions_2025 <- predictions_2025[order(predictions_2025$Month), ]
  
  cat("\nPredictions for 2025:\n")
  cat("=====================\n")
  display_cols <- c("Dateyyymm", "Month", "UBNL58_lb", "New_Predicted_Price", "New_Lower_CI", "New_Upper_CI")
  display_table <- predictions_2025[, display_cols]
  display_table$Price_Type <- ifelse(is.na(display_table$UBNL58_lb), "PREDICTED", "ACTUAL")
  
  print(display_table)
  
  return(combined_data)
}

# Example usage:
# predictions <- generate_predictions("model3_improved_predictions.csv", 
#                                     "crab_price_model.rds", 
#                                     "crab_price_full_predictions.csv")