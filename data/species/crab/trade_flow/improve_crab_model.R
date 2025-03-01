# Load necessary libraries
library(readr)

# Load the data
model3_update <- read.csv("model3_predictions_updated.csv")

# Add new market shock factor
model3_update$Market_Shock_2025 <- 0
model3_update$Market_Shock_2025[model3_update$Dateyyymm %in% c("11/1/24", "12/1/24", "1/1/25", "2/1/25")] <- 1

# Create the updated model
model3_improved <- lm(log_UBNL58_lb ~ log_CAUS_Total + log_USD_Cost + CADUSDEXCH + 
                Season_Factor_1 + Pandemic_Shock + Market_Shock_Factor + 
                Extra_Demand_Factor + Tariff_Shock + Market_Shock_2025 +
                log_USD_Cost:CADUSDEXCH, 
              data = model3_update)

# Print model performance
cat("Original model R-squared:", 0.9073625, "\n")
cat("Improved model R-squared:", summary(model3_improved)$r.squared, "\n")

# Make predictions with the improved model
predictions <- predict(model3_improved, newdata = model3_update, interval = "confidence", level = 0.95)

# Convert log predictions back to original scale
model3_update$New_Predicted_Price <- exp(predictions[,"fit"])
model3_update$New_Lower_CI <- exp(predictions[,"lwr"])
model3_update$New_Upper_CI <- exp(predictions[,"upr"])

# Print comparison for recent months
recent_months <- model3_update[model3_update$Dateyyymm %in% c("11/1/24", "12/1/24", "1/1/25", "2/1/25"), ]
print(recent_months[, c("Dateyyymm", "UBNL58_lb", "Predicted_Price", "New_Predicted_Price", "New_Lower_CI", "New_Upper_CI")])

# Save the results
write.csv(model3_update, "model3_improved_predictions.csv", row.names = FALSE)