# Load the improved model predictions
model3_improved_predictions <- read.csv("model3_improved_predictions.csv")

# Display the R-squared value of the improved model
cat("Improved model R-squared:", r2_improved, "\n")

# Filter for recent months
recent_months <- model3_improved_predictions[model3_improved_predictions$Dateyyymm %in% 
                                               c("10/1/24", "11/1/24", "12/1/24", "1/1/25", "2/1/25"), ]

# Sort by date
recent_months <- recent_months[order(as.Date(paste0("01/", recent_months$Dateyyymm), format="%d/%m/%y")), ]

# Create a formatted table with actual prices, old predictions, and new predictions
result_table <- data.frame(
  Date = recent_months$Dateyyymm,
  Actual_Price = round(recent_months$UBNL58_lb, 2),
  Old_Predicted = round(recent_months$Predicted_Price, 2),
  New_Predicted = round(recent_months$New_Predicted_Price, 2),
  Lower_CI = round(recent_months$New_Lower_CI, 2),
  Upper_CI = round(recent_months$New_Upper_CI, 2)
)

# Calculate error metrics
result_table$Old_Error = round(result_table$Actual_Price - result_table$Old_Predicted, 2)
result_table$New_Error = round(result_table$Actual_Price - result_table$New_Predicted, 2)
result_table$Old_Error_Pct = round((result_table$Old_Error / result_table$Old_Predicted) * 100, 1)
result_table$New_Error_Pct = round((result_table$New_Error / result_table$New_Predicted) * 100, 1)
result_table$Improvement = round(abs(result_table$Old_Error_Pct) - abs(result_table$New_Error_Pct), 1)

# Print the results
print("Prediction Results for Recent Months:")
print(result_table)

# Print average improvement
cat("\nAverage error reduction:", round(mean(result_table$Improvement), 1), "percentage points\n")

# Check if actual prices are within the new confidence intervals
result_table$Within_CI <- result_table$Actual_Price >= result_table$Lower_CI & 
  result_table$Actual_Price <= result_table$Upper_CI
cat("\nNumber of months where actual price is within CI:", sum(result_table$Within_CI), 
    "out of", nrow(result_table), "\n")

# Print summary statistics for the model coefficients
cat("\nModel Coefficients:\n")
coefficients <- data.frame(summary(model3_improved)$coefficients)
print(coefficients)