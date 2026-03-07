import os
import asyncio
import logging
import aiohttp
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from xml.etree import ElementTree as ET
from lxml import etree as lxml_etree
from aiohttp import ClientSession
from CONFIG import USE_PROXIES, AUTO_FETCH_PROXIES
from src.fetcher import rate_limiter, get_random_headers


class ProxyManager:
    """
    Gestor de proxies rotativos para evitar bloqueos por IP
    """
    def __init__(self):
        # Lista inicial de proxies (se puede actualizar dinámicamente)
        self.proxies = self._load_initial_proxies()
        self.current_proxy_index = 0
        self.failed_proxies = set()
        self.proxy_stats = {}
        self.use_proxies = USE_PROXIES  # Configuración global para activar/desactivar proxies

    def _load_initial_proxies(self):
        """
        Carga la lista inicial de proxies. En producción, esto debería conectarse
        a un servicio de proxies o leer de un archivo/database.
        """
        # Lista de ejemplo - reemplazar con proxies reales o servicio de proxies
        return [
            # Proxies de ejemplo - reemplazar con proxies reales
            # Formato: 'protocol://ip:port' o 'protocol://user:pass@ip:port'

            # Proxies HTTP gratuitos (ejemplos - cambiar por reales)
            'http://185.82.99.181:9091',
            'http://45.77.56.51:3128',
            'http://167.99.182.197:3128',
            'http://198.199.120.102:3128',
            'http://159.65.171.69:80',

            # Proxies HTTPS (ejemplos)
            'https://52.157.128.119:3128',
            'https://20.206.106.192:3128',
            'https://172.67.181.231:3128',

            # Más proxies para mayor rotación
            'http://47.254.47.51:8080',
            'http://8.219.97.248:80',
            'http://154.236.168.179:1981',
            'http://102.68.128.50:1981',
            'http://41.216.230.154:1981',
        ]

    def update_proxy_list(self, new_proxies):
        """
        Actualiza la lista de proxies dinámicamente
        """
        self.proxies = new_proxies
        self.failed_proxies.clear()  # Limpiar lista negra al actualizar
        self.current_proxy_index = 0
        logging.info(f"Proxy list updated with {len(new_proxies)} proxies")

    def add_proxy(self, proxy):
        """
        Agrega un proxy individual a la lista
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logging.info(f"Added proxy: {proxy}")

    def remove_proxy(self, proxy):
        """
        Remueve un proxy de la lista
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            if proxy in self.failed_proxies:
                self.failed_proxies.remove(proxy)
            logging.info(f"Removed proxy: {proxy}")

    def enable_proxies(self):
        """Activa el uso de proxies"""
        self.use_proxies = True
        logging.info("Proxy usage enabled")

    def disable_proxies(self):
        """Desactiva el uso de proxies"""
        self.use_proxies = False
        logging.info("Proxy usage disabled")

    async def fetch_free_proxies(self, limit=20):
        """
        Obtiene proxies gratuitos de fuentes públicas
        """
        proxy_sources = [
            'https://free-proxy-list.net/',
            'https://www.us-proxy.org/',
            'https://free-proxy-list.com/',
        ]

        found_proxies = []

        try:
            import aiohttp

            for source_url in proxy_sources:
                try:
                    headers = get_random_headers()
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(source_url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                # Extraer IPs y puertos usando regex simple
                                import re
                                ip_port_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})'
                                matches = re.findall(ip_port_pattern, content)

                                for ip, port in matches[:limit//len(proxy_sources)]:
                                    proxy = f'http://{ip}:{port}'
                                    if proxy not in found_proxies:
                                        found_proxies.append(proxy)

                except Exception as e:
                    logging.warning(f"Error fetching proxies from {source_url}: {e}")
                    continue

        except ImportError:
            logging.warning("aiohttp not available for fetching proxies")

        if found_proxies:
            self.update_proxy_list(found_proxies)
            logging.info(f"Fetched {len(found_proxies)} free proxies")
            return found_proxies
        else:
            logging.warning("No proxies found from free sources")
            return []

    def get_next_proxy(self):
        """
        Obtiene el siguiente proxy disponible rotando cíclicamente
        """
        if not self.proxies:
            logging.warning("No hay proxies disponibles, usando conexión directa")
            return None

        # Filtrar proxies que no hayan fallado recientemente
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]

        if not available_proxies:
            logging.warning("Todos los proxies han fallado, reiniciando lista de proxies fallidos")
            self.failed_proxies.clear()
            available_proxies = self.proxies

        # Rotar al siguiente proxy
        proxy = available_proxies[self.current_proxy_index % len(available_proxies)]
        self.current_proxy_index += 1

        # Actualizar estadísticas
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {'success': 0, 'fail': 0, 'last_used': None}
        self.proxy_stats[proxy]['last_used'] = time.time()

        logging.debug(f"Usando proxy: {proxy}")
        return proxy

    def mark_proxy_success(self, proxy):
        """Marca un proxy como exitoso"""
        if proxy and proxy in self.proxy_stats:
            self.proxy_stats[proxy]['success'] += 1
            # Si un proxy que falló anteriormente funciona, lo removemos de la lista negra
            if proxy in self.failed_proxies:
                self.failed_proxies.remove(proxy)
                logging.info(f"Proxy {proxy} recuperado y removido de lista negra")

    def mark_proxy_failed(self, proxy):
        """Marca un proxy como fallido"""
        if proxy and proxy in self.proxy_stats:
            self.proxy_stats[proxy]['fail'] += 1
            self.failed_proxies.add(proxy)
            logging.warning(f"Proxy {proxy} marcado como fallido")

    def get_proxy_stats(self):
        """Obtiene estadísticas de uso de proxies"""
        return self.proxy_stats

    def should_use_proxy(self):
        """
        Decide si usar proxy basado en configuración y disponibilidad
        """
        return self.use_proxies and bool(self.proxies and len(self.proxies) > 0)


