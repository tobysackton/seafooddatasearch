# ===========================================================================
# CRAB PRICE MODEL UPDATE SCRIPT
# Extends Tariff_Shock to all dates from Nov 2024 through Dec 2025
# ===========================================================================

# 1. Load required libraries
library(stats)

# 2. Read in your data file
model_data <- read.csv("model3_improved_predictions.csv", na.strings = c("NA", ""))

# 3. Create training dataset (removing NA values for model building)
training_data <- model_data[!is.na(model_data$UBNL58_lb), ]

# 4. Build the model with existing variables (same as your original)
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

# 5. Print model summary to check coefficients
summary(model3_improved)

# 6. Save the model
saveRDS(model3_improved, "crab_price_model.rds")
cat("Model saved to crab_price_model.rds\n")

# 7. Find the existing non-zero Tariff_Shock value from your data
existing_tariff_value <- unique(model_data$Tariff_Shock[model_data$Tariff_Shock != 0 & !is.na(model_data$Tariff_Shock)])[1]
cat("Using existing tariff value:", existing_tariff_value, "\n")

# 8. Create date objects for easier comparison
model_data$Date <- as.Date(paste(model_data$Year, model_data$Month, "01", sep="-"))

# 9. Apply the tariff shock to all dates from Nov 1, 2024 to Dec 1, 2025
tariff_period_start <- as.Date("2024-11-01")
tariff_period_end <- as.Date("2025-12-01")

model_data$Tariff_Shock_Updated <- model_data$Tariff_Shock
model_data$Tariff_Shock_Updated[model_data$Date >= tariff_period_start & 
                                  model_data$Date <= tariff_period_end] <- existing_tariff_value

# 10. Make a copy for predictions
prediction_data <- model_data
prediction_data$Tariff_Shock <- prediction_data$Tariff_Shock_Updated  # Use the updated values for prediction

# 11. Generate predictions
prediction_data$predicted_log_price <- predict(model3_improved, newdata = prediction_data)

# 12. Convert from log price back to actual price
prediction_data$predicted_price <- exp(prediction_data$predicted_log_price)

# 13. Save the new predictions to a CSV file
write.csv(prediction_data, "crab_price_predictions_updated_tariff.csv", row.names = FALSE)

# 14. Print summary of changes made
cat("Updated Tariff_Shock for", sum(model_data$Date >= tariff_period_start & model_data$Date <= tariff_period_end), 
    "observations from Nov 2024 to Dec 2025\n")
cat("Saved predictions to: crab_price_predictions_updated_tariff.csv\n")

# 15. Show a sample of the updated predictions for the tariff period
cat("\nSample of updated predictions for the tariff period:\n")
head(prediction_data[prediction_data$Date >= tariff_period_start & prediction_data$Date <= tariff_period_end, 
                     c("Year", "Month", "Tariff_Shock", "Tariff_Shock_Updated", "predicted_price")])