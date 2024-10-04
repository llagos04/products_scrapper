# delete duplicates from a txt

import os
import pandas as pd

source = "results/kundebrand.com/execution_7/processed_titles.txt"

# Read the text file
with open(source, 'r') as file:
    urls = file.read().splitlines()

# Create a DataFrame from the URLs
df = pd.DataFrame({'url': urls})

# Remove duplicates
df = df.drop_duplicates()

# Save the DataFrame to a new text file
with open(source, 'w') as file:
    for url in df['url']:
        file.write(url + '\n')