# Instancia global del gestor de proxies
proxy_manager = ProxyManager()

# Configuración (asegúrate de que estas variables estén definidas)
IGNORE_URLS_WITH = []
USE_RATE_LIMIT = False
REQUEST_TIMEOUT = 10  # Puedes ajustar el tiempo de espera según tus necesidades
MAX_SITEMAPS = 5  # Número máximo de sitemaps a procesar recursivamente
MAX_URLS = 200  # Máximo de URLs a procesar


def get_random_headers():
    """
    Genera headers aleatorios para evitar bloqueos por rate limiting con amplia variedad de user-agents
    """
    user_agents = [
        # Chrome Desktop - Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Chrome Desktop - macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",

        # Chrome Desktop - Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",

        # Firefox Desktop
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",

        # Safari Desktop
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",

        # Edge Desktop
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47",

        # Chrome Mobile - Android
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",

        # Safari Mobile - iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",

        # Samsung Internet
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/18.0 Chrome/99.0.4844.88 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/17.0 Chrome/96.0.4664.104 Mobile Safari/537.36",

        # Opera Desktop
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0",

        # Vivaldi
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Vivaldi/6.5",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Vivaldi/6.4",

        # Brave
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Brave/119",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Brave/118",
    ]

    accept_languages = [
        "es-ES,es;q=0.9,en;q=0.8",
        "es-ES,es;q=0.9",
        "es,en;q=0.9,en-US;q=0.8",
        "es-ES,es;q=0.9,*;q=0.5",
        "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "es-MX,es;q=0.9,en;q=0.8",
        "es-AR,es;q=0.9,en;q=0.8",
        "es-CO,es;q=0.9,en;q=0.8",
        "es-CL,es;q=0.9,en;q=0.8",
        "es-PE,es;q=0.9,en;q=0.8"
    ]

    # Headers adicionales aleatorios para mayor variabilidad
    additional_headers = {}
    if random.choice([True, False]):
        additional_headers['Cache-Control'] = random.choice(['no-cache', 'max-age=0'])
    if random.choice([True, False]):
        additional_headers['Pragma'] = 'no-cache'
    if random.choice([True, False]):
        additional_headers['Sec-Fetch-Dest'] = random.choice(['document', 'empty'])
    if random.choice([True, False]):
        additional_headers['Sec-Fetch-Mode'] = random.choice(['navigate', 'cors'])
    if random.choice([True, False]):
        additional_headers['Sec-Fetch-Site'] = random.choice(['none', 'cross-site'])

    base_headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': random.choice(accept_languages),
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': random.choice([
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            'https://search.yahoo.com/',
            '',
        ]),
        'DNT': '1',
    }

    # Combinar headers base con adicionales
    base_headers.update(additional_headers)
    return base_headers


