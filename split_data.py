import pandas as pd
import csv

# Read the CSV file
data = pd.read_csv('data-1716872464964.csv')

splits = 6000
num_rows = len(data) // splits
print(num_rows)

pieces = [data[i*num_rows:(i+1)*num_rows] for i in range(splits)]

# Print the first few rows of each piece
for i, piece in enumerate(pieces):
    print(f"Piece {i+1}:")
    print(piece.head())
    print()
    piece.to_csv(f'data/piece_{i+1}.csv', index=False, quoting=csv.QUOTE_NONNUMERIC, quotechar='"', encoding='utf-8')