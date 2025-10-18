import pandas as pd

# Load the Excel file
df = pd.read_excel("Datasets/Arrests.xlsx")

# Print the exact column names
print(df.columns.tolist())
