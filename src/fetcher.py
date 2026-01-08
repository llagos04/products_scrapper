import asyncio
import logging
import time
import random
from bs4 import BeautifulSoup
import aiohttp
from CONFIG import IMAGE_CLASSES, TITLE_TAGS, DESCRIPTION_TAGS, PRICE_TAGS, LOWER_PRICE, OG_IMAGE, OG_DESCRIPTION, OG_TITLE, REQUEST_TIMEOUT, TITLE_SEPARATORS, MODIFY_DESCRIPTION, DELETE_DESCRIPTION_CHARACTERS, CHECK_PRICE, IMAGE_IDS, ROOT_URL, CHECK_STOCK, STOCK_TAGS, STOCK_IN_PATTERNS, STOCK_OUT_PATTERNS
import re
from markdownify import markdownify as md
import re
from CONFIG import USE_PROXIES, AUTO_FETCH_PROXIES, USE_RATE_LIMIT, MIN_REQUEST_DELAY, MAX_REQUEST_DELAY, BATCH_DELAY, RATE_LIMIT_BACKOFF_MULTIPLIER, MAX_RATE_LIMIT_RETRIES, HTML_LOAD_DELAY


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

    def auto_enable_proxies_on_rate_limit(self, consecutive_429_errors):
        """
        Activa automáticamente proxies si se detectan muchos errores 429 consecutivos
        """
        if consecutive_429_errors >= 3 and not self.use_proxies:
            logging.warning(f"Detectados {consecutive_429_errors} errores 429 consecutivos. Activando proxies automáticamente...")
            self.enable_proxies()
            # Intentar obtener proxies automáticamente
            asyncio.create_task(self.fetch_free_proxies(limit=10))
            return True
        return False


# Instancia global del gestor de proxies
proxy_manager = ProxyManager()


class RateLimiter:
    """
    Controla el rate limiting para evitar bloqueos por peticiones demasiado frecuentes
    """
    def __init__(self):
        self.last_request_time = 0
        self.use_rate_limiting = USE_RATE_LIMIT

    async def wait_if_needed(self):
        """
        Espera el tiempo necesario antes de hacer la siguiente petición
        """
        if not self.use_rate_limiting:
            return

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        min_delay = MIN_REQUEST_DELAY
        max_delay = MAX_REQUEST_DELAY

        # Calcular delay aleatorio
        required_delay = random.uniform(min_delay, max_delay)

        if time_since_last_request < required_delay:
            wait_time = required_delay - time_since_last_request
            logging.debug(f"Rate limiting: esperando {wait_time:.2f} segundos")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def wait_between_batches(self):
        """
        Espera entre batches de peticiones
        """
        if not self.use_rate_limiting:
            return

        logging.info(f"Esperando {BATCH_DELAY} segundos entre batches...")
        await asyncio.sleep(BATCH_DELAY)


# Instancia global del rate limiter
rate_limiter = RateLimiter()

# Contador global de errores 429 consecutivos
consecutive_429_errors = 0


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


def extract_title_from_soup(soup, url):
    """
    Helper to extract title from a BeautifulSoup object.
    """
    title = None
    if OG_TITLE:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")

    if not title:
        for entry in TITLE_TAGS:
            title_tag = soup.find(entry["tag"], class_=entry.get("class"))
            if title_tag:
                title = title_tag.get_text(strip=True)
                break

    formatted_title = format_title(title)
    return "Title not found" if not formatted_title else formatted_title

def format_title(title):
    if not title:
        return None
    title_lower = title.lower()
    for separator in TITLE_SEPARATORS:
        index = title_lower.find(separator.lower())
        if index > 0:
            return title[:index].strip()
    return title.strip()




import re

