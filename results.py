import os
import pandas as pd
import shutil
import logging
from CONFIG import ROOT_URL
import logging

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
            self.existing_titles = set(existing_df['name'].astype(str).tolist())
        else:
            self.existing_titles = set()

    def get_domain_name(self, url):
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")

    def append_results(self, product_details, batch_processed_urls_titles):
        """
        Append new product details to the results list, ensuring no duplicates.
        """
        new_products = []
        # remove None from product_details
        product_details = [product for product in product_details if product is not None]
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
        self.save_urls_to_txt(batch_processed_urls_titles)
    
    def save_urls_to_txt(self, batch_processed_urls_titles):
        """
        Save the processed URLs to a text file.
        """
        with open(os.path.join(self.results_folder, 'processed_urls.txt'), 'a') as f:
            for url_title in batch_processed_urls_titles:
                f.write(f"{url_title["title"]}: {url_title['url']}\n")

        with open(os.path.join(self.results_folder, 'processed_titles.txt'), 'a') as f:
            for url_title in batch_processed_urls_titles:
                if url_title["title"] != "Title not found":
                    f.write(f"{url_title['title']}\n")

    def save_to_excel(self):
        """
        Save the products list to an Excel file, ensuring no duplicates, and add a 'keywords' column.
        """
        # Rename columns
        df = pd.DataFrame(self.products)
        df.rename(columns={'title': 'name', 'image': 'image_url'}, inplace=True)

        # Reorder columns
        df = df[['name', 'description', 'price', 'url', 'image_url']]

        # Add the 'keywords' column with the same content as 'name'
        df['keywords'] = df['name']

        if os.path.exists(self.results_file):
            # Read existing data
            existing_df = pd.read_excel(self.results_file)
            # Rename and reorder existing data to match the new format
            existing_df.rename(columns={'title': 'name', 'image': 'image_url'}, inplace=True)
            existing_df = existing_df[['name', 'description', 'price', 'url', 'image_url']]
            
            # Add the 'keywords' column to existing data as well
            existing_df['keywords'] = existing_df['name']

            # Combine new and existing data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Drop duplicates based on 'name'
            combined_df.drop_duplicates(subset=['name'], inplace=True)

            # Sort alphabetically by 'name'
            combined_df = combined_df.sort_values(by='name')
            
            # Save combined data back to Excel
            combined_df.to_excel(self.results_file, index=False)
            self.total_products = len(combined_df)
            self.seen_titles = combined_df['name'].astype(str).tolist()
        else:
            # Drop duplicates in current batch based on 'name'
            df.drop_duplicates(subset=['name'], inplace=True)

            # Sort alphabetically by 'name'
            df = df.sort_values(by='name')
            
            df.to_excel(self.results_file, index=False)
            self.total_products = len(df)
            self.seen_titles = df['name'].astype(str).tolist()

        logging.info(f"Saved {self.total_products} products.")

        # Clear the products list after saving
        self.products = []

    def save_to_txt(self):
        """
        Save the products list to a text file.
        """
        with open(os.path.join(self.results_folder, 'products.txt'), 'a') as f:
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

    def get_processed_urls(self):
        # load them from the txt file if file doesn't exist return empty list
        if os.path.exists(os.path.join(self.results_folder, 'processed_urls.txt')):
            with open(os.path.join(self.results_folder, 'processed_urls.txt'), 'r') as f:
                processed_urls = [line.strip() for line in f.readlines()]
            return processed_urls
        else:
            return []
        
    def get_processed_titles(self):
        # load them from the txt file if file doesn't exist return empty list
        if os.path.exists(os.path.join(self.results_folder, 'processed_titles.txt')):
            with open(os.path.join(self.results_folder, 'processed_titles.txt'), 'r') as f:
                processed_titles = [line.strip() for line in f.readlines()]
            return processed_titles
        else:
            return []

def get_execution_number(root_url, fixed=False):
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

    if fixed:
        return execution_number
    
    execution_number += 1
    with open(execution_file, 'w') as f:
        f.write(str(execution_number))
    return execution_number

def get_domain_name(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc.replace("www.", "")
