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

        # Files for products with stock
        self.results_file_with_stock = os.path.join(self.results_folder, 'products.xlsx')
        self.products_with_stock = []

        # Now assign results_file after defining results_file_with_stock
        self.results_file = self.results_file_with_stock  # For logging

        # Files for products without stock
        self.results_file_without_stock = os.path.join(self.results_folder, 'products_without_stock.xlsx')
        self.products_without_stock = []

        # File for discarded products (without price)
        self.discarded_file = os.path.join(self.results_folder, 'discarded_products.txt')
        self.discarded_products = []

        self.total_products_with_stock = 0
        self.total_products_without_stock = 0
        self.total_discarded_products = 0
        self.total_products = 0
        self.seen_titles = []

        # Copy CONFIG.py to the results folder
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

    def append_results(self, in_stock_products, without_stock_products, discarded_products):
        for product in in_stock_products:
            self.append_product_with_stock(product)

        for product in without_stock_products:
            self.append_product_without_stock(product)

        for product in discarded_products:
            self.append_discarded_product(product['title'], product['url'])

    def append_product_with_stock(self, product):
        if product['title'] not in self.seen_titles:
            self.products_with_stock.append(product)
            self.seen_titles.append(product['title'])
            self.save_to_txt(product, 'products.txt')
            self.save_to_excel(product, self.results_file_with_stock)
            self.total_products_with_stock += 1
            self.total_products += 1
        else:
            logging.info(f"Duplicate product found and skipped: {product['title']}")

    def append_product_without_stock(self, product):
        if product['title'] not in self.seen_titles:
            self.products_without_stock.append(product)
            self.seen_titles.append(product['title'])
            self.save_to_txt(product, 'products_without_stock.txt')
            self.save_to_excel(product, self.results_file_without_stock)
            self.total_products_without_stock += 1
            self.total_products += 1
        else:
            logging.info(f"Duplicate product found and skipped: {product['title']}")

    def append_discarded_product(self, product_title, url):
        discarded_entry = {'title': product_title, 'url': url}
        self.discarded_products.append(discarded_entry)
        self.total_discarded_products += 1
        with open(self.discarded_file, 'a', encoding='utf-8') as f:
            # f.write(f"Producto Descartado: {product_title}\nURL: {url}\n\n")
            f.write(f"{url}\n")

    def save_urls_to_txt(self, batch_processed_urls_titles):
        """
        Save the processed URLs to a text file using UTF-8 encoding.
        """
        # Guardar las URLs procesadas
        with open(os.path.join(self.results_folder, 'processed_urls.txt'), 'a', encoding='utf-8') as f:
            for url_title in batch_processed_urls_titles:
                f.write(f"{url_title['title']}: {url_title['url']}\n")

        # Guardar los títulos procesados
        with open(os.path.join(self.results_folder, 'processed_titles.txt'), 'a', encoding='utf-8') as f:
            for url_title in batch_processed_urls_titles:
                if url_title['title'] != "Title not found":
                    f.write(f"{url_title['title']}\n")

    def save_to_excel(self, product, excel_file):
        """
        Save products to the corresponding Excel file.
        """
        # Create a DataFrame from the product
        df = pd.DataFrame([product])
        df.rename(columns={'title': 'name', 'image': 'image_url'}, inplace=True)
        df = df[['name', 'description', 'price', 'url', 'image_url']]
        df['keywords'] = df['name']

        # Save to Excel
        if os.path.exists(excel_file):
            existing_df = pd.read_excel(excel_file)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.drop_duplicates(subset=['name'], inplace=True)
            combined_df.to_excel(excel_file, index=False)
        else:
            df.to_excel(excel_file, index=False)

    def save_to_excel_bulk(self, products, excel_file):
        """
        Save a list of products to the specified Excel file.
        """
        if not products:
            return

        # Create a DataFrame from the list of products
        df = pd.DataFrame(products)
        df.rename(columns={'title': 'name', 'image': 'image_url'}, inplace=True)
        df = df[['name', 'description', 'price', 'url', 'image_url']]
        df['keywords'] = df['name']

        # Save to Excel
        if os.path.exists(excel_file):
            existing_df = pd.read_excel(excel_file)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.drop_duplicates(subset=['name'], inplace=True)
            combined_df.to_excel(excel_file, index=False)
        else:
            df.to_excel(excel_file, index=False)

    def save_to_txt(self, product, file_name):
        """
        Save products to a TXT file.
        """
        file_path = os.path.join(self.results_folder, file_name)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{product['title']}\n")
            f.write(f"Precio: {product['price']}\n\n")
            f.write(f"{product['description']}\n\n")
            f.write(f"Información extraída de [{product['title']}]({product['url']})\n\n")
            f.write("\n-------\n\n")

    def save_discarded_products(self):
        """
        Save discarded products to a text file.
        """
        discarded_file = os.path.join(self.results_folder, 'discarded_products.txt')
        with open(discarded_file, 'w', encoding='utf-8') as f:
            for product in self.discarded_products:
                # f.write(f"Producto Descartado: {product_title}\nURL: {url}\n\n")
                f.write(f"{product['url']}\n")


    def save_results(self):
        """
        Save all results before finishing the process.
        """
        if self.products_with_stock:
            self.save_to_excel_bulk(self.products_with_stock, self.results_file_with_stock)
        if self.products_without_stock:
            self.save_to_excel_bulk(self.products_without_stock, self.results_file_without_stock)
        if self.discarded_products:
            self.save_discarded_products()

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