def extract_prices(text):
    """
    Extrae todos los precios del texto, devolviendo una lista de tuplas (precio, moneda).
    Detecta tanto precios con '€', '$', 'USD' delante como detrás del número.
    Maneja formatos europeos (1.234,56) y americanos (1,234.56).
    """
    # Limpiar el texto de entidades HTML y caracteres especiales
    import html
    text = html.unescape(text)  # Convertir &nbsp; a espacios, etc.

    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'\s+', ' ', text).strip()

    prices = []

    # Patrones para formato Europeo (1.234,56) - Prioridad para €
    # Ej: 1.234,56 € | € 1.234,56
    eu_patterns = [
        (r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)\s*€', '€'),
        (r'€\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)', '€'),
        (r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)€', '€'),
    ]

    # Patrones para formato Americano (1,234.56) - Prioridad para $ y USD
    # Ej: $ 1,234.56 | 1,234.56 $ | USD 1,234.56
    us_patterns = [
        (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', '$'),       # $ 1,234.56
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*\$', '$'),       # 1,234.56 $
        (r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', 'USD'),      # USD 1,234.56
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*USD', 'USD'),      # 1,234.56 USD
        (r'US\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', 'USD'),     # US$ 1,234.56
    ]

    # Patrón genérico (sin símbolo) - Ambigüedad
    generic_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)'

    # 1. Buscar coincidencias explícitas EU (coma decimal)
    for pattern, currency in eu_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            # Limpiar: quitar puntos de miles, cambiar coma a punto
            clean_val = m.replace('.', '').replace(',', '.')
            try:
                val = float(clean_val)
                prices.append((val, currency))
            except ValueError:
                pass

    # 2. Buscar coincidencias explícitas US (punto decimal)
    for pattern, currency in us_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            # Limpiar: quitar comas de miles
            clean_val = m.replace(',', '')
            try:
                val = float(clean_val)
                prices.append((val, currency))
            except ValueError:
                pass
    
    # 3. Si no encontramos nada con símbolos, intentar búsqueda genérica
    if not prices:
        # Buscamos números "sueltos" que parezcan precios
        matches = re.findall(generic_pattern, text)
        for m in matches:
            val = None
            currency = '€' # Default fallback if no symbol found, or maybe None?
            # Let's assume € for generic if ambiguous, or try to detect context?
            # For now, defaulting to € as per original behavior which assumed €
            
            if ',' in m and '.' in m:
                last_comma = m.rfind(',')
                last_dot = m.rfind('.')
                if last_comma > last_dot: # Formato EU: 1.234,56
                    clean_val = m.replace('.', '').replace(',', '.')
                    try: val = float(clean_val)
                    except: pass
                else: # Formato US: 1,234.56
                    clean_val = m.replace(',', '')
                    try: val = float(clean_val)
                    except: pass
                    currency = '$' # If it looks like US format, maybe default to $?
            elif ',' in m: # Solo comas: 17,90 o 1,234
                clean_val = m.replace(',', '.')
                try: val = float(clean_val)
                except: pass
            elif '.' in m: # Solo puntos: 17.90 o 1.234
                if re.search(r'\.\d{2}$', m):
                     try: val = float(m)
                     except: pass
                     currency = '$' # Likely US format
            
            if val is not None:
                prices.append((val, currency))

    # Eliminar duplicados manteniendo el orden
    seen = set()
    prices = [x for x in prices if not (x in seen or seen.add(x))]
    
    final_prices = []
    for p, c in prices:
        if 0.01 <= p <= 100000:
            final_prices.append((p, c))
            
    return final_prices


def format_price(price_value, currency='€'):
    """
    Da formato al precio para que tenga el formato '0,00€' o '$0.00' según la moneda.
    """
    if currency in ['$', 'USD']:
        return f"${price_value:.2f}"
    else:
        return f"{price_value:.2f}".replace('.', ',') + currency



def format_description(description):
    if not description:
        return description
    if MODIFY_DESCRIPTION:
        # Iterar sobre cada secuencia de caracteres a eliminar
        for del_chars in DELETE_DESCRIPTION_CHARACTERS:
            # Mientras la secuencia esté en la descripción, reemplázala
            while del_chars in description:
                description = description.replace(del_chars, '')
    return description


def extract_text_comprehensive(element, separator='\n'):
    """
    Extrae texto de manera comprehensiva de un elemento, incluyendo todos los elementos anidados.
    Maneja específicamente elementos complejos como divs con múltiples párrafos.
    """
    if not element:
        return ""

    # Para elementos que contienen texto directo y elementos anidados
    text_parts = []

    def extract_recursive(elem, depth=0):
        """Función recursiva para extraer texto de elementos anidados"""
        if elem.name in ['script', 'style', 'noscript']:
            return  # Omitir elementos que no contienen texto útil

        # Si es un elemento de texto directo
        if hasattr(elem, 'string') and elem.string and elem.string.strip():
            if depth > 0:  # Si no es el elemento raíz, agregar separador
                text_parts.append(elem.string.strip())
            else:
                text_parts.append(elem.string.strip())

        # Procesar elementos hijos
        if hasattr(elem, 'children'):
            for child in elem.children:
                if hasattr(child, 'name') and child.name:
                    # Es un tag HTML
                    extract_recursive(child, depth + 1)
                elif hasattr(child, 'string') and child.string and child.string.strip():
                    # Es texto directo
                    text_parts.append(child.string.strip())

    # Extraer texto recursivamente
    extract_recursive(element)

    # Unir todas las partes de texto con el separador
    if text_parts:
        return separator.join(text_parts)
    else:
        # Fallback al método estándar si no se encontró texto con el método recursivo
        return element.get_text(separator=separator).strip()


def extract_text_smart(element):
    """
    Extrae texto de manera inteligente, combinando toda la información relevante
    del elemento en lugar de devolver solo el primer método que encuentra algo.
    Especialmente diseñado para divs complejos como los de lmrgraphics.com
    """
    if not element:
        return ""

    all_text_parts = []

    # Método 1: Extraer título (h1)
    h1_elements = element.find_all('h1')
    for h1 in h1_elements:
        h1_text = h1.get_text(separator=' ').strip()
        if h1_text:
            all_text_parts.append(f"Título: {h1_text}")

    # Método 2: Extraer breadcrumbs
    breadcrumb_elements = element.find_all(['p'], class_=lambda c: c and 'breadcrumb' in c)
    for breadcrumb in breadcrumb_elements:
        breadcrumb_text = breadcrumb.get_text(separator=' ').strip()
        if breadcrumb_text:
            all_text_parts.append(f"Categoría: {breadcrumb_text}")

    # Método 3: Extraer información importante de alertas
    alerts = element.find_all(['div'], class_=lambda c: c and 'alert' in c)
    for alert in alerts:
        alert_content = alert.get_text(separator='\n').strip()
        if alert_content:
            all_text_parts.append(f"Información importante:\n{alert_content}")

    # Método 4: Extraer información de entrega/envío
    delivery_elements = element.find_all(['div'], class_=lambda c: c and ('success' in c or 'info' in c))
    for delivery in delivery_elements:
        delivery_text = delivery.get_text(separator=' ').strip()
        if delivery_text and ('días' in delivery_text.lower() or 'entrega' in delivery_text.lower() or 'envío' in delivery_text.lower()):
            all_text_parts.append(f"Información de entrega: {delivery_text}")

    # Método 5: Extraer opciones importantes del formulario
    forms = element.find_all('form')
    for form in forms:
        selects = form.find_all('select')
        for select in selects:
            label = select.find_previous('label')
            if label:
                label_text = label.get_text().strip()
                if 'tamaño' in label_text.lower() or 'acabado' in label_text.lower() or 'laminado' in label_text.lower():
                    options = select.find_all('option')
                    option_texts = []
                    for option in options[1:]:  # Omitir la primera opción (placeholder)
                        opt_text = option.get_text().strip()
                        if opt_text and not opt_text.startswith('Selecciona'):
                            option_texts.append(opt_text)
                    if option_texts:
                        all_text_parts.append(f"{label_text}: {', '.join(option_texts[:5])}")  # Mostrar más opciones

    # Método 6: Si no encontramos información específica, extraer párrafos
    if not all_text_parts:
        paragraphs = element.find_all('p')
        for p in paragraphs:
            p_text = p.get_text(separator=' ').strip()
            if p_text and len(p_text) > 5:  # Solo párrafos significativos
                all_text_parts.append(p_text)

    # Método 7: Si aún no tenemos contenido, usar el método comprehensivo
    if not all_text_parts:
        comprehensive_text = extract_text_comprehensive(element, '\n')
        if comprehensive_text:
            all_text_parts.append(comprehensive_text)

    # Unir todos los textos encontrados
    return '\n\n'.join(all_text_parts)


def fetch_product_details_from_soup(soup):
    """
    Fetch product details from BeautifulSoup object and check for stock if needed.

    :param soup: BeautifulSoup object.
    :return: A dictionary with 'image', 'description', 'price', and 'in_stock'.
    """
    # Extract image URLs
    image = None

    # Prioridad 1: OG_IMAGE
    if OG_IMAGE:
        meta_image = soup.find("meta", property="og:image")
        if meta_image:
            image = meta_image.get("content", "").strip()

    # Prioridad 2: Buscar por IDs específicos (IMAGE_IDS)
    if not image:
        for img_id in IMAGE_IDS:
            img_tag = soup.find("img", id=img_id)
            if img_tag:
                image = img_tag.get("src", "").strip()


                if image:
                    break

    # Prioridad 3: easyzoom-product (divs con imágenes)
    if not image:
        easyzoom_divs = soup.find_all("div", class_="easyzoom easyzoom-product")
        image_urls = []

        for div in easyzoom_divs:
            img_tag = div.find("a", class_="js-easyzoom-trigger")
            if img_tag and img_tag.get("href"):
                image_urls.append(img_tag.get("href").strip())

        if image_urls:
            image = image_urls[0]

    # Prioridad 3.5: cloud-zoom (tiendafetichista.com y sitios similares)
    if not image:
        cloud_zoom_links = soup.find_all("a", class_=lambda c: c and "cloud-zoom" in c)
        for link in cloud_zoom_links:
            href = link.get("href", "").strip()
            if href and (href.endswith('.jpg') or href.endswith('.png') or href.endswith('.jpeg') or href.endswith('.webp')):
                # Resolver URL relativa si es necesario
                if href.startswith('/') and ROOT_URL:
                    href = ROOT_URL.rstrip('/') + href
                image = href
                logging.info(f"Imagen encontrada via cloud-zoom: {image}")
                break

    # Prioridad 4: IMAGE_CLASSES (respaldo)
    if not image:
        for img_class in IMAGE_CLASSES:
            # 4.a) Buscar primero <img> con las clases configuradas
            img_el = soup.find("img", class_=lambda c: c and all(cls in c for cls in img_class.split()))
            if img_el:
                src_attr = img_el.get("src") or img_el.get("data-src") or img_el.get("data-original")
                if src_attr:
                    candidate = src_attr.strip()
                    # Resolver URL relativa comenzando por '/'
                    if candidate.startswith('/') and ROOT_URL:
                        candidate = ROOT_URL.rstrip('/') + candidate
                    image = candidate
                    if image:
                        break

            # 4.b) Como alternativa, buscar <a> con esas clases y tomar href
            a_el = soup.find("a", class_=lambda c: c and all(cls in c for cls in img_class.split()))
            if a_el:
                href = a_el.get("href", "").strip()
                if href:
                    if href.startswith('/') and ROOT_URL:
                        href = ROOT_URL.rstrip('/') + href
                    image = href
                    if image:
                        break

    # Prioridad 5: Custom pattern - buscar imágenes con patrón configurable


    # Si no se encontró ninguna imagen
    if not image:
        image = "Image not found"

    # Extract description
    description = ''
    # Prioridad 1: OG_DESCRIPTION
    if OG_DESCRIPTION:
        og_description = soup.find("meta", property="og:description")
        if og_description and og_description.get("content"):
            description = og_description.get("content")
    
    # Si no encontramos og:description, recorrer los DESCRIPTION_TAGS definidos en CONFIG.py
    if not description:
        # for desc_tag in DESCRIPTION_TAGS:
        #     logging.debug({'Se va a procesar': desc_tag})
        # ... (removed verbose commented code to clean up) ...

        for desc_tag in DESCRIPTION_TAGS:
            logging.debug({'Se va a procesar': desc_tag})

            # Determinar si buscar por 'class' o 'id'
            if "class" in desc_tag:
                # Buscar todos los elementos que coincidan con el tag y cuya clase contenga la clase especificada
                elements = soup.find_all(desc_tag["tag"], class_=lambda c: c and desc_tag["class"] in c)
            elif "id" in desc_tag:
                # Buscar todos los elementos que coincidan con el tag y el id especificado
                elements = soup.find_all(desc_tag["tag"], id=desc_tag["id"])
            else:
                # Si no hay ni 'class' ni 'id', buscar solo por el tag
                elements = soup.find_all(desc_tag["tag"])

            logging.debug({'Número de elementos encontrados': len(elements)})

            # Evitar añadir descripciones duplicadas cuando hay elementos gemelos (desktop/mobile, duplicados por layout)
            seen_element_texts = set()

            for i, element in enumerate(elements):
                # Extraer absolutamente todo el texto del div indicado (incluyendo subnodos)
                raw_text = extract_text_comprehensive(element, '\n')

                # Normalizar para comparar duplicados a nivel de elemento
                normalized_for_set = re.sub(r'\s+', ' ', raw_text).strip().lower()
                if not normalized_for_set:
                    continue
                if normalized_for_set in seen_element_texts:
                    continue
                seen_element_texts.add(normalized_for_set)

                # Eliminar líneas consecutivas duplicadas dentro del propio bloque extraído
                lines = [line.rstrip() for line in raw_text.splitlines()]
                deduped_lines = []
                for line in lines:
                    if not deduped_lines or deduped_lines[-1] != line:
                        deduped_lines.append(line)
                text_content = '\n'.join([l for l in deduped_lines if l.strip()])

                if text_content.strip():
                    if description:  # Si ya hay contenido, agregar separador
                        description += '\n\n'
                    description += text_content.strip()
                    logging.debug({f'description elemento {i+1}': text_content[:200] + '...' if len(text_content) > 200 else text_content})

        # Continuamos con el siguiente desc_tag sin romper el bucle

    if not description.strip():
        description = "Description not found"
    else:
        # Remover saltos de línea extra y espacios en blanco
        description = re.sub(r'\n\s*\n+', '\n\n', description)
        description = '\n'.join([line.rstrip() for line in description.splitlines() if line.strip()])
        if MODIFY_DESCRIPTION:
            description = format_description(description)

    # Buscar en todo el HTML un enlace a un archivo PDF y añadirlo al final de la descripción
    technical_sheet_url = None
    a_tags = soup.find_all('a', href=True)
    for a_tag in a_tags:
        href = a_tag['href']
        if href.lower().endswith('.pdf'):
            technical_sheet_url = href.strip()
            break

    # Añadir la URL al final de la descripción si se encontró
    if technical_sheet_url:
        description += f"\n\nFicha técnica: {technical_sheet_url}"

    # Extract prices
    if not CHECK_PRICE:
        price = format_price(0)
    else:
        price_list = []
        logging.debug(f"Starting price extraction. CHECK_PRICE=True. Tags to check: {len(PRICE_TAGS)}")
        
        for i, price_tag in enumerate(PRICE_TAGS):
            logging.debug(f"Checking tag {i+1}/{len(PRICE_TAGS)}: {price_tag}")
            
            # Si el precio se encuentra por 'id' además de por 'class'
            if "id" in price_tag:
                # Buscar por id también
                elements = soup.find_all(price_tag["tag"], id=price_tag["id"])
                logging.debug(f"Found {len(elements)} elements by ID '{price_tag['id']}'")
            else:
                # Buscar solo por clase
                elements = soup.find_all(price_tag["tag"], class_=lambda c: c and price_tag["class"] in c)
                logging.debug(f"Found {len(elements)} elements by Class '{price_tag['class']}'")

            for j, element in enumerate(elements):
                logging.debug(f"Processing element {j+1}/{len(elements)}")
                # Logging del contenido raw del elemento (truncado)
                raw_html = str(element)[:200].replace('\n', ' ')
                logging.debug(f"Element HTML (truncated): {raw_html}...")

                # Buscar primero dentro del <ins> (precio actual si hay descuento)
                ins_element = element.find("ins")
                if ins_element:
                    logging.debug("Found <ins> element")
                    price_bdi = ins_element.find("bdi")
                    if price_bdi:
                        logging.debug("Found <bdi> inside <ins>")
                        price_text = price_bdi.get_text(strip=True)
                    else:
                        logging.debug("No <bdi> inside <ins>, using <ins> text")
                        price_text = ins_element.get_text(strip=True)
                else:
                    logging.debug("No <ins> element found")
                    # Si no hay <ins>, tomar el precio desde el <bdi> dentro del <span>
                    price_bdi = element.find("bdi")
                    if price_bdi:
                        logging.debug("Found <bdi> element")
                        price_text = price_bdi.get_text(strip=True)
                    else:
                        logging.debug("No <bdi> element found, using direct element text")
                        # Si no hay <bdi>, intentar extraer directamente del elemento
                        price_text = element.get_text(strip=True)

                # Extraer precios del texto
                logging.debug(f"Raw extracted text for price: '{price_text}'")
                prices = extract_prices(price_text)
                logging.debug(f"Extracted prices from text: {prices}")
                
                if not prices:
                    # Si no se encontraron precios, intentar con el texto completo del elemento
                    full_text = element.get_text(strip=True)
                    if full_text != price_text:
                        logging.debug(f"Retrying with full element text: '{full_text[:100]}...'")
                        prices = extract_prices(full_text)
                        logging.debug(f"Extracted prices from full text: {prices}")

                price_list.extend(prices)
        
        logging.debug(f"Final collected price list: {price_list}")
        if not price_list:
            price = "Price not found"
        else:
            if LOWER_PRICE:
                # Si LOWER_PRICE es True, tomamos el menor precio encontrado
                # price_list es una lista de tuplas (valor, moneda)
                best_price = min(price_list, key=lambda x: x[0])
                price = format_price(best_price[0], best_price[1])
            else:
                # Si LOWER_PRICE es False, tomamos el primer precio encontrado
                best_price = price_list[0]
                price = format_price(best_price[0], best_price[1])





    # Extract Stock
    stock_status = "yes" # Default to yes (in stock)
    if CHECK_STOCK:
        for stock_tag in STOCK_TAGS:
            if "id" in stock_tag:
                 elements = soup.find_all(stock_tag["tag"], id=stock_tag["id"])
            else:
                 elements = soup.find_all(stock_tag["tag"], class_=lambda c: c and stock_tag["class"] in c)
            
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                logging.debug(f"Checking stock element text: '{text}'")
                
                found = False
                for pattern in STOCK_IN_PATTERNS:
                    if pattern.lower() in text.lower():
                        stock_status = "yes"
                        found = True
                        break
                if found: break
                
                for pattern in STOCK_OUT_PATTERNS:
                     if pattern.lower() in text.lower():
                         stock_status = "false"
                         found = True
                         break
                if found: break
            
            if stock_status == "false": break # Stop if definitely out of stock


    # Extract title
    title = extract_title_from_soup(soup, "") # URL not needed for title extraction in this helper

    return {
        "title": title,
        "image": image,
        "description": description.strip(),
        "price": price,
        "stock": stock_status
    }




class ProductFetcher:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.proxy_manager = ProxyManager()
        self.consecutive_429_errors = 0

    async def fetch_details(self, session, url, semaphore, max_retries=3):
        async with semaphore:
            # Aplicar rate limiting antes de cualquier petición
            await self.rate_limiter.wait_if_needed()

            for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
                proxy = None
                if self.proxy_manager.should_use_proxy():
                    proxy = self.proxy_manager.get_next_proxy()

                try:
                    # Usar headers rotativos para cada request
                    headers = get_random_headers()
                    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

                    async with session.get(url, timeout=timeout, headers=headers, proxy=proxy) as response:
                        if response.status == 403:
                            logging.warning(f"Access forbidden (403) to {url}. Attempt {attempt} of {max_retries}")
                            if attempt < max_retries:
                                delay = 2 ** attempt
                                logging.info(f"Retrying {url} in {delay} seconds...")
                                await asyncio.sleep(delay)
                                continue
                            else:
                                logging.error(f"Failed to fetch {url} after {max_retries} attempts due to 403 Forbidden.")
                                return ('discarded', {'url': url, 'title': "Access forbidden (403)", 'error': "Access forbidden (403)"})

                        elif response.status == 429:
                            self.consecutive_429_errors += 1
                            logging.warning(f"Rate limit exceeded (429) to {url}. Attempt {attempt} of {MAX_RATE_LIMIT_RETRIES}. Consecutive 429 errors: {self.consecutive_429_errors}")

                            # Activar proxies automáticamente si hay muchos errores 429
                            self.proxy_manager.auto_enable_proxies_on_rate_limit(self.consecutive_429_errors)

                            if attempt < MAX_RATE_LIMIT_RETRIES:
                                # Generar nuevos headers aleatorios
                                new_headers = get_random_headers()
                                logging.info(f"New headers for retry: User-Agent: {new_headers['User-Agent']}")
                                # Esperar con backoff exponencial mejorado para rate limit
                                delay = (RATE_LIMIT_BACKOFF_MULTIPLIER ** attempt) + random.uniform(2, 5)
                                logging.info(f"Rate limit detected. Retrying {url} with new headers in {delay:.2f} seconds...")
                                await asyncio.sleep(delay)
                                # Aplicar rate limiting adicional antes del retry
                                await self.rate_limiter.wait_if_needed()
                                continue
                            else:
                                logging.error(f"Failed to fetch {url} after {MAX_RATE_LIMIT_RETRIES} attempts due to 429 Rate Limit.")
                                return ('discarded', {'url': url, 'title': "Rate limit exceeded (429)", 'error': "Rate limit exceeded (429)"})

                        elif response.status != 200:
                            logging.warning(f"Status code: {response.status}")
                            return ('discarded', {'url': url, 'title': f"Status code: {response.status}", 'error': f"Status code: {response.status}"})

                        try:
                            # Read bytes and try to decode with replacement for errors
                            content_bytes = await response.read()
                            content = content_bytes.decode('utf-8', errors='replace')
                        except Exception as e:
                            logging.warning(f"Error decoding content for {url}: {e}. Fallback to text() with errors='replace'")
                            content = await response.text(errors='replace')
                        
                        if HTML_LOAD_DELAY > 0:
                            logging.info(f"Waiting {HTML_LOAD_DELAY} seconds for HTML load delay...")
                            await asyncio.sleep(HTML_LOAD_DELAY)

                        soup = BeautifulSoup(content, 'lxml')
                        details = fetch_product_details_from_soup(soup)

                        # Marcar proxy como exitoso y resetear contador de errores 429
                        self.proxy_manager.mark_proxy_success(proxy)
                        self.consecutive_429_errors = 0  # Resetear contador en petición exitosa

                        if details["price"] == "Price not found":
                            logging.warning("Price not found")
                            return ('discarded', {'url': url, 'title': details['title']})

                        return ('in_stock', {
                            "url": url,
                            "title": details["title"],
                            "image": details["image"],
                            "description": details["description"],
                            "price": details["price"],
                            "stock": details["stock"]
                        })

                except aiohttp.ClientHttpProxyError as e:
                    self.proxy_manager.mark_proxy_failed(proxy)
                    logging.error(f"Proxy error fetching details for {url} (proxy: {proxy}): {e}")
                    return ('discarded', {'url': url, 'title': 'Proxy Error', 'error': f'Proxy Error: {str(e)}'})
                except Exception as e:
                    self.proxy_manager.mark_proxy_failed(proxy)
                    logging.error(f"Error fetching details for {url} (proxy: {proxy}): {e}")
                    return ('discarded', {'url': url, 'title': 'Error', 'error': str(e)})

    async def fetch_product_details(self, urls, max_concurrent_requests=10):
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        connector = aiohttp.TCPConnector(limit_per_host=max_concurrent_requests)

        products = []
        discarded_products = []

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.fetch_details(session, url, semaphore) for url in urls]
            results = await asyncio.gather(*tasks)

        for status, data in results:
            if status == 'in_stock':
                products.append(data)
            elif status == 'discarded':
                discarded_products.append(data)
            else:
                # Handle errors or other statuses if needed
                pass

        return products, discarded_products

