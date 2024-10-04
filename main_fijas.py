import asyncio
import logging
import crawler
import fetcher
import analizer
import results
import time
from colorama import init, Fore, Style
from dotenv import load_dotenv
from CONFIG import ROOT_URL, LLM_BATCH_SIZE, TARGET_PRODUCTS_N, CONCURRENT_REQUESTS, GENERAL_BATCH_SIZE
import signal

URLS = [
    "https://depataverde.es/therapy-cbd",
    "https://depataverde.es/comprar-cogollos-marihuana-online",
    "https://depataverde.es/strawberry-cbd",
    "https://depataverde.es/skywalker-og-cbd",
    "https://depataverde.es/comprar-cogollos-canamo-dpv",
    "https://depataverde.es/cannatonic-cbg",
    "https://depataverde.es/biomasa-canamo-kompolti",
    "https://depataverde.es/aceite-cbd-30-cannactiva",
    "https://depataverde.es/aceite-cbd-30-dpv",
    "https://depataverde.es/aceite-cbd-mascotas",
    "https://depataverde.es/crema-sensible-cbd-formula-swiss",
    "https://depataverde.es/locion-corporal-cbd-cannactiva",
    "https://depataverde.es/aceite-cbd-20-cannactiva",
    "https://depataverde.es/aceite-cbd-10-cannactiva",
    "https://depataverde.es/aceite-cbd-20-manna",
    "https://depataverde.es/aceite-ohcbd-5",
    "",
    "",
    "",
    "",

    ]

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

# Configure logging for both file and console output
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s -\t%(message)s',
                    handlers=[
                        logging.FileHandler('scraper.log', mode='w'),
                        logging.StreamHandler()
                    ])

logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

async def main():
    """
    Main function to orchestrate the web scraping process.
    """
    try:
        logging.info("Starting web scraping process...")

        # Check if the domain is JavaScript-driven
        logging.info(f"Checking if {ROOT_URL} is JavaScript-driven...")
        is_javascript_driven = await crawler.is_javascript_driven_async(ROOT_URL)
        logging.info(f"{ROOT_URL} is {'not ' if not is_javascript_driven else ''}JavaScript-driven.")

        # Initialize variables
        total_products_found = 0
        iterations = 0
        processed_urls = set()
        start_time = time.time()

        # import links to ignore from ignore_links.txt
        with open('ignore_links.txt', 'r') as f:
            ignore_links = [line.strip() for line in f.readlines()]

        # Initialize crawler
        crawler_instance = crawler.Crawler(ROOT_URL, is_javascript_driven, ignore_links)

        # Initialize results manager
        execution_number = results.get_execution_number(ROOT_URL, fixed=True)
        results_manager = results.ResultsManager(ROOT_URL, execution_number)

        batch_urls_to_process = URLS

        # Fetch Titles
        logging.info(f"Fetching titles for {len(batch_urls_to_process)} URLs...")
        start_time_fetch_titles = time.time()
        url_titles = await fetcher.fetch_titles(batch_urls_to_process, max_concurrent_requests=CONCURRENT_REQUESTS)
        elapsed_time_fetch_titles = time.time() - start_time_fetch_titles
        logging.info(Fore.GREEN + f"Fetched titles for {len(url_titles)} URLs in {elapsed_time_fetch_titles:.2f} seconds\n" + Style.RESET_ALL)

        all_urls_titles = []
        urls_titles_found = [url_title["url"] for url_title in url_titles]
        urls_titles_not_found = [url for url in batch_urls_to_process if url not in urls_titles_found]
        all_urls_titles.extend(url_titles)
        for url in urls_titles_not_found:
            all_urls_titles.append({"url": url, "title": "Title not found"})
        results_manager.save_urls_to_txt(all_urls_titles)
        
        if len(url_titles) > 5:
            logging.info(f"Last 5 fetched titles:\n\t\t{"\n\t\t".join([url_title["title"] for url_title in url_titles[-5:]])}\n")
        else:
            logging.info(f"Fetched titles:\n\t\t{"\n\t\t".join([url_title["title"] for url_title in url_titles])}\n")

        # discard existing titles
        url_titles = [title for title in url_titles if title not in results_manager.seen_titles]

        product_urls_titles = url_titles
        
        # Fetch Product Details
        logging.info(f"Fetching product details for {len(product_urls_titles)} product URLs...")
        start_time_fetch_details = time.time()
        product_details = await fetcher.fetch_product_details(product_urls_titles, max_concurrent_requests=CONCURRENT_REQUESTS)
        elapsed_time_fetch_details = time.time() - start_time_fetch_details
        logging.info(Fore.GREEN + f"Fetched {len(product_details)} product details in {elapsed_time_fetch_details:.2f} seconds\n" + Style.RESET_ALL)

        # Update total products found
        total_products_found += len(product_details)
        logging.info(f"Total products found so far: {total_products_found}")

        # Save Results
        logging.info("Saving results...")
        start_time_save_results = time.time()
        results_manager.append_results(product_details, all_urls_titles)
        elapsed_time_save_results = time.time() - start_time_save_results
        logging.info(Fore.GREEN  + f"Saved {results_manager.total_products} unique products to {results_manager.results_file}\n" + Style.RESET_ALL)
        
        # Final save
        results_manager.save_results()

        total_elapsed_time = time.time() - start_time
        logging.info(Fore.GREEN + Style.BRIGHT + f"Completed web scraping process in {total_elapsed_time:.2f} seconds")

    except Exception as e:
        logging.exception(f"An error occurred during the web scraping process: {e}")

if __name__ == '__main__':
    asyncio.run(main())