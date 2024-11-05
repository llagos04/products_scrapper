import asyncio
import logging
import src.crawler as crawler
import src.fetcher as fetcher
import src.analizer as analizer
import src.results as results
import time
from colorama import init, Fore, Style
from dotenv import load_dotenv
from CONFIG import ROOT_URL, LLM_BATCH_SIZE, TARGET_PRODUCTS_N, CONCURRENT_REQUESTS, GENERAL_BATCH_SIZE, IGNORE_URLS_WITH
import signal

load_dotenv()
init()  # Initialize Colorama

# Custom log level formatting with color and style
class ColorFormatter(logging.Formatter):
    def __init__(self, fmt):
        super().__init__(fmt)

    def format(self, record):
        levelname = record.levelname
        if levelname == "INFO":
            record.levelname = f"{Fore.GREEN}{levelname}{Style.RESET_ALL}"
        elif levelname == "WARNING":
            record.levelname = f"{Fore.YELLOW}{levelname}{Style.RESET_ALL}"
        elif levelname == "ERROR":
            record.levelname = f"{Fore.RED}{levelname}{Style.RESET_ALL}"
        elif levelname == "DEBUG":
            record.levelname = f"{Fore.BLUE}{levelname}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging for both file and console output with color
logging.basicConfig(level=logging.INFO,
                    format=f'{Style.BRIGHT}%(levelname)s -\t%(message)s{Style.RESET_ALL}',
                    handlers=[
                        logging.FileHandler('scraper.log', mode='w'),
                        logging.StreamHandler()
                    ])
for handler in logging.root.handlers:
    handler.setFormatter(ColorFormatter(handler.formatter._fmt))

logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

def filter_urls(urls, results_manager):
    # get the set of processed URLs
    processed_urls = results_manager.get_processed_urls()

    # filter out processed URLs
    filtered_urls = [url for url in urls if url not in processed_urls]

    # remove duplicates
    filtered_urls = list(set(filtered_urls))

    # IGNORE_URLS_WITH
    filtered_urls = [url for url in filtered_urls if not IGNORE_URLS_WITH in url]

    return filtered_urls

def filter_titles(urls_titles, results_manager):
    # get the set of processed URLs
    processed_titles = results_manager.get_processed_titles()

    # filter out processed URLs
    filtered_urls_titles = [url_title for url_title in urls_titles if url_title["title"] not in processed_titles]

    # remove duplicates
    filtered_urls_titles_copy = filtered_urls_titles.copy()
    filtered_urls_titles = []
    for url_title in filtered_urls_titles_copy:
        if url_title["title"] not in processed_titles:
            filtered_urls_titles.append(url_title)

    return filtered_urls_titles



def manual_sitemap_selection(sitemap, urls):
    """
    Presenta el sitemap al usuario para que decida si contiene productos.
    Si responde que sí, se seleccionan todas las URLs; si no, se descartan.
    """
    print(f"\nEste sitemap contiene los siguientes URLs:")
    print(sitemap)
    for url in urls:
        print(f"  ├── {url}")
    
    user_input = input("\n¿Este sitemap contiene productos? (Sí/No): ").strip().lower()
    if user_input in ['sí', 'si', 's']:
        return urls  # Si elige "sí", se devuelven todas las URLs
    else:
        return []  # Si elige "no", se descartan todas las URLs

