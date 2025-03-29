#THIS KEEPS JUST THE FIRST 4 columns

import pandas as pd

# Load the Excel file
df = pd.read_excel('concert_tickets.xlsx')

# Keep only the first 4 columns
df.iloc[:, :4].to_csv('concert_tickets.csv', index=False)