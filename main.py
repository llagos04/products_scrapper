import asyncio
import logging
import src.crawler as crawler
import src.fetcher as fetcher
import src.results as results
import time
from colorama import init, Fore, Style
from dotenv import load_dotenv
from CONFIG import ROOT_URL, TARGET_PRODUCTS_N, CONCURRENT_REQUESTS, GENERAL_BATCH_SIZE, NUM_WORKERS
import signal
from src.crawler import Crawler
from src.fetcher import ProductFetcher
from src.results import get_execution_number, ResultsManager
import sys

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

async def test_sitemap():
    """Función de prueba para verificar el fetching del sitemap"""
    print(f"Probando fetching del sitemap para: {ROOT_URL}")
    print("=" * 60)

    try:
        # Inicializar crawler
        crawler_instance = Crawler(ROOT_URL, True, [])

        # Obtener todos los sitemaps y URLs
        try:
            from CONFIG import SITEMAP_URL
            custom_sitemap = SITEMAP_URL.strip() if SITEMAP_URL else None
        except ImportError:
            custom_sitemap = None
        all_sitemaps = await crawler_instance.get_all_urls(custom_sitemap)

        print(f"\nResultado: Se encontraron {len(all_sitemaps)} sitemaps")
        print("-" * 40)

        for i, sitemap_data in enumerate(all_sitemaps, 1):
            sitemap_url = sitemap_data['sitemap']
            urls = sitemap_data['urls']
            print(f"\nSitemap {i}: {sitemap_url}")
            print(f"URLs encontradas: {len(urls)}")

            # Mostrar primeras 5 URLs como ejemplo
            if urls:
                print("Primeras URLs:")
                for j, url in enumerate(urls[:5], 1):
                    print(f"  {j}. {url}")
                if len(urls) > 5:
                    print(f"  ... y {len(urls) - 5} más")

        print("\n" + "=" * 60)
        print("Prueba completada exitosamente!")

    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()


async def worker(name, url_queue, results_queue, processed_urls_set):
    """
    Worker task that fetches products in batches from the queue.
    """
    fetcher_instance = ProductFetcher()
    logging.debug(f"Worker {name} started")

    while True:
        try:
            # Get a batch of URLs from the queue
            batch_urls = []
            try:
                # Try to get up to GENERAL_BATCH_SIZE items
                for _ in range(GENERAL_BATCH_SIZE):
                    url = url_queue.get_nowait()
                    if url not in processed_urls_set:
                        batch_urls.append(url)
                        processed_urls_set.add(url)
                    else:
                        url_queue.task_done() # Already processed, mark done
            except asyncio.QueueEmpty:
                pass

            if not batch_urls:
                # If we didn't get any URLs but queue might not be fully empty (race condition) or just empty now
                if url_queue.empty():
                    break
                else:
                    await asyncio.sleep(0.1)
                    continue

            logging.debug(f"Worker {name} processing batch of {len(batch_urls)} URLs")
            
            # Fetch details
            products, discarded = await fetcher_instance.fetch_product_details(
                batch_urls, max_concurrent_requests=CONCURRENT_REQUESTS
            )

            # Put results in results queue
            await results_queue.put((products, discarded))

            # Mark tasks as done
            for _ in batch_urls:
                url_queue.task_done()

        except Exception as e:
            logging.error(f"Worker {name} error: {e}")
            # Ensure we don't hang if there's an error, mark items as done? 
            # Ideally we'd track exactly which ones failed, but for now we log.
            
    logging.debug(f"Worker {name} finished")

async def results_saver(results_queue, results_manager, target_n, total_urls):
    """
    Task to save results from the queue to files. Safe serialization.
    """
    processed_count = 0
    # Initial status
    logging.info(f"Progress: 0/{total_urls} | Found: {results_manager.total_products} | Discarded: {results_manager.total_discarded_products}")

    while True:
        products, discarded = await results_queue.get()
        
        # Save Results
        if products or discarded:
            results_manager.append_results(products, discarded)
            
            # Reconstruct title info for logging processed URLs to txt
            all_urls_titles = []
            for p in products:
                all_urls_titles.append({'url': p['url'], 'title': p['title']})
            for d in discarded:
                all_urls_titles.append({'url': d['url'], 'title': d.get('title', 'Title not found')})
            results_manager.save_urls_to_txt(all_urls_titles)

            processed_count += len(products) + len(discarded)
            
            # Update 'processed_count' based on what results manager knows (safer) if we tracked raw URLs there, 
            # but here calculating local batch size is fine. 
            # Actually, results_manager.total_products + results_manager.total_discarded_products is the most accurate truth.
            total_processed = results_manager.total_products + results_manager.total_discarded_products
            
            logging.info(f"Progress: {total_processed}/{total_urls} ({total_processed/total_urls*100:.1f}%) | Found: {results_manager.total_products} | Discarded: {results_manager.total_discarded_products} | Duplicates: {results_manager.total_duplicates}" + Style.RESET_ALL)
            
            if results_manager.total_products >= target_n:
                logging.info(f"Target number of products ({target_n}) reached.")

        results_queue.task_done()


