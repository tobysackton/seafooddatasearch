# Fix dates and exchange rates in the model data
# Set the working directory
setwd("/Users/jtsackton/Documents/github_seafood_datasearch/data/species/crab/trade_flow")

# Load libraries
library(dplyr)
library(readr)

# Read the model data
data <- read_csv("model3_improved_predictions.csv")

# Check if we have all months for 2025
months_2025 <- data %>% 
  filter(grepl("^[0-9]+/1/25$", Dateyyymm)) %>%
  pull(Month) %>%
  unique() %>%
  sort()

cat("Found 2025 months:", paste(months_2025, collapse=", "), "\n")

# Add any missing months for 2025
missing_months <- setdiff(1:12, months_2025)
if (length(missing_months) > 0) {
  cat("Adding missing months:", paste(missing_months, collapse=", "), "\n")
  
  # Use February as template
  feb_data <- data %>% 
    filter(Dateyyymm == "2/1/25") %>% 
    as.data.frame()
  
  for (month in missing_months) {
    new_row <- feb_data
    new_row$Dateyyymm <- paste0(month, "/1/25")
    new_row$Month <- month
    
    # Clear actual price for future months
    if (month > 2) {
      new_row$UBNL58_lb <- NA
    }
    
    # Add to data
    data <- rbind(data, new_row)
  }
}

# Now apply the exchange rate adjustment - 3% weakening over Mar-Dec 2025
# Get February 2025 exchange rate
feb_2025_exchange <- data %>%
  filter(Dateyyymm == "2/1/25") %>%
  pull(CADUSDEXCH)

cat("February 2025 exchange rate:", feb_2025_exchange, "\n")

# Apply progressive weakening
if (!is.na(feb_2025_exchange)) {
  total_months <- 10 # Mar-Dec
  
  for (month in 3:12) {
    # Calculate progressive weakening (0% in Feb to 3% in Dec)
    months_since_feb <- month - 2
    increase_percent <- (months_since_feb / total_months) * 3
    
    # New exchange rate with weakening applied (higher = weaker CAD)
    new_exchange_rate <- feb_2025_exchange * (1 + increase_percent / 100)
    
    # Update the exchange rate
    date_string <- paste0(month, "/1/25")
    data$CADUSDEXCH[data$Dateyyymm == date_string] <- new_exchange_rate
    
    # Calculate log value too
    data$log_CADUSDEXCH[data$Dateyyymm == date_string] <- log(new_exchange_rate)
    
    cat(sprintf("Updated %s exchange rate to %.6f (%.2f%% increase)\n", 
                date_string, new_exchange_rate, increase_percent))
  }
}

# Make sure all 2025 dates after February have NA for UBNL58_lb
data <- data %>%
  mutate(
    UBNL58_lb = if_else(
      grepl("^[3-9]/1/25$|^1[0-2]/1/25$", Dateyyymm),
      NA_real_,
      UBNL58_lb
    )
  )

# Write the updated data back
write_csv(data, "model3_improved_predictions.csv")

cat("\nUpdated file with proper dates and exchange rates\n")
cat("Total rows:", nrow(data), "\n")
cat("2025 months included:", paste(sort(unique(data$Month[grepl("1/25$", data$Dateyyymm)])), collapse=", "), "\n")source()