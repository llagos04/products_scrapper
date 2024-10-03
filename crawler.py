import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

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

    async def get_next_batch_urls(self, batch_size):
        if self.is_javascript_driven:
            return await self.get_next_batch_urls_pyw(batch_size)
        else:
            return await self.get_next_batch_urls_bfs(batch_size)

    async def get_next_batch_urls_bfs(self, batch_size):
        batch_urls = []

        async with aiohttp.ClientSession() as session:
            while self.urls_to_visit and len(batch_urls) < batch_size:
                current_url = self.urls_to_visit.pop(0)
                normalized_url = urlparse(current_url)._replace(fragment='').geturl()

                if normalized_url not in self.visited:
                    self.visited.add(normalized_url)

                    # Skip non-HTML URLs
                    if not is_html_page(current_url):
                        logging.info(f"Skipping non-HTML URL: {current_url}")
                        continue

                    try:
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
                            else:
                                logging.error(f"Failed to load {current_url}, status code: {response.status}")
                    except Exception as e:
                        logging.exception(f"Error accessing {current_url}: {e}")

                    # After processing the current URL, add it to batch_urls
                    batch_urls.append(current_url)

        return batch_urls

    async def get_next_batch_urls_pyw(self, batch_size):
        batch_urls = []
        max_concurrent_pages = 5  # You can adjust this as needed
        semaphore = asyncio.Semaphore(max_concurrent_pages)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            async def process_url(current_url):
                normalized_url = urlparse(current_url)._replace(fragment='').geturl()

                if normalized_url not in self.visited:
                    self.visited.add(normalized_url)

                    # Skip non-HTML URLs
                    if not is_html_page(current_url):
                        logging.info(f"Skipping non-HTML URL: {current_url}")
                        return

                    try:
                        async with semaphore:
                            page = await context.new_page()

                            # Block unnecessary resources to speed up loading
                            async def block_unnecessary_resources(route, request):
                                if request.resource_type in ['document', 'xhr', 'fetch']:
                                    await route.continue_()
                                else:
                                    await route.abort()

                            await page.route("**/*", block_unnecessary_resources)

                            # Set a reduced timeout
                            await page.goto(current_url, timeout=10000)  # 10 seconds timeout

                            # Wait for the page to load necessary content
                            await page.wait_for_selector("a", timeout=5000)  # Wait max 5 seconds

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
                    except Exception as e:
                        logging.exception(f"Error accessing {current_url}: {e}")

                    # After processing the current URL, add it to batch_urls
                    batch_urls.append(current_url)

            # Process URLs concurrently
            tasks = []
            while self.urls_to_visit and len(batch_urls) < batch_size:
                current_url = self.urls_to_visit.pop(0)
                tasks.append(process_url(current_url))

                # If we reach max_concurrent_pages, wait for tasks to complete
                if len(tasks) >= max_concurrent_pages:
                    await asyncio.gather(*tasks)
                    tasks = []

            # Process any remaining tasks
            if tasks:
                await asyncio.gather(*tasks)

            await browser.close()

        return batch_urls
