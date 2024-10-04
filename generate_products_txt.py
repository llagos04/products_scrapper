import pandas as pd

def excel_to_txt(source_path, destination_path):
    # Read the Excel file
    df = pd.read_excel(source_path)

    # Initialize a list to store each product's formatted text
    output = []

    # Loop through each row in the dataframe
    for index, row in df.iterrows():
        # Extract fields from the current row
        name = row['name']
        description = row['description']
        price = row['price']
        url = row['url']

        # Create the formatted text for the current product
        product_text = f"{name}\nPrecio: {price} (IVA incluido)\n\n{description}\n\nInformación extraída de [{name}]({url})\n\n-------\n"
        
        # Append the formatted text to the output list
        output.append(product_text)

    # Join all the product texts into a single string
    final_output = "\n".join(output)

    # Write the final output to the specified destination file
    with open(destination_path, 'w', encoding='utf-8') as f:
        f.write(final_output)

# Example usage:
source_path = 'results/canelonsbarcelona.com/execution_10/products_modified.xlsx'  # Replace with your source Excel file path
destination_path = 'results/canelonsbarcelona.com/execution_10/products.txt'  # Replace with your destination text file path
excel_to_txt(source_path, destination_path)