async def main():
    """
    Main function to orchestrate the web scraping process.
    """
    try:
        logging.info("Starting web scraping process...")

        # Check if the domain is JavaScript-driven
        logging.info(f"Checking if {ROOT_URL} is JavaScript-driven...")
        is_javascript_driven = await crawler.is_javascript_driven_async(ROOT_URL)
        is_javascript_driven = True  # Forcing JavaScript-driven for now
        logging.info(f"{ROOT_URL} is {'not ' if not is_javascript_driven else ''}JavaScript-driven.")
        
        # Initialize variables
        total_products_found = 0
        iterations = 0
        processed_urls = set()
        start_time = time.time()

        # Import links to ignore from ignore_links.txt
        with open('ignore_links.txt', 'r') as f:
            ignore_links = [line.strip() for line in f.readlines()]

        # Initialize crawler
        crawler_instance = crawler.Crawler(ROOT_URL, is_javascript_driven, ignore_links)

        # Initialize results manager
        execution_number = results.get_execution_number(ROOT_URL)
        results_manager = results.ResultsManager(ROOT_URL, execution_number)

        # Define a signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logging.info('You pressed Ctrl+C! Saving results and exiting...')
            results_manager.save_results()
            exit(0)
        signal.signal(signal.SIGINT, signal_handler)

        # Fetch all URLs (from sitemap or crawling)
        logging.info(f"Fetching all URLs from {ROOT_URL}...")
        all_sitemaps = await crawler_instance.get_all_urls()

        selected_urls = []
        
        # Recorrer la lista de sitemaps y sus URLs asociadas
        for sitemap_data in all_sitemaps:
            sitemap, urls = sitemap_data['sitemap'], sitemap_data['urls']
            urls_from_sitemap = manual_sitemap_selection(sitemap, urls)
            selected_urls.extend(urls_from_sitemap)

        # LOG adicional: mostrar todas las URLs seleccionadas
        logging.info(f"Selected {len(selected_urls)} URLs after manual sitemap filtering.")
        
        # If there are no manually selected URLs, proceed with crawling or LLM analysis
        if not selected_urls:
            logging.info("No URLs selected manually. Proceeding with crawling or LLM-based filtering...")
            # Perform crawling (if not already done) or use LLM for product selection

            # If we have no sitemaps or filtered URLs, we'll use the crawling method and the LLM
            crawling_urls = await crawler_instance.get_all_urls_by_crawling()
            logging.info(f"Found {len(crawling_urls)} URLs via crawling.")

            if crawling_urls:
                logging.info(f"Using LLM to filter product URLs from {len(crawling_urls)} crawled URLs...")
                url_titles = await fetcher.fetch_titles(crawling_urls, max_concurrent_requests=CONCURRENT_REQUESTS)

                # Use LLM to identify product URLs
                product_urls_titles = await analizer.select_product_urls(url_titles, LLM_BATCH_SIZE)
                selected_urls = [url_title['url'] for url_title in product_urls_titles]
                logging.info(f"LLM identified {len(selected_urls)} product URLs.")
            else:
                logging.info("No URLs found through crawling or sitemap.")
                return

        # Variables to keep track of counts
        total_products_found = 0
        total_without_stock = 0
        total_discarded = 0
        total_urls_processed = 0
        total_urls_to_process = len(selected_urls)

        # Process the URLs in batches
        while total_products_found < TARGET_PRODUCTS_N and selected_urls:
            start_iteration_time = time.time()
            iterations += 1
            logging.info(Fore.GREEN + Style.BRIGHT + f"############### START ITERATION {iterations} ###############\n" + Style.RESET_ALL)
            
            # Get the next batch of URLs
            batch_urls = selected_urls[:GENERAL_BATCH_SIZE]
            selected_urls = selected_urls[GENERAL_BATCH_SIZE:]  # Remove processed URLs from the list

            if not batch_urls:
                logging.info("No more URLs to process.")
                break

            # Remove already processed URLs
            batch_urls_to_process = [url for url in batch_urls if url not in processed_urls]
            # Update processed URLs
            processed_urls.update(batch_urls_to_process)


            # Fetch Titles
            start_time_fetch_titles = time.time()
            url_titles = await fetcher.fetch_titles(batch_urls_to_process, max_concurrent_requests=CONCURRENT_REQUESTS)
            elapsed_time_fetch_titles = time.time() - start_time_fetch_titles

            all_urls_titles = []
            urls_titles_found = [url_title["url"] for url_title in url_titles]
            urls_titles_not_found = [url for url in batch_urls_to_process if url not in urls_titles_found]
            all_urls_titles.extend(url_titles)
            for url in urls_titles_not_found:
                all_urls_titles.append({"url": url, "title": "Title not found"})
            results_manager.save_urls_to_txt(all_urls_titles)
            
            
            # Ahora pasamos la lista de diccionarios con 'url' y 'title' a fetch_product_details
            
            start_time_fetch_details = time.time()
            
            # Fetch product details
            in_stock_products, without_stock_products, discarded_products = await fetcher.fetch_product_details(
                all_urls_titles, max_concurrent_requests=CONCURRENT_REQUESTS
            )

            # Save Results
            start_time_save_results = time.time()
            results_manager.append_results(in_stock_products, without_stock_products, discarded_products)
            elapsed_time_save_results = time.time() - start_time_save_results

            logging.info(f"Products with stock: {results_manager.total_products_with_stock}" + Style.RESET_ALL)
            logging.info(f"Products without stock: {results_manager.total_products_without_stock}" + Style.RESET_ALL)
            logging.info(f"Discarded products: {results_manager.total_discarded_products}" + Style.RESET_ALL)
            logging.info(f"Total products processed: {results_manager.total_products_with_stock + results_manager.total_products_without_stock + results_manager.total_discarded_products}" + Style.RESET_ALL)
            logging.info(f"Total URLs to process: {total_urls_to_process}" + Style.RESET_ALL)
            
            elapsed_iteration_time = time.time() - start_iteration_time
            logging.info(Fore.GREEN + Style.BRIGHT + f"Completed iteration {iterations} in {elapsed_iteration_time:.2f} seconds" + Style.RESET_ALL)
            
            # Check if TARGET_PRODUCTS_N is reached
            if results_manager.total_products_with_stock >= TARGET_PRODUCTS_N:
                logging.info(f"Target number of products ({TARGET_PRODUCTS_N}) reached.")
                break
            if total_urls_processed >= total_urls_to_process:
                logging.info(f"Target maximum number of products ({total_urls_to_process}) reached.")
                break

        # Final save
        results_manager.save_results()

        total_elapsed_time = time.time() - start_time
        logging.info(Fore.GREEN + Style.BRIGHT + f"Completed web scraping process in {total_elapsed_time:.2f} seconds")
    
    except Exception as e:
        logging.exception(f"An error occurred during the web scraping process: {e}")



if __name__ == '__main__':
    asyncio.run(main())