async def main():
    """
    Main function to orchestrate the web scraping process.
    """
    try:
        logging.info("Starting web scraping process with PARALLEL WORKERS...")

        # Check if the domain is JavaScript-driven
        logging.info(f"Checking if {ROOT_URL} is JavaScript-driven...")
        is_javascript_driven = True 
        logging.info(f"{ROOT_URL} is {'not ' if not is_javascript_driven else ''}JavaScript-driven.")
        
        # Initialize variables
        start_time = time.time()
        processed_urls = set()

        # Import links to ignore from ignore_links.txt
        with open('ignore_links.txt', 'r') as f:
            ignore_links = [line.strip() for line in f.readlines()]

        # Initialize crawler
        crawler_instance = crawler.Crawler(ROOT_URL, is_javascript_driven, ignore_links)

        # Initialize results manager
        execution_number = results.get_execution_number(ROOT_URL)
        results_manager = results.ResultsManager(ROOT_URL, execution_number)

        # Fetch all URLs (from sitemap or crawling)
        logging.info(f"Fetching all URLs from {ROOT_URL}...")

        selected_urls = []
        
        try:
            from CONFIG import MANUAL_LINKS, MAX_PRODUCTS_PER_MANUAL_LINK, SITEMAP_URL
        except ImportError:
            from CONFIG import MANUAL_LINKS, MAX_PRODUCTS_PER_MANUAL_LINK
            SITEMAP_URL = ""
        
        # Si hay enlaces manuales, usarlos directamente y no buscar sitemaps
        if MANUAL_LINKS and any(MANUAL_LINKS):
            logging.info("MANUAL_LINKS detectados. Omitiendo búsqueda de sitemaps...")
            all_sitemaps = await crawler_instance.get_manual_links(MANUAL_LINKS, MAX_PRODUCTS_PER_MANUAL_LINK)
        else:
            custom_sitemap = SITEMAP_URL.strip() if SITEMAP_URL else None
            all_sitemaps = await crawler_instance.get_all_urls(custom_sitemap)

        for sitemap_data in all_sitemaps:
            sitemap, urls = sitemap_data['sitemap'], sitemap_data['urls']
            urls_from_sitemap = manual_sitemap_selection(sitemap, urls)
            selected_urls.extend(urls_from_sitemap)

        logging.info(f"Selected {len(selected_urls)} URLs after manual sitemap filtering.")

        if not selected_urls:
            logging.warning("No URLs selected. Exiting.")
            return

        # Setup Queues
        url_queue = asyncio.Queue()
        for url in selected_urls:
            url_queue.put_nowait(url)
        
        results_queue = asyncio.Queue()

        # Start Results Saver
        saver_task = asyncio.create_task(results_saver(results_queue, results_manager, TARGET_PRODUCTS_N, len(selected_urls)))

        # Start Workers
        num_workers = NUM_WORKERS
        logging.info(f"Starting {num_workers} parallel workers...")
        workers = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(f"Worker-{i+1}", url_queue, results_queue, processed_urls))
            workers.append(task)

        # Wait for all URLs to be processed
        await url_queue.join()
        logging.info("All URLs processed by workers.")

        # Cancel workers (they are in infinite loops waiting for queue, or exited if empty)
        for w in workers:
            w.cancel()
        
        # Wait for all results to be saved
        await results_queue.join()
        
        # Cancel saver
        saver_task.cancel()

        # Final save just in case
        results_manager.save_results()

        total_elapsed_time = time.time() - start_time
        logging.info(Fore.GREEN + Style.BRIGHT + f"Completed web scraping process in {total_elapsed_time:.2f} seconds")
    
    except Exception as e:
        logging.exception(f"An error occurred during the web scraping process: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test_sitemap':
        asyncio.run(test_sitemap())
    else:
        asyncio.run(main())
