import os
import pandas as pd

# load the names from a txt
# load the names from a column of a excel
# generate another txt the names that don't match between the two

source_txt = "results/kundebrand.com/execution_7/processed_titles.txt"
source_excel = "results/kundebrand.com/execution_7/products.xlsx"

# load the names from a txt
with open(source_txt, 'r') as file:
    txt_names = file.read().splitlines()

# load the names from a column of a excel
df = pd.read_excel(source_excel)
excel_names = df['name'].tolist()

# generate another txt the names that don't match between the two
with open('results/kundebrand.com/execution_7/missing_titles.txt', 'w') as file:
    for name in txt_names:
        if name not in excel_names:
            file.write(name + '\n')