# Mantenemos una función de compatibilidad para código legado que no usa la clase,
# pero ahora instanciará su propio fetcher temporal.
# OJO: Esto no compartirá estado con otros llamadas.
async def fetch_product_details(urls, max_concurrent_requests=10):
    fetcher = ProductFetcher()
    return await fetcher.fetch_product_details(urls, max_concurrent_requests)


def test_extract_text_smart():
    """
    Función de prueba para mostrar cómo funciona extract_text_smart con el HTML de ejemplo
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("BeautifulSoup no está disponible")
        return ""

    # HTML de ejemplo proporcionado por el usuario
    html_content = '''
    <div class="col-md-6 col-xl-4 col-xxl-3 ">
        <h1><a href="https://www.lmrgraphics.com/kit-adhesivos/adhesivos-moto-enduro/-50-aniversario">HONDA 50 ANIVERSARIO</a></h1>
        <p class="breadcrumb"><a href="https://www.lmrgraphics.com/kit-adhesivos/adhesivos-moto-enduro/pegatinas-honda">HONDA -  CR &amp; CRF</a></p>
        <p class="breadcrumb"><a href="https://www.lmrgraphics.com/honda">Honda</a></p>
        <div class="item-description"></div>
        <div class="alert alert-info  fade show"><p><strong><span class="text-secondary">Los diseños son adaptables a todas las cilindradas y años.</span></strong></p>
        <p><strong><span class="text-secondary">Rellena todo el contenido de nuestro personalizador.</span></strong></p>
        <p><strong><span class="text-secondary">Si tienes más detalles que contarnos coméntalo en el campo de notas.</span></strong></p>
        <p><strong><span class="text-secondary">Si quieres adjuntar tus logos, imágenes, etc puedes enviarlos a &nbsp;la web@lmrgraphics.com con tu número de pedido.</span></strong></p></div>
        <div class="zona-pago mb-4">
            <div class="text-success mb-3">Producto personalizado, entrega de 4 a 10 días</div>
            <form action="https://www.lmrgraphics.com/basic/p/shop/add_to_cart" class="form-ajax" id="form-addtocart" method="post">
                <select name="bike_size" class="form-select calc_price">
                    <option value="">Selecciona...</option>
                    <option value="50cc">50cc</option>
                    <option value="65cc +">65cc + (20,00 €)</option>
                    <option value="85cc / pit bike +">85cc / Pit Bike + (45,00 €)</option>
                    <option value="125cc - 450 cc +">125cc - 450 cc + (60,00 €)</option>
                </select>
                <select name="laminate" class="form-select calc_price">
                    <option value="">Selecciona...</option>
                    <option value="brillo ( estándar )">Brillo ( estándar ) (0,00 €)</option>
                    <option value="matte">Matte (0,00 €)</option>
                    <option value="cosmic shift +">Cosmic Shift + (15,00 €)</option>
                </select>
            </form>
        </div>
    </div>
    '''

    soup = BeautifulSoup(html_content, 'html.parser')
    main_div = soup.find('div', class_=lambda c: c and 'col-md-6' in c)

    if main_div:
        extracted_text = extract_text_smart(main_div)
        print("=" * 80)
        print("TEXTO EXTRAÍDO DEL DIV DE EJEMPLO:")
        print("=" * 80)
        print(extracted_text)
        print("=" * 80)
        return extracted_text

    return "No se encontró el div principal"


# Global instance for backward compatibility (used by crawler.py)
rate_limiter = RateLimiter()

if __name__ == "__main__":
    # Sample URL to test the function
    test_url = "https://www.example.com"

    # Asynchronous call to fetch the title of the test URL
    async def main():
        # Define logging level
        logging.basicConfig(level=logging.INFO, encoding='utf-8')

        # Single URL title fetching
        session_headers = get_random_headers()
        async with aiohttp.ClientSession(headers=session_headers) as session:
            semaphore = asyncio.Semaphore(1)  # Only one request at a time
            title_result = await fetch_title(session, test_url, semaphore)
            print(f"Fetched title for {test_url}: {title_result}")

    # Run the asynchronous main function
    asyncio.run(main())