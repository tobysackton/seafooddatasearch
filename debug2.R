# ===========================================================================
# REVISED TARIFF IMPACT MODEL
# Applies tariff impact on top of original predictions from Nov 2024 onward
# ===========================================================================

# Load required libraries
library(stats)

# Read in the ORIGINAL data file
model_data <- read.csv("crab_price_predictions_updated.csv", na.strings = c("NA", ""))

# Print initial info
cat("Original data has", nrow(model_data), "rows\n")

# Load the previously saved model (if it exists, otherwise create it)
if(file.exists("crab_price_model.rds")) {
  model3_improved <- readRDS("crab_price_model.rds")
  cat("Loaded existing model from crab_price_model.rds\n")
} else {
  # Create training dataset (removing NA values for model building)
  training_data <- model_data[!is.na(model_data$UBNL58_lb), ]
  
  # Build the model with existing variables
  model3_improved <- lm(
    log_UBNL58_lb ~ log_CAUS_Total + 
      log_USD_Cost + 
      CADUSDEXCH + 
      Season_Factor_1 + 
      Pandemic_Shock + 
      Market_Shock_Factor + 
      Extra_Demand_Factor + 
      Tariff_Shock + 
      Market_Shock_2025 + 
      log_USD_Cost:CADUSDEXCH, 
    data = training_data
  )
  
  # Save the model
  saveRDS(model3_improved, "crab_price_model.rds")
  cat("Created and saved new model to crab_price_model.rds\n")
}

# Find the existing tariff shock coefficient from the model
tariff_coef <- summary(model3_improved)$coefficients["Tariff_Shock", "Estimate"]
tariff_effect <- exp(tariff_coef) - 1  # Convert log effect to percentage
cat("\nTariff_Shock coefficient in model:", tariff_coef, "\n")
cat("This translates to a price effect of approximately", round(tariff_effect * 100, 2), "%\n")

# Create a copy of the data for modification
updated_data <- model_data

# Determine the target tariff percentage for all months from Nov 2024 to Dec 2025
target_tariff_pct <- 0.20  # 20% tariff impact

# Define the target period (all dates from Nov 2024 through Dec 2025)
for(i in 1:nrow(updated_data)) {
  # Skip rows with missing Year or Month
  if(is.na(updated_data$Year[i]) || is.na(updated_data$Month[i])) {
    next
  }
  
  # Check if this date is in our target period
  if((updated_data$Year[i] == 2024 && updated_data$Month[i] >= 11) || 
     (updated_data$Year[i] == 2025 && updated_data$Month[i] <= 12)) {
    
    # First, get the original predicted price WITHOUT tariff
    original_predicted_price <- NA
    if(!is.na(updated_data$Predicted_Price[i])) {
      # Use the model to predict what price would have been without tariff
      temp_data <- updated_data[i, ]
      temp_data$Tariff_Shock <- 0  # Remove tariff effect
      
      # Create temp dataset for prediction with all required columns
      pred_cols <- c("log_CAUS_Total", "log_USD_Cost", "CADUSDEXCH", "Season_Factor_1", 
                     "Pandemic_Shock", "Market_Shock_Factor", "Extra_Demand_Factor", 
                     "Tariff_Shock", "Market_Shock_2025")
      for(col in pred_cols) {
        if(is.na(temp_data[[col]])) {
          temp_data[[col]] <- 0  # Replace NA with 0 for prediction
        }
      }
      
      # Make the no-tariff prediction
      log_price_no_tariff <- predict(model3_improved, newdata = temp_data)
      price_no_tariff <- exp(log_price_no_tariff)
      
      # Apply the 20% tariff on top of this prediction
      updated_data$Tariff_Shock[i] <- 1  # Standard tariff indicator
      updated_data$Tariff_Amt[i] <- price_no_tariff * target_tariff_pct  # Dollar amount of tariff
      
      # Calculate and store the tariff-adjusted price
      price_with_tariff <- price_no_tariff * (1 + target_tariff_pct)
      updated_data$Predicted_Price_Tariff_Adjusted[i] <- price_with_tariff
      updated_data$Predicted_Price[i] <- price_with_tariff
      updated_data$New_Predicted_Price[i] <- price_with_tariff
    }
  }
}

# Count modified rows
modified_rows <- sum((updated_data$Year == 2024 & updated_data$Month >= 11) | 
                       (updated_data$Year == 2025 & updated_data$Month <= 12), 
                     na.rm = TRUE)
cat("\nModified", modified_rows, "rows in the target period (Nov 2024 - Dec 2025)\n")

# Create comparison table for understanding changes
cat("\nBefore/After adding tariff impact:\n")
cat("Year-Month, Original Price, Price with 20% Tariff\n")

# Show a sample of changes
for(year in c(2024, 2025)) {
  for(month in c(11, 12)) {
    if(year == 2025 && month == 12) next  # Skip if we don't have this data
    
    # Find the row
    row_idx <- which(updated_data$Year == year & updated_data$Month == month)
    if(length(row_idx) > 0) {
      orig_row <- model_data[row_idx[1], ]
      new_row <- updated_data[row_idx[1], ]
      
      # Get prices
      orig_price <- orig_row$Predicted_Price
      new_price <- new_row$Predicted_Price
      
      if(!is.na(orig_price) && !is.na(new_price)) {
        pct_change <- ((new_price / orig_price) - 1) * 100
        cat(year, "-", month, ": $", round(orig_price, 2), 
            " -> $", round(new_price, 2), 
            " (", round(pct_change, 2), "% change)\n", sep="")
      }
    }
  }
}

# Save the new predictions to a CSV file
write.csv(updated_data, "crab_price_predictions_updated_tariff.csv", row.names = FALSE)
cat("\nSaved predictions to: crab_price_predictions_updated_tariff.csv\n")

# Print a final summary
cat("\nSummary of changes:\n")
cat("- Applied a 20% tariff impact on top of original predictions for all months from Nov 2024 through Dec 2025\n")
cat("- For each affected month, calculated what the price would have been without tariff\n")
cat("- Then added 20% to that price to reflect the tariff impact\n")
cat("- Updated the Predicted_Price, Predicted_Price_Tariff_Adjusted, and New_Predicted_Price columns\n")