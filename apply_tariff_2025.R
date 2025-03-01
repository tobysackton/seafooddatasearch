# ===========================================================================
# CORRECTED CRAB PRICE MODEL UPDATE SCRIPT
# Extends Tariff_Shock to all dates from Nov 2024 through Dec 2025
# ===========================================================================

# Load required libraries
library(stats)

# Read in the ORIGINAL data file (not the updated tariff one)
model_data <- read.csv("crab_price_predictions_updated.csv", na.strings = c("NA", ""))

# Print initial summary
cat("Original data has", nrow(model_data), "rows\n")

# Create training dataset (removing NA values for model building)
training_data <- model_data[!is.na(model_data$UBNL58_lb), ]

# Build the model with existing variables (same as your original)
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
cat("Model saved to crab_price_model.rds\n")

# Find the existing non-zero Tariff_Shock value from your data
tariff_shock_values <- model_data$Tariff_Shock[!is.na(model_data$Tariff_Shock) & model_data$Tariff_Shock != 0]
if(length(tariff_shock_values) > 0) {
  existing_tariff_value <- tariff_shock_values[1]
  cat("Using existing tariff shock value:", existing_tariff_value, "\n")
} else {
  existing_tariff_value <- 1
  cat("No existing tariff value found. Using default value of 1\n")
}

# Find the existing Tariff_Amt value as well
tariff_amt_values <- model_data$Tariff_Amt[!is.na(model_data$Tariff_Amt) & model_data$Tariff_Amt != 0]
if(length(tariff_amt_values) > 0) {
  existing_tariff_amt <- tariff_amt_values[1]
  cat("Using existing tariff amount value:", existing_tariff_amt, "\n")
} else {
  existing_tariff_amt <- 11.34
  cat("No existing tariff amount found. Using default value of 11.34\n")
}

# Create a copy of the data for modification
updated_data <- model_data

# Create a flag to identify rows in the target time period (Nov 2024 to Dec 2025)
updated_data$in_target_period <- FALSE

for(i in 1:nrow(updated_data)) {
  # Only process rows with valid Year and Month
  if(!is.na(updated_data$Year[i]) && !is.na(updated_data$Month[i])) {
    # Create a date for comparison (first day of month)
    row_date <- as.Date(paste(updated_data$Year[i], updated_data$Month[i], "01", sep="-"))
    
    # Check if this date is in our target period
    if(!is.na(row_date) && 
       row_date >= as.Date("2024-11-01") && 
       row_date <= as.Date("2025-12-01")) {
      updated_data$in_target_period[i] <- TRUE
    }
  }
}

# Count how many rows are in the target period
target_rows <- sum(updated_data$in_target_period, na.rm = TRUE)
cat("Found", target_rows, "rows in the target period (Nov 2024 - Dec 2025)\n")

# Apply tariff shock and amount to all rows in the target period
updated_data$Tariff_Shock[updated_data$in_target_period] <- existing_tariff_value
updated_data$Tariff_Amt[updated_data$in_target_period] <- existing_tariff_amt

# Generate new predictions
# First, temporarily replace NAs with 0 for prediction purposes
prediction_copy <- updated_data
na_columns <- c("log_CAUS_Total", "log_USD_Cost", "CADUSDEXCH", "Season_Factor_1", 
                "Pandemic_Shock", "Market_Shock_Factor", "Extra_Demand_Factor", 
                "Tariff_Shock", "Market_Shock_2025")

for(col in na_columns) {
  prediction_copy[[col]][is.na(prediction_copy[[col]])] <- 0
}

# Generate predictions where possible
prediction_copy$predicted_log_price <- NA
prediction_copy$predicted_price <- NA

# Only try to predict for rows that have the necessary predictors
valid_rows <- complete.cases(prediction_copy[, c("log_CAUS_Total", "log_USD_Cost", "CADUSDEXCH")])
if(sum(valid_rows) > 0) {
  prediction_copy$predicted_log_price[valid_rows] <- predict(model3_improved, newdata = prediction_copy[valid_rows, ])
  prediction_copy$predicted_price[valid_rows] <- exp(prediction_copy$predicted_log_price[valid_rows])
}

# Update the New_Predicted_Price column as well
prediction_copy$New_Predicted_Price <- prediction_copy$predicted_price

# Count rows that got new predictions
predicted_rows <- sum(!is.na(prediction_copy$predicted_price))
cat("Generated new predictions for", predicted_rows, "rows\n")

# For rows in tariff period, also update Predicted_Price_Tariff_Adjusted
# This is the price with tariff applied
prediction_copy$Predicted_Price_Tariff_Adjusted[prediction_copy$in_target_period] <- 
  prediction_copy$predicted_price[prediction_copy$in_target_period]

# Remove the temporary column before saving
prediction_copy$in_target_period <- NULL

# Save the predictions to a new CSV file
write.csv(prediction_copy, "crab_price_predictions_updated_tariff.csv", row.names = FALSE)
cat("Saved predictions to: crab_price_predictions_updated_tariff.csv\n")

# Display a sample of the changes
cat("\nSample of updated rows in the target period:\n")
head_rows <- head(prediction_copy[prediction_copy$Year == 2024 & prediction_copy$Month == 11 |
                                    prediction_copy$Year == 2025 & prediction_copy$Month == 12, ], 3)
print(head_rows[, c("Year", "Month", "Tariff_Shock", "Tariff_Amt", "predicted_price", "New_Predicted_Price")])