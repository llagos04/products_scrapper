import asyncio
import logging
import aiohttp
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
import logging
from urllib.parse import urlparse, urljoin
from CONFIG import IGNORE_URLS_WITH, USE_RATE_LIMIT, REQUEST_TIMEOUT

def is_same_domain(domain, url):
    return urlparse(domain).netloc == urlparse(url).netloc

async def is_javascript_driven_async(domain):
    # Implement your logic to determine if a site is JavaScript-driven
    # For this example, we'll assume it's not JavaScript-driven
    return False

def is_html_page(url):
    """
    Check if a URL is likely to point to an HTML page based on its file extension.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    # List of extensions that are typically non-HTML resources
    non_html_extensions = (
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
        '.zip', '.rar', '.exe', '.dmg', '.apk', '.tar.gz', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
        '.rtf', '.csv', '.ico', '.css', '.js', '.json', '.xml',
    )
    if any(path.endswith(ext) for ext in non_html_extensions):
        return False
    return True

class Crawler:
    def __init__(self, domain, is_javascript_driven=False, ignore_links=[]):
        self.domain = domain
        self.is_javascript_driven = is_javascript_driven
        self.visited = set()
        self.urls_to_visit = [domain]
        self.ignore_links = ignore_links
        self.use_rate_limit = USE_RATE_LIMIT
        self.rate_limit = 1  # Max requests per second
        self.concurrent_requests = 5  # Max concurrent requests
        self.lock = asyncio.Lock()

    async def get_next_batch_urls(self, batch_size):
        if self.is_javascript_driven:
            return await self.get_next_batch_urls_pyw(batch_size)
        else:
            return await self.get_next_batch_urls_bfs(batch_size)

    async def get_next_batch_urls_bfs(self, batch_size):
        batch_urls = []
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async with aiohttp.ClientSession(headers={'User-Agent': 'YourCrawler/1.0'}) as session:
            tasks = []
            while self.urls_to_visit and len(batch_urls) < batch_size:
                current_url = self.urls_to_visit.pop(0)
                tasks.append(self.process_url(session, current_url, batch_urls, semaphore))

                if len(tasks) >= self.concurrent_requests:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

        return batch_urls

    async def process_url(self, session, current_url, batch_urls, semaphore):
        async with semaphore:
            parsed_url = urlparse(current_url)
            normalized_url = parsed_url._replace(fragment='').geturl()

            # Ignore URLs with specific query parameters
            if IGNORE_URLS_WITH in parsed_url.query:
                return

            if normalized_url not in self.visited:
                self.visited.add(normalized_url)

                # Skip non-HTML URLs
                if not is_html_page(current_url):
                    logging.info(f"Skipping non-HTML URL: {current_url}")
                    return

                retry_count = 0
                max_retries = 5
                backoff_factor = 1

                while retry_count <= max_retries:
                    try:
                        # Rate limiting: wait if necessary
                        if self.use_rate_limit:
                            async with self.lock:
                                await asyncio.sleep(random.uniform(1 / self.rate_limit, 2 / self.rate_limit))

                        async with session.get(current_url, timeout=10) as response:
                            if response.status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                                content = await response.text()
                                soup = BeautifulSoup(content, 'html.parser')
                                # Extract and enqueue new URLs
                                for link in soup.find_all('a', href=True):
                                    href = link['href']
                                    full_url = urljoin(self.domain, href)
                                    full_url = urlparse(full_url)._replace(fragment='').geturl()
                                    if is_same_domain(self.domain, full_url) and full_url not in self.visited and full_url not in self.ignore_links:
                                        self.urls_to_visit.append(full_url)
                                # After processing the current URL, add it to batch_urls
                                batch_urls.append(current_url)
                                break  # Exit retry loop on success
                            elif response.status == 429:
                                if self.use_rate_limit:
                                    retry_after = response.headers.get('Retry-After')
                                    if retry_after:
                                        wait_time = int(retry_after)
                                    else:
                                        wait_time = backoff_factor * (2 ** retry_count)
                                    logging.warning(f"Received 429 for {current_url}, retrying after {wait_time} seconds")
                                    await asyncio.sleep(wait_time)
                                    retry_count += 1
                                else:
                                    logging.error(f"Received 429 for {current_url}, but rate limiting is disabled.")
                                    break  # Do not retry if rate limiting is disabled
                            else:
                                logging.error(f"Failed to load {current_url}, status code: {response.status}")
                                break  # Don't retry other status codes
                    except Exception as e:
                        logging.exception(f"Error accessing {current_url}: {e}")
                        if self.use_rate_limit:
                            retry_count += 1
                            wait_time = backoff_factor * (2 ** retry_count)
                            await asyncio.sleep(wait_time)
                        else:
                            break  # Do not retry if rate limiting is disabled
                else:
                    if self.use_rate_limit:
                        logging.error(f"Exceeded max retries for {current_url}")

    async def get_next_batch_urls_pyw(self, batch_size):
        batch_urls = []
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        backoff_factor = 1
        max_retries = 5

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent='YourCrawler/1.0')

            async def process_url(current_url):
                async with semaphore:
                    normalized_url = urlparse(current_url)._replace(fragment='').geturl()

                    if normalized_url not in self.visited:
                        self.visited.add(normalized_url)

                        # Skip non-HTML URLs
                        if not is_html_page(current_url):
                            logging.info(f"Skipping non-HTML URL: {current_url}")
                            return

                        retry_count = 0

                        while retry_count <= max_retries:
                            try:
                                # Rate limiting
                                if self.use_rate_limit:
                                    async with self.lock:
                                        await asyncio.sleep(random.uniform(1 / self.rate_limit, 2 / self.rate_limit))

                                page = await context.new_page()

                                # # Block unnecessary resources to speed up loading
                                # async def block_unnecessary_resources(route, request):
                                #     if request.resource_type in ['image', 'media', 'font']:
                                #         await route.continue_()
                                #     else:
                                #         await route.abort()

                                # await page.route("**/*", block_unnecessary_resources)

                                # Set a reduced timeout
                                response = await page.goto(current_url, timeout=10000)  # 10 seconds timeout

                                # Check for 429 status code
                                if response.status == 429:
                                    if self.use_rate_limit:
                                        retry_after = response.headers.get('Retry-After')
                                        if retry_after:
                                            wait_time = int(retry_after)
                                        else:
                                            wait_time = backoff_factor * (2 ** retry_count)
                                        logging.warning(f"Received 429 for {current_url}, retrying after {wait_time} seconds")
                                        await page.close()
                                        await asyncio.sleep(wait_time)
                                        retry_count += 1
                                        continue
                                    else:
                                        logging.error(f"Received 429 for {current_url}, but rate limiting is disabled.")
                                        await page.close()
                                        break  # Do not retry if rate limiting is disabled
                                elif response.status != 200:
                                    logging.error(f"Failed to load {current_url}, status code: {response.status}")
                                    await page.close()
                                    break  # Don't retry other status codes

                                # Wait for the page to load necessary content
                                await page.wait_for_selector("a", state='attached', timeout=REQUEST_TIMEOUT*1000)

                                # Extract all links from the page
                                links = await page.query_selector_all("a")
                                for link in links:
                                    href = await link.get_attribute("href")
                                    if href:
                                        full_url = urljoin(self.domain, href)
                                        full_url = urlparse(full_url)._replace(fragment='').geturl()
                                        if is_same_domain(self.domain, full_url) and full_url not in self.visited and full_url not in self.ignore_links:
                                            self.urls_to_visit.append(full_url)
                                await page.close()
                                # After processing the current URL, add it to batch_urls
                                batch_urls.append(current_url)
                                break  # Exit retry loop on success
                            except Exception as e:
                                logging.exception(f"Error accessing {current_url}: {e}")
                                if self.use_rate_limit:
                                    retry_count += 1
                                    wait_time = backoff_factor * (2 ** retry_count)
                                    await asyncio.sleep(wait_time)
                                else:
                                    break  # Do not retry if rate limiting is disabled
                        else:
                            if self.use_rate_limit:
                                logging.error(f"Exceeded max retries for {current_url}")

            # Process URLs concurrently
            tasks = []
            while self.urls_to_visit and len(batch_urls) < batch_size:
                current_url = self.urls_to_visit.pop(0)
                tasks.append(process_url(current_url))

                if len(tasks) >= self.concurrent_requests:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

            await browser.close()

        return batch_urls
