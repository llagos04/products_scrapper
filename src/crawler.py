import os
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from xml.etree import ElementTree as ET
from aiohttp import ClientSession

# Configuración (asegúrate de que estas variables estén definidas)
IGNORE_URLS_WITH = []
USE_RATE_LIMIT = False
REQUEST_TIMEOUT = 10  # Puedes ajustar el tiempo de espera según tus necesidades
MAX_SITEMAPS = 5  # Número máximo de sitemaps a procesar recursivamente
MAX_URLS = 200  # Máximo de URLs a procesar

async def fetch_links_with_playwright(url):
    """
    Usa Playwright para renderizar la página y extraer enlaces generados dinámicamente.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)
            links.append(full_url)

        await browser.close()
        return links

def is_same_domain(domain, url, include_subdomains=True):
    """
    Verifica si la URL pertenece al dominio principal o a un subdominio.
    """
    domain_netloc = urlparse(domain).netloc.lower()
    url_netloc = urlparse(url).netloc.lower()

    if include_subdomains:
        return url_netloc.endswith(domain_netloc)
    else:
        return domain_netloc == url_netloc

def normalize_url(url):
    """
    Normaliza una URL eliminando el fragmento y asegurándose de que tiene esquema.
    """
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'http://' + url  # O 'https://' dependiendo de tu caso
        parsed = urlparse(url)
    return parsed._replace(fragment='').geturl()

def is_html_page(url):
    """
    Acepta URLs incluso sin extensiones explícitas, excepto recursos no deseados conocidos.
    """
    non_html_extensions = (
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
        '.zip', '.rar', '.exe', '.dmg', '.apk', '.tar.gz', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.ico', '.css', '.js', '.json', '.xml',
    )
    path = urlparse(url).path.lower()
    return not any(path.endswith(ext) for ext in non_html_extensions)

class Crawler:
    def __init__(self, domain, is_javascript_driven=False, ignore_links=[]):
        self.domain = domain.rstrip('/')
        self.is_javascript_driven = is_javascript_driven
        self.visited = set()
        self.urls_to_visit = asyncio.Queue()
        self.visited_lock = asyncio.Lock()
        self.ignore_links = ignore_links
        self.use_rate_limit = USE_RATE_LIMIT
        self.rate_limit = 1  # Máximo de solicitudes por segundo
        self.concurrent_requests = 5  # Máximo de solicitudes concurrentes
        self.sitemap_checked = False  # Para evitar intentar obtener el sitemap más de una vez
        self.stop_crawling = False  # Bandera para detener el crawling
        # Headers comunes, incluyendo un User-Agent popular
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/85.0.4183.121 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        }

    async def get_all_urls(self):
        """
        Obtiene todas las URLs del sitemap, si está disponible, o usa el crawling regular si no hay sitemap.
        Este método maneja sitemaps recursivos y devuelve todos los sitemaps y URLs.
        """
        all_sitemaps = []
        if not self.sitemap_checked:
            self.sitemap_checked = True  # Solo intentamos obtener el sitemap una vez
            logging.info(f"Checking for sitemap in robots.txt at {self.domain}...")

            # Intentar obtener el sitemap desde robots.txt
            sitemap_url = await self.get_sitemap_from_robots_txt()

            if not sitemap_url:
                # Probar ubicaciones comunes para el sitemap
                common_sitemap_paths = [
                    f"{self.domain}/sitemap.xml",
                    f"{self.domain}/sitemap_index.xml",
                    f"{self.domain}/sitemap/sitemap.xml",
                    f"{self.domain}/sitemaps.xml",
                    f"{self.domain}/sitemapindex.xml"
                ]
                logging.info("No sitemap found in robots.txt. Checking common sitemap locations...")
                for path in common_sitemap_paths:
                    if await self.url_exists(path):
                        logging.info(f"Sitemap found at {path}")
                        sitemap_url = path
                        break

            if sitemap_url:
                # Obtener las URLs del sitemap usando el sitemap encontrado
                logging.info(f"Procesando sitemap encontrado: {sitemap_url}")
                sitemap_data = await self.get_urls_from_sitemap_recursive(sitemap_url)

                if sitemap_data:
                    logging.info(f"Found {len(sitemap_data)} URLs after processing all sitemaps.")
                    return sitemap_data
                else:
                    logging.info("No URLs found in sitemap.")
                    return []
            else:
                logging.info("No sitemap found in robots.txt or common locations.")
        
        # Si no hay sitemap, seguimos con el crawling tradicional
        logging.info(f"No sitemap found, proceeding with crawling...")
        urls_from_crawling = await self.get_all_urls_by_crawling()

        logging.info(f"Found {len(urls_from_crawling)} URLs from crawling.")
        return [{'sitemap': 'Crawling', 'urls': urls_from_crawling}]

    async def url_exists(self, url):
        """
        Verifica si una URL existe (respuesta 200).
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logging.error(f"Error checking URL {url}: {e}")
            return False

    async def get_all_urls_by_crawling(self):
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async def process_url(session):
            while True:
                url = await self.urls_to_visit.get()
                if url is None:
                    # Recibimos el sentinel, salimos del bucle
                    self.urls_to_visit.task_done()
                    break
                try:
                    async with semaphore:
                        normalized_url = normalize_url(url)

                        async with self.visited_lock:
                            if normalized_url in self.visited:
                                logging.debug(f"URL ya visitada: {normalized_url}")
                                continue
                            self.visited.add(normalized_url)

                        # Verificar si se alcanzó MAX_URLS
                        async with self.visited_lock:
                            if len(self.visited) >= MAX_URLS:
                                logging.info(f"Reached MAX_URLS limit of {MAX_URLS}, stopping crawling.")
                                self.stop_crawling = True
                                # Añadimos sentinels para desbloquear las tareas
                                for _ in range(self.concurrent_requests):
                                    await self.urls_to_visit.put(None)
                                break

                        logging.info(f"Procesando URL: {normalized_url}")
                        try:
                            async with session.get(normalized_url, headers=self.headers, timeout=REQUEST_TIMEOUT) as response:
                                logging.info(f"Estado {response.status} recibido para: {normalized_url}")

                                if response.status == 200:
                                    content = await response.text()
                                    soup = BeautifulSoup(content, "html.parser")

                                    # Extraer enlaces del HTML
                                    links_found = 0
                                    for link in soup.find_all("a", href=True):
                                        href = link["href"]
                                        full_url = urljoin(normalized_url, href)
                                        full_url = normalize_url(full_url)

                                        if is_same_domain(self.domain, full_url):
                                            async with self.visited_lock:
                                                if full_url not in self.visited and full_url not in self.ignore_links:
                                                    if not self.stop_crawling:
                                                        await self.urls_to_visit.put(full_url)
                                                        links_found += 1
                                                        # Verificar si se alcanzó MAX_URLS
                                                        if len(self.visited) + self.urls_to_visit.qsize() >= MAX_URLS:
                                                            logging.info(f"Reached MAX_URLS limit of {MAX_URLS}, stopping addition of new URLs.")
                                                            self.stop_crawling = True
                                                            # Añadimos sentinels para desbloquear las tareas
                                                            for _ in range(self.concurrent_requests):
                                                                await self.urls_to_visit.put(None)
                                                            break
                                        else:
                                            logging.debug(f"Skipping URL from different domain: {full_url}")

                                    logging.info(f"{links_found} enlaces encontrados en {normalized_url}")

                                    # Extraer enlaces JavaScript si es necesario
                                    if self.is_javascript_driven and not self.stop_crawling:
                                        js_links = await fetch_links_with_playwright(normalized_url)
                                        for js_link in js_links:
                                            full_js_link = urljoin(normalized_url, js_link)
                                            full_js_link = normalize_url(full_js_link)

                                            if is_same_domain(self.domain, full_js_link):
                                                async with self.visited_lock:
                                                    if full_js_link not in self.visited and full_js_link not in self.ignore_links:
                                                        await self.urls_to_visit.put(full_js_link)
                                                        # Verificar si se alcanzó MAX_URLS
                                                        if len(self.visited) + self.urls_to_visit.qsize() >= MAX_URLS:
                                                            logging.info(f"Reached MAX_URLS limit of {MAX_URLS}, stopping addition of new URLs.")
                                                            self.stop_crawling = True
                                                            # Añadimos sentinels para desbloquear las tareas
                                                            for _ in range(self.concurrent_requests):
                                                                await self.urls_to_visit.put(None)
                                                            break
                                            else:
                                                logging.debug(f"Skipping JS URL from different domain: {full_js_link}")

                        except Exception as e:
                            logging.error(f"Error procesando {normalized_url}: {e}")
                finally:
                    self.urls_to_visit.task_done()

        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Sembrar la cola con la URL inicial
            await self.urls_to_visit.put(self.domain)

            tasks = [asyncio.create_task(process_url(session)) for _ in range(self.concurrent_requests)]

            await self.urls_to_visit.join()

            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logging.info(f"Crawling completado. Total de URLs encontradas: {len(self.visited)}")
        return list(self.visited)

    def extract_sitemap_from_robots(self, robots_content):
        """
        Extrae la URL del sitemap desde el contenido de un archivo robots.txt.
        """
        for line in robots_content.splitlines():
            if line.lower().startswith("sitemap:"):
                return line.split(":", 1)[1].strip()
        return None

    async def get_sitemap_from_robots_txt(self):
        """
        Busca el archivo robots.txt en el dominio y extrae la URL del sitemap.
        """
        robots_url = f"{self.domain}/robots.txt"
        try:
            async with ClientSession(headers=self.headers) as session:
                async with session.get(robots_url, timeout=10) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        sitemap_url = self.extract_sitemap_from_robots(robots_content)
                        if sitemap_url:
                            logging.info(f"Sitemap encontrado en robots.txt: {sitemap_url}")
                            return sitemap_url
                        else:
                            logging.info("No se encontró ninguna directiva Sitemap en robots.txt.")
                            return None
                    elif response.status == 403:
                        logging.warning("Acceso prohibido a robots.txt (403). Intentando sin robots.txt.")
                        return None
                    else:
                        logging.warning(f"No se pudo obtener robots.txt, estado HTTP: {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Error al obtener robots.txt: {e}")
            return None

    async def get_urls_from_sitemap_recursive(self, sitemap_url, depth=0):
        """
        Procesa un sitemap de forma recursiva para extraer URLs. Si un sitemap contiene otros sitemaps,
        sigue procesando hasta que encuentre URLs finales.
        """
        if depth > MAX_SITEMAPS:
            logging.warning(f"Max sitemap recursion depth ({MAX_SITEMAPS}) reached.")
            return []

        try:
            logging.info(f"Fetching sitemap: {sitemap_url}")
            async with ClientSession(headers=self.headers) as session:
                async with session.get(sitemap_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                        all_sitemaps = []

                        # Manejo recursivo de sitemaps
                        for sitemap in root.findall('sitemap:sitemap', ns):
                            loc = sitemap.find('sitemap:loc', ns).text
                            logging.info(f"Found secondary sitemap: {loc}")
                            secondary_sitemaps = await self.get_urls_from_sitemap_recursive(loc, depth + 1)
                            all_sitemaps.extend(secondary_sitemaps)

                        # Manejo de URLs finales
                        urls = [url.text for url in root.findall('sitemap:url/sitemap:loc', ns)]
                        if urls:
                            all_sitemaps.append({'sitemap': sitemap_url, 'urls': urls})
                        return all_sitemaps
                    elif response.status == 403:
                        logging.warning(f"Access to {sitemap_url} is forbidden (403).")
                    else:
                        logging.error(f"Failed to fetch sitemap: {sitemap_url}, Status Code: {response.status}")
                    return []
        except Exception as e:
            logging.error(f"Error fetching sitemap {sitemap_url}: {e}")
            return []

