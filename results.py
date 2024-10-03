import os
import pandas as pd
import shutil
import logging
from CONFIG import ROOT_URL

class ResultsManager:
    def __init__(self, root_url, execution_number):
        self.root_url = root_url
        self.execution_number = execution_number
        self.domain_name = self.get_domain_name(root_url)
        self.results_folder = os.path.join('results', self.domain_name, f'execution_{execution_number}')
        os.makedirs(self.results_folder, exist_ok=True)
        self.results_file = os.path.join(self.results_folder, 'products.xlsx')
        self.products = []
        self.total_products = 0
        self.seen_titles = []

        # Copy CONFIG.py to results folder
        shutil.copy('CONFIG.py', self.results_folder)

        # Load existing product titles to avoid duplicates
        if os.path.exists(self.results_file):
            existing_df = pd.read_excel(self.results_file)
            self.existing_titles = set(existing_df['title'].astype(str).tolist())
        else:
            self.existing_titles = set()

    def get_domain_name(self, url):
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")

    def append_results(self, product_details):
        """
        Append new product details to the results list, ensuring no duplicates.
        """
        new_products = []
        for product in product_details:
            title = str(product.get('title', '')).strip()
            if title not in self.existing_titles:
                new_products.append(product)
                self.existing_titles.add(title)
            else:
                logging.info(f"Duplicate product found and skipped: {title}")

        if new_products:
            self.products.extend(new_products)
            # Save to both Excel and TXT before clearing the products list
            self.save_to_txt()
            self.save_to_excel()
        else:
            logging.info("No new unique products to save.")

    def save_to_excel(self):
        """
        Save the products list to an Excel file, ensuring no duplicates.
        """
        df = pd.DataFrame(self.products)

        if os.path.exists(self.results_file):
            # Read existing data
            existing_df = pd.read_excel(self.results_file)
            # Combine new and existing data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Drop duplicates based on 'title'
            combined_df.drop_duplicates(subset=['title'], inplace=True)
            # Save combined data back to Excel
            combined_df.to_excel(self.results_file, index=False)
            self.total_products = len(combined_df)
            self.seen_titles = combined_df['title'].astype(str).tolist()
        else:
            # Drop duplicates in current batch
            df.drop_duplicates(subset=['title'], inplace=True)
            df.to_excel(self.results_file, index=False)
            self.total_products = len(df)
            self.seen_titles = df['title'].astype(str).tolist()
        
        logging.info(f"Saved {self.total_products} products.")

        # Clear the products list after saving
        self.products = []

    def save_to_txt(self):
        """
        Save the products list to a text file.
        """
        with open(os.path.join(self.results_folder, 'products.txt'), 'w') as f:
            for product in self.products:
                f.write(f"{product['title']}\n")
                f.write(f"Precio: {product['price']}\n\n")
                f.write(f"{product['description']}\n\n")
                f.write(f"Información extraída de [{product['title']}]({product['url']})\n\n")
                f.write("-------\n\n")

    def save_results(self):
        """
        Final save of results.
        """
        if self.products:
            self.save_to_excel()
            self.save_to_txt()

def get_execution_number(root_url):
    """
    Read n.txt, increment the execution number, save it back, and return the new execution number.
    """
    domain_name = get_domain_name(root_url)
    execution_file = os.path.join('results', domain_name, 'n.txt')
    os.makedirs(os.path.dirname(execution_file), exist_ok=True)

    if os.path.exists(execution_file):
        with open(execution_file, 'r') as f:
            execution_number = int(f.read())
    else:
        execution_number = 0
    execution_number += 1
    with open(execution_file, 'w') as f:
        f.write(str(execution_number))
    return execution_number

def get_domain_name(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc.replace("www.", "")
