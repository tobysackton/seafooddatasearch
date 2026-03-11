# Load necessary libraries
library(tidyverse)
library(lmtest)
library(car)
library(lubridate)

# Load dataset
df <- read.csv("Lobster_Master_shore_Inv_Corrected.csv")

# Convert Date column to date format and check for missing values
df$Date <- as.Date(df$Date, format="%m/%d/%y")

# Check if there are missing or invalid Date values
if (any(is.na(df$Date))) {
  print("Warning: Some Date values are missing. Removing missing dates.")
  df <- df %>% drop_na(Date)
}

# Ensure Date column contains valid finite values
if (all(is.finite(df$Date))) {
  print("Date values are valid.")
} else {
  stop("Error: Found non-finite values in Date column. Please check the dataset.")
}

# Ensure every month from the start to end of the dataset is included
df_complete <- df %>%
  complete(Date = seq.Date(from = min(df$Date, na.rm = TRUE), 
                           to = max(df$Date, na.rm = TRUE), 
                           by = "month"))

# Fill missing values in key predictor variables using forward fill
df_complete <- df_complete %>%
  arrange(Date) %>%
  fill(CA_Export_US_Price_USD, CA_Export_US_Share, USD_JPY_EXCH, USDEUR_EXCH, 
       Estimated_Inventory, Shore_Price_Component_USD, Month_sin, Month_cos, .direction = "down")

# Run multiple regression model with all relevant variables
model <- lm(CA_Export_US_Price_USD ~ CA_Export_US_Share + USD_JPY_EXCH + USDEUR_EXCH + 
              CADUSD_EXCH + Estimated_Inventory + Shore_Price_Component_USD + 
              Month_sin + Month_cos, data = df_complete)

# Display model summary to check R² value and coefficient significance
summary(model)

# Generate predictions
df_complete$Predicted_Price <- predict(model, newdata = df_complete)

# Save results
output_file <- paste0("Lobster_Price_Predictions_Fixed_", Sys.Date(), ".csv")
write.csv(df_complete, output_file, row.names = FALSE)

# Print success message
cat("Predictions successfully written to:", output_file, "\n")