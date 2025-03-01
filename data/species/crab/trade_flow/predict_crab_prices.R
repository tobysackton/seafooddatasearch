predict_crab_prices <- function(input_file, output_file) {
  # Load necessary libraries
  library(readr)
  
  # Load the data
  model_data <- read.csv(input_file, na.strings = c("NA", ""))
  
  # Print column names to verify
  cat("Columns in dataset:", paste(names(model_data), collapse=", "), "\n\n")
  
  # Make a backup of original data before modifications
  original_data <- model_data
  
  # Check for 2025 data
  cat("Rows for 2025:", nrow(model_data[model_data$Year == 2025, ]), "\n")
  
  # Create the improved model using only historical data (where UBNL58_lb is not NA)
  model_data_hist <- model_data[!is.na(model_data$UBNL58_lb), ]
  model3_improved <- lm(log_UBNL58_lb ~ log_CAUS_Total + log_USD_Cost + CADUSDEXCH + 
                          Season_Factor_1 + Pandemic_Shock + Market_Shock_Factor + 
                          Extra_Demand_Factor + Tariff_Shock + Market_Shock_2025 +
                          log_USD_Cost:CADUSDEXCH, 
                        data = model_data_hist, na.action = na.exclude)
  
  # Print model summary
  cat("Model R-squared:", summary(model3_improved)$r.squared, "\n\n")
  
  # Clean up the future months data (March-December 2025)
  # First identify which rows are Jan-Feb 2025 (with actual data)
  data_2025_early <- model_data[model_data$Year == 2025 & model_data$Month %in% c(1, 2), ]
  
  # Get the future months (March-December 2025) from original data
  future_rows <- grepl("/1/25$", model_data$Dateyyymm) & 
    !(model_data$Month %in% c(1, 2) & model_data$Year == 2025)
  
  future_months <- model_data[future_rows, ]
  
  # Clean up future_months and ensure proper values
  future_months$Year <- 2025
  future_months$Month <- as.numeric(sub("/1/25$", "", future_months$Dateyyymm))
  
  # Ensure UBNL58_lb is NA for future months
  future_months$UBNL58_lb <- NA
  future_months$log_UBNL58_lb <- NA
  
  # Process each future month individually to ensure complete data
  for (i in 1:nrow(future_months)) {
    current_month <- future_months$Month[i]
    # Find matching 2024 data for the same month
    match_2024 <- model_data[model_data$Year == 2024 & model_data$Month == current_month, ]
    
    if (nrow(match_2024) > 0) {
      # Copy values from 2024
      future_months$CAUS_Total[i] <- match_2024$CAUS_Total
      future_months$Season_Factor_1[i] <- match_2024$Season_Factor_1
      future_months$Pandemic_Shock[i] <- 0  # Assume pandemic shock is over
      future_months$Extra_Demand_Factor[i] <- match_2024$Extra_Demand_Factor
      future_months$Market_Shock_Factor[i] <- match_2024$Market_Shock_Factor
      
      # Carry forward from Feb 2025 for these values
      last_known <- model_data[model_data$Year == 2025 & model_data$Month == 2, ]
      future_months$USD_Cost[i] <- last_known$USD_Cost
      # CADUSDEXCH is already set correctly in the data
    }
  }
  
  # Set shock factors for future months
  future_months$Tariff_Shock <- 1  # Assuming tariff shock continues
  future_months$Market_Shock_2025 <- 1  # Assuming 2025 specific market shock continues
  
  # Calculate log values that we need for the model
  future_months$log_CAUS_Total <- log(future_months$CAUS_Total)
  future_months$log_USD_Cost <- log(future_months$USD_Cost)
  future_months$log_CADUSDEXCH <- log(future_months$CADUSDEXCH)
  
  # Create a clean dataset by removing any existing future month data and adding our processed data
  # 1. Keep all non-2025 data
  clean_data <- model_data[model_data$Year != 2025 | is.na(model_data$Year), ]
  
  # 2. Add the Jan-Feb 2025 data with actual prices
  clean_data <- rbind(clean_data, data_2025_early)
  
  # 3. Add our properly prepared future months
  clean_data <- rbind(clean_data, future_months)
  
  # Make predictions for all data
  predictions <- predict(model3_improved, newdata = clean_data, interval = "confidence", level = 0.95)
  
  # Convert log predictions back to original scale
  clean_data$Predicted_Price <- exp(predictions[,"fit"])
  clean_data$Lower_CI <- exp(predictions[,"lwr"])
  clean_data$Upper_CI <- exp(predictions[,"upr"])
  
  # Update New_Predicted_Price for 2025 predictions (with Market_Shock_2025)
  clean_data$New_Predicted_Price <- clean_data$Predicted_Price
  clean_data$New_Lower_CI <- clean_data$Lower_CI
  clean_data$New_Upper_CI <- clean_data$Upper_CI
  
  # Filter for 2019-2025 for visualization
  visualization_data <- clean_data[clean_data$Year >= 2019 & clean_data$Year <= 2025, ]
  
  # Sort by date - handle cases where Year might be NA
  visualization_data$temp_date <- as.Date(
    paste0("01/", visualization_data$Month, "/", 
           ifelse(is.na(visualization_data$Year), "2025", visualization_data$Year)), 
    format="%d/%m/%Y")
  
  visualization_data <- visualization_data[order(visualization_data$temp_date), ]
  visualization_data$temp_date <- NULL  # Remove the temporary date column
  
  # Save to CSV - make sure to remove any duplicate rows
  visualization_data <- unique(visualization_data)  # Remove duplicates
  write.csv(visualization_data, output_file, row.names = FALSE)
  
  # Display future predictions for 2025
  future_predictions <- clean_data[clean_data$Year == 2025, ]
  future_predictions <- future_predictions[order(future_predictions$Month), ]
  
  cat("\nPredictions for 2025:\n")
  display_table <- future_predictions[, c("Dateyyymm", "Month", "UBNL58_lb", "New_Predicted_Price", "New_Lower_CI", "New_Upper_CI")]
  display_table$Price_Type <- ifelse(is.na(display_table$UBNL58_lb), "PREDICTED", "ACTUAL")
  
  print(display_table)
  
  cat("\nNote: UBNL58_lb values are NA for predicted months (Mar-Dec 2025)\n")
  
  return(visualization_data)
}

# Example usage:
# result <- predict_crab_prices("model3_improved_predictions.csv", "crab_price_forecast_2019_2025.csv")