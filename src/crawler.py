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

from xml.etree import ElementTree as ET

# Función para extraer URLs desde un sitemap
async def get_urls_from_sitemap(domain):
    """
    Intenta obtener URLs desde el sitemap del dominio.
    Primero busca el sitemap en /sitemap.xml o lo detecta desde el robots.txt.
    """
    possible_sitemap_urls = [
        urljoin(domain, '/sitemap.xml'),
        urljoin(domain, '/robots.txt')
    ]
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'YourCrawler/1.0'}) as session:
        for sitemap_url in possible_sitemap_urls:
            try:
                async with session.get(sitemap_url, timeout=10) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'xml' in content_type:
                            # Si el contenido es XML, intentamos parsearlo como sitemap directamente
                            sitemap_content = await response.text()
                            return parse_sitemap_xml(sitemap_content)
                        elif 'text/plain' in content_type and 'robots.txt' in sitemap_url:
                            # Si es un robots.txt, buscamos la línea con el sitemap
                            robots_content = await response.text()
                            sitemap_url = extract_sitemap_from_robots(robots_content)
                            if sitemap_url:
                                # Intentamos obtener las URLs desde el sitemap indicado en robots.txt
                                return await get_urls_from_sitemap(sitemap_url)
            except Exception as e:
                logging.warning(f"Error al obtener el sitemap desde {sitemap_url}: {e}")

    # Si no se encuentra un sitemap válido, retornamos una lista vacía
    return []

# Función para parsear el contenido XML del sitemap
def parse_sitemap_xml(sitemap_content):
    """
    Parsea el contenido XML del sitemap y extrae las URLs.
    """
    try:
        root = ET.fromstring(sitemap_content)
        urls = [url_elem.text for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        return urls
    except ET.ParseError as e:
        logging.error(f"Error al parsear el sitemap: {e}")
        return []

# Función para extraer el sitemap de un robots.txt
def extract_sitemap_from_robots(robots_content):
    """
    Busca en el robots.txt la línea que indica la ubicación del sitemap.
    """
    for line in robots_content.splitlines():
        if line.lower().startswith("sitemap:"):
            return line.split(":", 1)[1].strip()
    return None

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
        self.sitemap_checked = False  # Para evitar intentar obtener el sitemap más de una vez

    async def get_all_urls(self):
        """
        Obtiene todas las URLs del sitemap, si está disponible, o usa el crawling regular si no hay sitemap.
        Este método maneja sitemaps recursivos y devuelve todos los sitemaps y URLs.
        """
        all_sitemaps = []
        if not self.sitemap_checked:
            self.sitemap_checked = True  # Solo intentamos obtener el sitemap una vez
            logging.info(f"Checking for sitemap at {self.domain}...")

            # Obtener las URLs del sitemap
            sitemap_data = await self.get_urls_from_sitemap_recursive(self.domain + '/sitemap.xml')

            if sitemap_data:
                logging.info(f"Found {len(sitemap_data)} URLs after processing all sitemaps.")
                return sitemap_data
            else:
                logging.info("No URLs found in sitemap.")
                return []

        # Si no hay sitemap, seguimos con el crawling tradicional
        logging.info(f"No sitemap found, proceeding with crawling...")
        urls_from_crawling = await self.get_all_urls_by_crawling()

        logging.info(f"Found {len(urls_from_crawling)} URLs from crawling.")
        return [{'sitemap': 'Crawling', 'urls': urls_from_crawling}]

   
    async def get_urls_from_sitemap_recursive(self, sitemap_url):
        """
        Procesa un sitemap de forma recursiva para extraer URLs. Si un sitemap contiene otros sitemaps,
        sigue procesando hasta que encuentre URLs finales.
        """
        try:
            logging.info(f"Fetching sitemap: {sitemap_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(sitemap_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Parsear el contenido XML del sitemap
                        root = ET.fromstring(content)
                        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

                        all_sitemaps = []

                        # Si el sitemap contiene otros sitemaps, procesarlos recursivamente
                        for sitemap in root.findall('sitemap:sitemap', ns):
                            loc = sitemap.find('sitemap:loc', ns).text
                            logging.info(f"Found secondary sitemap: {loc}")
                            secondary_sitemaps = await self.get_urls_from_sitemap_recursive(loc)
                            all_sitemaps.extend(secondary_sitemaps)

                        # Si el sitemap contiene URLs finales, extraerlas
                        urls = []
                        for url in root.findall('sitemap:url/sitemap:loc', ns):
                            loc = url.text
                            urls.append(loc)

                        # Guardar el sitemap y sus URLs
                        if urls:
                            all_sitemaps.append({
                                'sitemap': sitemap_url,
                                'urls': urls
                            })

                        return all_sitemaps
                    else:
                        logging.error(f"Failed to fetch sitemap: {sitemap_url}, Status Code: {response.status}")
                        return []
        except Exception as e:
            logging.error(f"Error fetching sitemap {sitemap_url}: {e}")
            return []

        
    def is_html_page(self, url):
        """
        Verifica si una URL apunta a una página HTML basándose en la extensión del archivo.
        """
        non_html_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.mp3']
        return not any(url.lower().endswith(ext) for ext in non_html_extensions)

    async def get_all_urls_by_crawling(self):
        """
        Obtiene todas las URLs usando el método de crawling tradicional, recorriendo páginas.
        """
        all_urls = []
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async with aiohttp.ClientSession(headers={'User-Agent': 'YourCrawler/1.0'}) as session:
            tasks = []
            while self.urls_to_visit:
                current_url = self.urls_to_visit.pop(0)
                tasks.append(self.process_url(session, current_url, all_urls, semaphore))

                if len(tasks) >= self.concurrent_requests:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

        return all_urls  # Devolver todas las URLs obtenidas por crawling

    async def process_url(self, session, current_url, all_urls, semaphore):
        """
        Procesa una URL individual, obteniendo sus enlaces si es HTML y no ha sido visitada.
        """
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
                                # Añadir la URL actual procesada
                                all_urls.append(current_url)
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
