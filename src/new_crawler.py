import asyncio
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse
import re
import time
import pickle
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
# import matplotlib to save to file a simple plot
import matplotlib.pyplot as plt

import logging
from colorama import init, Fore, Style

from datetime import datetime

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

class NewCrawler:
    def __init__(self, root_url, concurrency=100, batch_size=10, n_retries=3, timeout=10, use_last_state = False):
        # logging.info(f"Initializing crawler for {root_url} with {concurrency} concurrency and {batch_size} batch size")
        self.root_url = root_url                # Root URL to crawl
        self.concurrency = concurrency          # Max concurrent fetches (Semaphore: total tasks)
        self.batch_size = batch_size            # URLs to retrieve per batch
        self.use_last_state = use_last_state    # Use last state if exists
        self.n_retries = n_retries              # Max number of retries
        self.timeout = timeout                  # Timeout for HTTP requests

        self.visited_urls = set()               # Set of visited URLs
        self.seen_urls = set()                  # Set of seen URLs (used for deduplication)
        self.urls_to_visit = asyncio.Queue()    # Queue of URLs to visit
        self.urls_to_visit.put_nowait(root_url) # Add root to queue
        self.discovered_urls = asyncio.Queue()  # Queue of newly discovered URLs
        self.total_urls_batched = 0             # Total number of URLs batched
        self.total_batches = 0                  # Total number of batches
        self.mean_batching_time = 0             # Mean time to batch URLs

        self.historical_batches_mean_batching_time = []

        self.session = None     # aiohttp ClientSession
        self.playwright = None  # Playwright instance (for JS-heavy pages)
        self.browser = None     # Chromium browser    (for JS-heavy pages)

        self.crawling_task = None       # Crawler task
        self.save_state_interval = 10  # Save state every x seconds

        # get root folder (.. of this file)
        current_root_folder = os.path.dirname(os.path.abspath(__file__))
        self.root_folder = os.path.join(current_root_folder, '..')

        # Load state if exists
        if self.use_last_state:
            self.load_state()

    async def start(self):
        # logging.info(f"Starting crawler: async playwright, chromium browser and http client session")
        self.session = ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.crawling_task = asyncio.create_task(self.crawl())
        # logging.info(f"Crawler started:\n\tPlaywright: {self.playwright}\n\tBrowser: {self.browser}\n\tSession: {self.session}")

        # Start periodic state saving
        asyncio.create_task(self.periodic_state_save())

    async def stop(self):
        self.crawling_task.cancel()
        await self.session.close()
        await self.browser.close()
        await self.playwright.stop()
        self.save_state()

    async def crawl(self):
        # Handles the contious crawling of URLs
        # logging.info(f"Starting crawling loop")

        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = []

        iterations = 0

        while True:
            iterations += 1
            # logging.info(f"Starting iteration {iterations}")
            try:
                url = await self.urls_to_visit.get() # Get URL from queue
                if url in self.visited_urls:
                    continue
                # logging.info(f"Visiting {url}")
                self.visited_urls.add(url) # Mark URL as visited
                tasks.append(asyncio.create_task(self.fetch(url, semaphore))) # Add task to queue to fetch sub-pages

                if len(tasks) >= self.concurrency: # If queue is full, wait for tasks to complete
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = [t for t in tasks if not t.done()]
            except asyncio.CancelledError:
                break

    async def fetch(self, url, semaphore):
        # logging.info(f"Fetching {url}")
        async with semaphore:
            for attempt in range(5):
                # logging.info(f"Attempt {attempt + 1} for {url}")
                try:
                    async with self.session.get(url, timeout=10) as response:
                        if response.status != 200:
                            logging.error(f"\tFailed to fetch {url} with status code {response.status}")
                            return
                        content_type = response.headers.get('Content-Type', '')
                        if 'text/html' not in content_type:
                            # logging.info(f"\tSkipping non-HTML URL: {url}")
                            return
                        text = await response.text()

                        # logging.info(f"\tSuccessfully fetched {url}:\n{text[:100]}...")

                        # Heuristic to detect JS-heavy pages
                        if self.is_javascript_heavy(text):
                            # logging.info(f"\tDetected JS-heavy page: {url}")
                            await self.fetch_with_playwright(url)
                        else:
                            # logging.info(f"\tDetected non-JS-heavy page: {url}")
                            await self.parse_and_enqueue(url, text)
                        return
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    await asyncio.sleep(2 ** attempt)
            # Log failure after retries
            print(f"Failed to fetch {url} after retries")

   
    def is_javascript_heavy(self,html):
        # logging.info(f"\tChecking if url is JS-heavy")
        soup = BeautifulSoup(html, 'lxml')
        
        # Check for heavy script content
        scripts = soup.find_all('script')
        external_scripts = [script for script in scripts if script.get('src')]
        inline_scripts = [script for script in scripts if not script.get('src')]
        
        # Calculate total script size for inline scripts
        inline_script_content = ''.join(script.text for script in inline_scripts)
        inline_script_size = len(inline_script_content)
        
        # Heuristics to detect JS frameworks
        js_framework_patterns = {
            'React': r'data-reactroot|data-reactid',
            'Angular': r'ng-app|ng-controller',
            'Vue': r'v-bind|v-model'
        }
        
        # Check for framework-specific attributes or large inline scripts
        framework_detected = any(re.search(pattern, html) for pattern in js_framework_patterns.values())
        heavy_script_use = len(external_scripts) > 5 or inline_script_size > 20000  # Example thresholds

        return framework_detected or heavy_script_use

    async def fetch_with_playwright(self, url):
        # logging.info(f"\tFetching {url} with Playwright")
        for attempt in range(5):
            # logging.info(f"\tAttempt {attempt + 1} for {url}")
            try:
                context = await self.browser.new_context()
                page = await context.new_page()
                await page.goto(url, timeout=10000)
                content = await page.content()
                # logging.info(f"\t\tSuccessfully fetched {url} with Playwright, head:\n{content[:100]}...")
                await self.parse_and_enqueue(url, content)
                await context.close()
                return
            except (PlaywrightTimeoutError, Exception):
                await asyncio.sleep(2 ** attempt)
            finally:
                await context.close()
        print(f"Failed to fetch {url} with Playwright after retries")

    async def parse_and_enqueue(self, base_url, html):
        soup = BeautifulSoup(html, 'lxml')
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            href = urljoin(base_url, href)
            href, _ = urldefrag(href)  # Remove URL fragments
            parsed_href = urlparse(href)
            if parsed_href.netloc != urlparse(self.root_url).netloc:
                continue
            if href not in self.seen_urls:  # Check if URL is already seen
                self.seen_urls.add(href)    # Mark it as seen
                await self.urls_to_visit.put(href)
                await self.discovered_urls.put(href)
                # logging.debug(f"Enqueued new URL: {href}")

    async def get_batch(self):
        batch_start_time = time.time()  # Start time for getting the batch
        batch = []
        while len(batch) < self.batch_size:
            if self.discovered_urls.empty():
                await asyncio.sleep(1)  # Wait if there are no URLs to process
                continue
            url = await self.discovered_urls.get()
            batch.append(url)

        batch_end_time = time.time()  # End time after batch is completed
        batch_duration = batch_end_time - batch_start_time

        logging.info(f"Got batch of {len(batch)} URLs in {batch_duration:.2f} seconds.")

        # Update total_urls_batched and total_batches
        self.total_urls_batched += len(batch)
        self.total_batches += 1

        # Calculate the running mean of batch retrieval times
        if hasattr(self, 'mean_batching_time'):
            self.mean_batching_time = (self.mean_batching_time * (self.total_batches - 1) + batch_duration) / self.total_batches
        else:
            self.mean_batching_time = batch_duration  # Initialize if not previously set

        logging.info(f"Total URLs batched: {self.total_urls_batched} at mean batching time: {self.mean_batching_time:.2f} seconds for every {self.batch_size} URLs.")

        # Append the latest mean time to a historical list for plotting
        if not hasattr(self, 'historical_batches_mean_batching_time'):
            self.historical_batches_mean_batching_time = []

        self.historical_batches_mean_batching_time.append((self.total_urls_batched, self.mean_batching_time))

        return batch

    def plot_mean_batching_times(self):
        if not hasattr(self, 'historical_batches_mean_batching_time') or not self.historical_batches_mean_batching_time:
            return  # Do nothing if there's no data to plot

        # Extract data for plotting
        x, y = zip(*self.historical_batches_mean_batching_time)
        
        plt.figure(figsize=(10, 5))
        plt.plot(x, y, marker='o', linestyle='-', color='blue')
        plt.title('Mean Batching Time Progress')
        plt.xlabel('Total URLs Batched')
        plt.ylabel('Mean Batching Time (seconds)')
        plt.grid(True)
        path = os.path.join(self.root_folder, 'crawler_status')
        if not os.path.exists(path):
            os.makedirs(path)
        plt.savefig(os.path.join(path, 'mean_batching_time.png'))
        plt.close()

    def save_state(self):
        # save also visited_urls and urls_to_visit_list to file txt
        path = os.path.join(self.root_folder, 'crawler_status')
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path, 'visited_urls.txt'), 'w') as f:
            for url in self.visited_urls:
                f.write(url + '\n')
        with open(os.path.join(path, 'urls_to_visit_list.txt'), 'w') as f:
            for url in self.urls_to_visit._queue:
                f.write(url + '\n')

        # plot mean batching times
        self.plot_mean_batching_times()

    def load_state(self):
        # open the urls_to_visit.txt and _visited_urls.txt files
        path = os.path.join(self.root_folder, 'crawler_status')
        
        # load the urls_to_visit_variable
        with open(os.path.join(path, 'urls_to_visit_list.txt'), 'r') as f:
            urls_to_visit_list = [line.strip() for line in f.readlines()]
        self.urls_to_visit = asyncio.Queue()
        for url in urls_to_visit_list:
            self.urls_to_visit.put_nowait(url)

        # load the visited_urls_variable
        with open(os.path.join(path, 'visited_urls.txt'), 'r') as f:
            visited_urls = [line.strip() for line in f.readlines()]
        self.visited_urls = visited_urls

    async def periodic_state_save(self):
        while True:
            await asyncio.sleep(self.save_state_interval)
            self.save_state()

    def __del__(self):
        # Ensure resources are cleaned up
        if not self.session.closed:
            asyncio.create_task(self.session.close())
        if self.playwright:
            asyncio.create_task(self.playwright.stop())

# Example usage
async def main():

    crawler = NewCrawler(
        root_url='https://valkanik.com/',
        concurrency=10,
        batch_size=50,
        use_last_state=False,
        n_retries=5,
        timeout=20
    )
    await crawler.start()
    try:
        while True:
            batch = await crawler.get_batch()
            #print(f"Retrieved batch of {len(batch)} URLs")
            # Process batch here
    except KeyboardInterrupt:
        await crawler.stop()
    finally:
        await crawler.cleanup()

# Run the crawler
# asyncio.run(main())

if __name__ == '__main__':
    asyncio.run(main())
