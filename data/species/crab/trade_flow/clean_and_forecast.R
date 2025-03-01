# clean_and_forecast.R
# Script to clean the data and generate proper forecast file

# Set the correct working directory
setwd("/Users/jtsackton/Documents/github_seafood_datasearch/data/species/crab/trade_flow")

# Load necessary libraries
library(dplyr)
library(readr)

# Read the full dataset with model predictions
data <- read_csv("model3_improved_predictions.csv")

# Check for duplicate date entries
date_counts <- table(data$Dateyyymm)
duplicate_dates <- names(date_counts)[date_counts > 1]

if (length(duplicate_dates) > 0) {
  cat("Found duplicate dates:", paste(duplicate_dates, collapse=", "), "\n")
  
  # For each duplicate date, keep only the row with valid data
  deduped_data <- data %>%
    group_by(Dateyyymm) %>%
    # For dates in 2025 after February, keep the row with non-9.11 UBNL58_lb
    # This assumes 9.11 is the copied value from February
    mutate(
      keep_row = if (grepl("^[3-9]/1/25$|^1[0-2]/1/25$", Dateyyymm)) {
        # For Mar-Dec 2025:
        # If any row has UBNL58_lb != 9.11, keep that row
        # Otherwise keep the first row
        if (any(UBNL58_lb != 9.11 & !is.na(UBNL58_lb))) {
          UBNL58_lb != 9.11
        } else {
          row_number() == 1
        }
      } else {
        # For all other dates, keep the first row
        row_number() == 1
      }
    ) %>%
    filter(keep_row) %>%
    ungroup() %>%
    select(-keep_row)
  
  data <- deduped_data
}

# Clear UBNL58_lb for months after February 2025 (future projections)
data <- data %>%
  mutate(
    UBNL58_lb = if_else(
      grepl("^[3-9]/1/25$|^1[0-2]/1/25$", Dateyyymm),
      NA_real_,  # Set to NA for Mar-Dec 2025
      UBNL58_lb  # Keep existing value for other dates
    )
  )

# Make sure we have all 12 months of 2025
months_2025 <- data %>% 
  filter(grepl("^[0-9]+/1/25$", Dateyyymm)) %>%
  pull(Dateyyymm) %>%
  gsub("^([0-9]+)/.*$", "\\1", .) %>%
  as.integer() %>%
  sort()

# Check if we're missing any months
missing_months <- setdiff(1:12, months_2025)

if (length(missing_months) > 0) {
  cat("Missing months for 2025:", paste(missing_months, collapse=", "), "\n")
  
  # Use February as a template for creating new months
  feb_data <- data %>% filter(Dateyyymm == "2/1/25") %>% as.data.frame()
  
  # Create entries for missing months
  for (month in missing_months) {
    new_row <- feb_data
    new_row$Dateyyymm <- paste0(month, "/1/25")
    new_row$Month <- month
    
    # Clear UBNL58_lb for future months
    if (month > 2) {
      new_row$UBNL58_lb <- NA
    }
    
    # Add the new row
    data <- rbind(data, new_row)
  }
}

# Sort the data
data <- data %>%
  arrange(Year, Month)

# Write the cleaned data to the output file
write_csv(data, "crab_price_forecast_2019_2025.csv")

cat("Forecast file has been cleaned and updated.\n")