def create_session_with_random_headers():
    """
    Crea una sesión aiohttp con headers rotativos
    """
    return aiohttp.ClientSession(headers=get_random_headers())



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
        # self.headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
        #                   ' Chrome/85.0.4183.121 Safari/537.36',
        #     'Accept-Language': 'es-ES,es;q=0.9',
        #     'Accept-Encoding': 'gzip, deflate, br'
        # }
        # self.headers = {
        #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
        #     'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Connection': 'keep-alive',
        #     'Upgrade-Insecure-Requests': '1',
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        #     'Referer': 'https://www.google.com/',
        #     'DNT': '1',  # Do Not Track header
        # }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/",
            "DNT": "1",
        }



    async def get_all_urls(self, custom_sitemap_url=None):
        """
        Obtiene todas las URLs del sitemap, si está disponible.
        Si no se encuentra sitemap, se detiene el proceso.
        """
        if not self.sitemap_checked:
            self.sitemap_checked = True  # Solo intentamos obtener el sitemap una vez

            sitemap_data = []

            if custom_sitemap_url:
                logging.info(f"Using provided sitemap URL: {custom_sitemap_url}")
                sitemap_data = await self.get_urls_from_sitemap_recursive(custom_sitemap_url)
                if sitemap_data:
                    logging.info(f"Procesando sitemap proporcionado manualmente.")
                    return sitemap_data
                logging.warning(f"Provided sitemap ({custom_sitemap_url}) yielded no URLs. Falling back to automatic search.")

            logging.info(f"Checking for sitemap in robots.txt at {self.domain}...")

            # Intentar obtener el sitemap desde robots.txt
            sitemap_url_from_robots = await self.get_sitemap_from_robots_txt()

            if sitemap_url_from_robots:
                # Obtener las URLs del sitemap usando el sitemap encontrado
                logging.info(f"Procesando sitemap encontrado: {sitemap_url_from_robots}")
                sitemap_data = await self.get_urls_from_sitemap_recursive(sitemap_url_from_robots)

            # Si robots.txt no dio resultado o su sitemap falló/estaba vacío, probar common locations
            if not sitemap_data:
                if sitemap_url_from_robots:
                    logging.warning(f"Sitemap from robots.txt ({sitemap_url_from_robots}) yielded no URLs. Checking common locations...")
                else:
                    logging.info("No sitemap found in robots.txt. Checking common sitemap locations...")

                common_sitemap_paths = [
    # --- WordPress Standard (WP 5.5+) ---
    f"{self.domain}/wp-sitemap.xml",
    f"{self.domain}/wp-sitemap-index.xml",

    # --- PrestaShop estándar y multilenguaje ---
    f"{self.domain}/1_index_sitemap.xml",
    f"{self.domain}/1_es_0_sitemap.xml",
    f"{self.domain}/1_en_0_sitemap.xml",
    f"{self.domain}/1_fr_0_sitemap.xml",
    f"{self.domain}/1_pt_0_sitemap.xml",
    f"{self.domain}/1_it_0_sitemap.xml",
    f"{self.domain}/1_de_0_sitemap.xml",

    # Variantes para multitienda PrestaShop
    f"{self.domain}/2_index_sitemap.xml",
    f"{self.domain}/2_es_0_sitemap.xml",
    f"{self.domain}/3_index_sitemap.xml",

    # Variantes comunes PrestaShop (muchos módulos SEO las generan)
    f"{self.domain}/sitemap_shop_1.xml",
    f"{self.domain}/sitemap_shop_2.xml",
    f"{self.domain}/sitemap_products.xml",
    f"{self.domain}/sitemap_categories.xml",
    f"{self.domain}/sitemap_cms.xml",
    f"{self.domain}/sitemap_images.xml",
    f"{self.domain}/sitemap_index.xml",
    f"{self.domain}/sitemap-main.xml",

    # --- Variaciones de nombre y ubicación ---
    f"{self.domain}/index_sitemap.xml",
    f"{self.domain}/sitemap.xml",
    f"{self.domain}/sitemap_index.xml",
    f"{self.domain}/sitemap/sitemap.xml",
    f"{self.domain}/sitemap/sitemap_index.xml",
    f"{self.domain}/sitemaps.xml",
    f"{self.domain}/sitemapindex.xml",

    # --- Sitemaps numerados ---
    f"{self.domain}/sitemap-1.xml",
    f"{self.domain}/sitemap-2.xml",
    f"{self.domain}/sitemap-3.xml",
    f"{self.domain}/sitemap-4.xml",
    f"{self.domain}/sitemap_1.xml",
    f"{self.domain}/sitemap_2.xml",
    f"{self.domain}/sitemap_3.xml",

    # --- Variantes con guiones y underscores ---
    f"{self.domain}/sitemap-product.xml",
    f"{self.domain}/sitemap-category.xml",
    f"{self.domain}/sitemap-image.xml",
    f"{self.domain}/sitemap-categories.xml",

    # --- Sitemaps generados por módulos SEO populares ---
    f"{self.domain}/gsitemap.xml",                   # Google Sitemap módulo antiguo
    f"{self.domain}/modules/gsitemap/gsitemap.xml", # Ruta clásica PrestaShop
    f"{self.domain}/modules/gsitemap/sitemap.xml",
    f"{self.domain}/modules/sitemappro/sitemap.xml",
    f"{self.domain}/modules/sitemaps/sitemap.xml",
    f"{self.domain}/modules/smartseo/sitemap.xml",
    f"{self.domain}/modules/seositemap/sitemap.xml",

    # --- Rutas habituales en servidores ---
    f"{self.domain}/seo/sitemap.xml",
    f"{self.domain}/xml/sitemap.xml",
    f"{self.domain}/public/sitemap.xml",

    # --- Idiomas adicionales ---
    f"{self.domain}/1_pl_0_sitemap.xml",
    f"{self.domain}/1_nl_0_sitemap.xml",
    f"{self.domain}/1_ru_0_sitemap.xml",
    f"{self.domain}/1_ro_0_sitemap.xml",

                ]
                # Iterar en lotes para comprobar concurrentemente las rutas, manteniendo el orden de prioridad
                batch_size = 10
                for i in range(0, len(common_sitemap_paths), batch_size):
                    batch = [p for p in common_sitemap_paths[i:i+batch_size] if p != sitemap_url_from_robots]
                    if not batch:
                        continue
                        
                    # Comprobar concurrencia de este lote con asyncio.gather
                    results = await asyncio.gather(*(self.url_exists(p) for p in batch))
                    
                    found_valid_sitemap = False
                    for path, exists in zip(batch, results):
                        if exists:
                            logging.info(f"Sitemap found at {path}")
                            sitemap_data = await self.get_urls_from_sitemap_recursive(path)
                            if sitemap_data:
                                found_valid_sitemap = True
                                break # Found a valid sitemap
                                
                    if found_valid_sitemap:
                        break
            
            if sitemap_data:
                logging.info(f"Found {len(sitemap_data)} URLs after processing all sitemaps.")
                return sitemap_data
            else:
                logging.warning("No sitemap found in robots.txt or common locations (or they were empty).")
                return []
        
        return []

    async def url_exists(self, url):
        """
        Verifica si una URL existe (respuesta 200).
        """
        from CONFIG import MAX_RATE_LIMIT_RETRIES, RATE_LIMIT_BACKOFF_MULTIPLIER
        max_retries = MAX_RATE_LIMIT_RETRIES

        for attempt in range(1, max_retries + 1):
            # Aplicar rate limiting antes de cualquier petición
            await rate_limiter.wait_if_needed()

            proxy = None
            if proxy_manager.should_use_proxy():
                proxy = proxy_manager.get_next_proxy()

            try:
                headers = get_random_headers() if attempt == 1 else get_random_headers()

                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.head(url, timeout=10, proxy=proxy) as response:
                        if response.status == 200:
                            proxy_manager.mark_proxy_success(proxy)
                            from src.fetcher import consecutive_429_errors
                            consecutive_429_errors = 0  # Resetear contador en petición exitosa
                            return True
                        elif response.status == 429:
                            from CONFIG import MAX_RATE_LIMIT_RETRIES, RATE_LIMIT_BACKOFF_MULTIPLIER
                            from src.fetcher import consecutive_429_errors, proxy_manager as fetcher_proxy_manager

                            consecutive_429_errors += 1
                            logging.warning(f"Rate limit exceeded (429) checking URL {url}. Attempt {attempt} of {MAX_RATE_LIMIT_RETRIES}. Consecutive 429 errors: {consecutive_429_errors}")

                            # Activar proxies automáticamente si hay muchos errores 429
                            fetcher_proxy_manager.auto_enable_proxies_on_rate_limit(consecutive_429_errors)

                            if attempt < MAX_RATE_LIMIT_RETRIES:
                                # Generar nuevos headers aleatorios
                                new_headers = get_random_headers()
                                logging.info(f"New headers for retry: User-Agent: {new_headers['User-Agent']}")
                                # Esperar con backoff exponencial mejorado para rate limit
                                delay = (RATE_LIMIT_BACKOFF_MULTIPLIER ** attempt) + random.uniform(2, 5)
                                logging.info(f"Rate limit detected. Retrying URL check with new headers in {delay:.2f} seconds...")
                                await asyncio.sleep(delay)
                                # Aplicar rate limiting adicional antes del retry
                                await rate_limiter.wait_if_needed()
                                continue
                            else:
                                logging.error(f"Failed to check URL {url} after {MAX_RATE_LIMIT_RETRIES} attempts due to 429 Rate Limit.")
                                return False
                        else:
                            proxy_manager.mark_proxy_failed(proxy)
                            return False
            except aiohttp.ClientHttpProxyError as e:
                proxy_manager.mark_proxy_failed(proxy)
                logging.error(f"Proxy error checking URL {url} (proxy: {proxy}): {e}")
                return False
            except Exception as e:
                proxy_manager.mark_proxy_failed(proxy)
                logging.error(f"Error checking URL {url} (proxy: {proxy}): {e}")
                return False

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
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            # Aplicar rate limiting antes de cualquier petición
            await rate_limiter.wait_if_needed()

            proxy = None
            if proxy_manager.should_use_proxy():
                proxy = proxy_manager.get_next_proxy()

            try:
                # Usar headers aleatorios para el primer intento, y rotar en reintentos por 429
                headers = get_random_headers() if attempt == 1 else get_random_headers()

                async with ClientSession(headers=headers) as session:
                    async with session.get(robots_url, timeout=10, proxy=proxy) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            sitemap_url = self.extract_sitemap_from_robots(robots_content)
                            # Marcar proxy como exitoso
                            proxy_manager.mark_proxy_success(proxy)
                            from src.fetcher import consecutive_429_errors
                            consecutive_429_errors = 0  # Resetear contador en petición exitosa
                            if sitemap_url:
                                logging.info(f"Sitemap encontrado en robots.txt: {sitemap_url}")
                                return sitemap_url
                            else:
                                logging.info("No se encontró ninguna directiva Sitemap en robots.txt.")
                                return None
                        elif response.status == 403:
                            logging.warning("Acceso prohibido a robots.txt (403). Intentando sin robots.txt.")
                            return None
                        elif response.status == 429:
                            from CONFIG import MAX_RATE_LIMIT_RETRIES, RATE_LIMIT_BACKOFF_MULTIPLIER
                            from src.fetcher import consecutive_429_errors, proxy_manager as fetcher_proxy_manager

                            consecutive_429_errors += 1
                            logging.warning(f"Rate limit exceeded (429) for robots.txt. Attempt {attempt} of {MAX_RATE_LIMIT_RETRIES}. Consecutive 429 errors: {consecutive_429_errors}")

                            # Activar proxies automáticamente si hay muchos errores 429
                            fetcher_proxy_manager.auto_enable_proxies_on_rate_limit(consecutive_429_errors)

                            if attempt < MAX_RATE_LIMIT_RETRIES:
                                # Generar nuevos headers aleatorios
                                new_headers = get_random_headers()
                                logging.info(f"New headers for retry: User-Agent: {new_headers['User-Agent']}")
                                # Esperar con backoff exponencial mejorado para rate limit
                                delay = (RATE_LIMIT_BACKOFF_MULTIPLIER ** attempt) + random.uniform(2, 5)
                                logging.info(f"Rate limit detected. Retrying robots.txt with new headers in {delay:.2f} seconds...")
                                await asyncio.sleep(delay)
                                # Aplicar rate limiting adicional antes del retry
                                await rate_limiter.wait_if_needed()
                                continue
                            else:
                                logging.error(f"Failed to fetch robots.txt after {MAX_RATE_LIMIT_RETRIES} attempts due to 429 Rate Limit.")
                                return None
                        else:
                            logging.warning(f"No se pudo obtener robots.txt, estado HTTP: {response.status}")
                            return None
            except aiohttp.ClientHttpProxyError as e:
                proxy_manager.mark_proxy_failed(proxy)
                logging.error(f"Proxy error obteniendo robots.txt (proxy: {proxy}): {e}")
                return None
            except Exception as e:
                proxy_manager.mark_proxy_failed(proxy)
                logging.error(f"Error al obtener robots.txt (proxy: {proxy}): {e}")
                return None

    def parse_sitemap_xml(self, content, sitemap_url):
        """
        Intenta parsear el XML del sitemap usando diferentes métodos, empezando por los más robustos.
        """
        parsers = [
            ("lxml", lambda c: lxml_etree.fromstring(c.encode('utf-8'), parser=lxml_etree.XMLParser(recover=True, encoding='utf-8'))),
            ("beautifulsoup", lambda c: BeautifulSoup(c, 'xml')),
            ("etree", lambda c: ET.fromstring(c))
        ]

        for parser_name, parser_func in parsers:
            try:
                logging.info(f"Trying to parse sitemap with {parser_name}: {sitemap_url}")
                root = parser_func(content)
                logging.info(f"Successfully parsed sitemap with {parser_name}")
                return root, parser_name
            except Exception as e:
                logging.warning(f"Failed to parse sitemap with {parser_name}: {e}")
                continue

        logging.error(f"All XML parsers failed for sitemap {sitemap_url}")
        return None, None

    def extract_urls_from_parsed_xml(self, root, parser_name):
        """
        Extrae URLs del XML parseado, manejando diferentes formatos según el parser usado.
        """
        urls = []

        try:
            if parser_name == "beautifulsoup":
                # Para BeautifulSoup, buscar elementos sin namespace
                url_elements = root.find_all('url')
                for url_elem in url_elements:
                    loc = url_elem.find('loc')
                    if loc and loc.text:
                        urls.append(loc.text)

            elif parser_name in ["lxml", "etree"]:
                # Para lxml y etree, usar xpath con namespaces
                ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                url_elements = root.findall('.//sitemap:url/sitemap:loc', ns)
                urls = [url_elem.text for url_elem in url_elements if url_elem.text]

        except Exception as e:
            logging.error(f"Error extracting URLs from parsed XML: {e}")
            return []

        return urls

    def extract_secondary_sitemaps(self, root, parser_name):
        """
        Extrae URLs de sitemaps secundarios del XML parseado.
        """
        secondary_sitemaps = []

        try:
            if parser_name == "beautifulsoup":
                sitemaps = root.find_all('sitemap')
                for sitemap in sitemaps:
                    loc = sitemap.find('loc')
                    if loc and loc.text:
                        secondary_sitemaps.append(loc.text)

            elif parser_name in ["lxml", "etree"]:
                ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                sitemap_elements = root.findall('.//sitemap:sitemap', ns)
                for sitemap in sitemap_elements:
                    loc_elem = sitemap.find('.//sitemap:loc', ns)
                    if loc_elem is not None and loc_elem.text:
                        secondary_sitemaps.append(loc_elem.text)

        except Exception as e:
            logging.error(f"Error extracting secondary sitemaps: {e}")
            return []

        return secondary_sitemaps

    def is_xml_content(self, content):
        """
        Verifica si el contenido es XML puro o contiene elementos HTML/JS.
        """
        content_lower = content.lower().strip()
        # Si contiene elementos HTML típicos, no es XML puro
        html_indicators = ['<html', '<head', '<body', '<script', '<style', '<div', '<!doctype']
        return not any(indicator in content_lower for indicator in html_indicators)

    async def fetch_sitemap_content(self, sitemap_url):
        """
        Obtiene el contenido del sitemap.
        """
        from CONFIG import MAX_RATE_LIMIT_RETRIES
        max_retries = MAX_RATE_LIMIT_RETRIES

        # Determine URLs to try (handle http -> https upgrade automatically)
        urls_to_try = [sitemap_url]
        if sitemap_url.startswith("http://"):
            urls_to_try.append(sitemap_url.replace("http://", "https://"))

        for current_url in urls_to_try:
            for attempt in range(1, max_retries + 1):
                # Aplicar rate limiting antes de cualquier petición
                await rate_limiter.wait_if_needed()

                proxy = None
                if proxy_manager.should_use_proxy():
                    proxy = proxy_manager.get_next_proxy()

                try:
                    # Usar headers aleatorios para el primer intento, y rotar en reintentos por 429
                    headers = get_random_headers() if attempt == 1 else get_random_headers()

                    async with ClientSession(headers=headers) as session:
                        # Allow redirects=True by default in aiohttp
                        async with session.get(current_url, timeout=30, proxy=proxy, ssl=False) as response:
                            if response.status == 200:
                                raw_content = await response.read()
                                import gzip
                                try:
                                    content = gzip.decompress(raw_content).decode('utf-8')
                                except Exception:
                                    try:
                                        charset = response.charset or 'utf-8'
                                        content = raw_content.decode(charset)
                                    except UnicodeDecodeError:
                                        content = raw_content.decode('latin-1', errors='replace')
                                        
                                proxy_manager.mark_proxy_success(proxy)
                                from src.fetcher import consecutive_429_errors
                                consecutive_429_errors = 0
                                logging.info(f"Successfully fetched sitemap: {current_url}")
                                return content

                            elif response.status == 429:
                                from CONFIG import MAX_RATE_LIMIT_RETRIES, RATE_LIMIT_BACKOFF_MULTIPLIER
                                from src.fetcher import consecutive_429_errors, proxy_manager as fetcher_proxy_manager

                                consecutive_429_errors += 1
                                logging.warning(f"Rate limit exceeded (429) for sitemap {current_url}. Attempt {attempt}")
                                fetcher_proxy_manager.auto_enable_proxies_on_rate_limit(consecutive_429_errors)

                                if attempt < max_retries:
                                    delay = (RATE_LIMIT_BACKOFF_MULTIPLIER ** attempt) + random.uniform(2, 5)
                                    logging.info(f"Retrying in {delay:.2f} seconds...")
                                    await asyncio.sleep(delay)
                                    continue
                                else:
                                    logging.error(f"Failed to fetch {current_url} after retries (429).")
                                    # Don't break here, let the outer loop try 'https' if applicable
                            
                            else:
                                logging.warning(f"Sitemap fetch failed with status {response.status}: {current_url}")
                                proxy_manager.mark_proxy_failed(proxy)
                                break # Break retry loop, try next URL variant
                            
                except Exception as e:
                    proxy_manager.mark_proxy_failed(proxy)
                    logging.warning(f"Error fetching sitemap {current_url}: {e}")
                    # If it's a connection error, maybe allow retry?
                    break
        
        logging.error(f"Could not fetch sitemap content for: {sitemap_url}")
        return None

    async def get_urls_from_sitemap_recursive(self, sitemap_url, depth=0):
        """
        Procesa un sitemap de forma recursiva para extraer URLs. Si un sitemap contiene otros sitemaps,
        sigue procesando hasta que encuentre URLs finales.
        Maneja automáticamente XML mal formado usando diferentes parsers.
        """
        if depth > MAX_SITEMAPS:
            logging.warning(f"Max sitemap recursion depth ({MAX_SITEMAPS}) reached.")
            return []

        try:
            logging.info(f"Fetching sitemap: {sitemap_url}")
            content = await self.fetch_sitemap_content(sitemap_url)

            if content is None:
                logging.error(f"Could not fetch content for sitemap {sitemap_url}")
                return []

            # Intentar parsear el XML con diferentes métodos
            root, parser_name = self.parse_sitemap_xml(content, sitemap_url)

            if root is None:
                logging.error(f"Could not parse sitemap {sitemap_url} with any parser. Skipping.")
                return []

            # Extraer URLs del XML parseado
            urls = self.extract_urls_from_parsed_xml(root, parser_name)

            # Extraer URLs de sitemaps secundarios
            secondary_sitemap_urls = self.extract_secondary_sitemaps(root, parser_name)

            all_sitemaps = []

            # Si encontramos URLs, agregarlas al resultado
            if urls:
                all_sitemaps.append({'sitemap': sitemap_url, 'urls': urls})

            # Manejo recursivo de sitemaps secundarios
            for secondary_url in secondary_sitemap_urls:
                logging.info(f"Found secondary sitemap: {secondary_url}")
                secondary_sitemaps = await self.get_urls_from_sitemap_recursive(secondary_url, depth + 1)
                all_sitemaps.extend(secondary_sitemaps)

            return all_sitemaps

        except Exception as e:
            logging.error(f"Error processing sitemap {sitemap_url}: {e}")
            return []

    async def get_manual_links(self, manual_urls, max_products_per_link):
        """
        Extrae enlaces desde una o varias URLs proporcionadas manualmente.
        Útil como fallback cuando no hay sitemaps.
        """
        all_manual_data = []

        for url in manual_urls:
            # Ignorar URLs vacías
            if not url.strip():
                continue
                
            logging.info(f"Procesando URL manual (landing): {url}")
            try:
                # Reusar fetch_sitemap_content para obtener el HTML
                content = await self.fetch_sitemap_content(url)
                if not content:
                    logging.warning(f"No se pudo obtener el contenido de la URL manual: {url}")
                    continue

                soup = BeautifulSoup(content, 'html.parser')
                extracted_urls = set()

                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(url, href)
                    full_url = normalize_url(full_url)

                    # Verificar si es del mismo dominio y HTML
                    if is_same_domain(self.domain, full_url) and is_html_page(full_url):
                        # Evitar anclas a la misma página
                        parsed_full = urlparse(full_url)
                        parsed_base = urlparse(url)
                        if parsed_full.path != parsed_base.path:
                            # Filtro ignore_links
                            skip = False
                            for ignore_pattern in self.ignore_links:
                                if ignore_pattern and ignore_pattern in full_url:
                                    skip = True
                                    break
                            
                            if not skip:
                                extracted_urls.add(full_url)

                extracted_list = list(extracted_urls)
                logging.info(f"Encontrados {len(extracted_list)} enlaces totales en {url}")
                
                if max_products_per_link > 0 and len(extracted_list) > max_products_per_link:
                    extracted_list = extracted_list[:max_products_per_link]

                if extracted_list:
                    all_manual_data.append({'sitemap': f"Manual: {url}", 'urls': extracted_list})
                    logging.info(f"Seleccionados {len(extracted_list)} enlaces de {url}")

            except Exception as e:
                logging.error(f"Error procesando URL manual {url}: {e}")

        return all_manual_data
