import asyncio
import logging
import time
from bs4 import BeautifulSoup
import aiohttp
from CONFIG import IMAGE_CLASSES, TITLE_TAGS, DESCRIPTION_TAGS, PRICE_TAGS, LOWER_PRICE, CHECK_STOCK, STOCK_TAGS, STOCK_TEXT, OG_IMAGE, OG_DESCRIPTION, OG_TITLE, REQUEST_TIMEOUT, TITLE_SEPARATORS, MODIFY_DESCRIPTION, DESCRIPTION_ID, DELETE_DESCRIPTION_CHARACTERS, CHECK_PRICE, IMAGE_IDS, ROOT_URL, MODIFY_IMAGE_URL, CUSTOM_IMAGE_PATTERN
import re
from markdownify import markdownify as md
import re


async def fetch_title(session, url, semaphore, max_retries=3):
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                # headers = {
                #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                #                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                #                   'Chrome/85.0.4183.83 Safari/537.36',
                #     'Accept-Language': 'es-ES,es;q=0.9',
                #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                #     'Connection': 'keep-alive'
                # }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Referer': 'https://www.google.com/',
                    'DNT': '1',  # Do Not Track header
                }

                timeout = aiohttp.ClientTimeout(total=5)

                async with session.get(url, timeout=timeout, headers=headers) as response:
                    if response.status == 403:
                        logging.warning(f"Access forbidden (403) to {url}. Attempt {attempt} of {max_retries}")
                        if attempt < max_retries:
                            delay = 2 ** attempt
                            logging.info(f"Retrying {url} in {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logging.error(f"Failed to fetch {url} after {max_retries} attempts due to 403 Forbidden.")
                            return {'url': url, 'title': "Access forbidden (403)"}

                    elif response.status != 200:
                        return {'url': url, 'title': f"Status code: {response.status}"}

                    content = await response.text()
                    soup = BeautifulSoup(content, 'lxml')

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
                    return {'url': url, 'title': "Title not found" if not formatted_title else formatted_title}

            except asyncio.TimeoutError:
                logging.warning(f"Attempt {attempt}: Timed out fetching {url}")
                if attempt < max_retries:
                    delay = 2 ** attempt
                    logging.info(f"Retrying {url} in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"Failed to fetch {url} after {max_retries} attempts due to timeout.")
                    return {'url': url, 'title': "Timed out"}
            except Exception as e:
                logging.exception(f"Attempt {attempt}: Error fetching title from {url}: {e}")
                return {'url': url, 'title': "Error"}

def format_title(title):
    if not title:
        return None
    title_lower = title.lower()
    for separator in TITLE_SEPARATORS:
        index = title_lower.find(separator.lower())
        if index > 0:
            return title[:index].strip()
    return title.strip()



async def fetch_titles(urls, max_concurrent_requests=10):
    """
    Asynchronously fetch titles for a list of URLs.

    :param urls: List of URLs to fetch titles from.
    :param max_concurrent_requests: Maximum number of concurrent requests.
    :return: List of dictionaries with 'url' and 'title'.
    """
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent_requests)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_title(session, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

    # Manage Exceptions and remove urls with duplicated titles
    seen_titles = set()
    filtered_results = []
    for result in results:
        if isinstance(result, Exception):
            logging.exception(f"Error fetching title: {result}")
        elif result is None:
            continue
        elif result['title'] not in seen_titles:
                seen_titles.add(result['title'])
                filtered_results.append({
                    'url': result['url'],
                    'title': result['title']
                })

    return filtered_results

import re

def extract_prices(text):
    """
    Extrae todos los precios del texto, devolviendo una lista de precios numéricos.
    Detecta tanto precios con '€' delante como detrás del número.
    """
    # Expresión regular mejorada para detectar precios con formato europeo
    # Detecta precios con '€' delante o detrás del número
    prices = re.findall(r'€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)(?:\s*€)?', text)
    
    price_values = []
    for p in prices:
        # Eliminar los puntos (separadores de miles)
        p_no_thousand_sep = p.replace('.', '')
        # Reemplazar la coma decimal por punto
        p_standard = p_no_thousand_sep.replace(',', '.')
        try:
            price_value = float(p_standard)
            price_values.append(price_value)
        except ValueError:
            continue  # Omitir si no se puede convertir a float
    return price_values


def format_price(price_value):
    """
    Da formato al precio para que tenga el formato '0,00€'.
    """
    return f"{price_value:.2f}".replace('.', ',') + "€"

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
                if MODIFY_IMAGE_URL and image.startswith("../../../"):
                    image = ROOT_URL + image.replace("../../../", "")

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

    # Prioridad 4: IMAGE_CLASSES (respaldo)
    if not image:
        for img_class in IMAGE_CLASSES:
            img_tag = soup.find("a", class_=img_class)
            if img_tag:
                image = img_tag.get("href", "").strip()
                if image:
                    break

    # Prioridad 5: Custom pattern - buscar imágenes con patrón configurable
    if not image and CUSTOM_IMAGE_PATTERN:
        custom_images = soup.find_all('img', src=lambda x: x and CUSTOM_IMAGE_PATTERN in x)
        if custom_images:
            # Tomar la primera imagen que contenga información relevante en alt/title
            for img in custom_images:
                alt_text = img.get('alt', '').strip()
                title_text = img.get('title', '').strip()
                src_url = img.get('src', '').strip()

                # Priorizar imágenes que tengan texto descriptivo en alt o title
                if alt_text or title_text:
                    image = src_url
                    logging.info(f"Imagen encontrada via patrón personalizado '{CUSTOM_IMAGE_PATTERN}': {image}")
                    break

            # Si no se encontró ninguna con texto descriptivo, tomar la primera
            if not image and custom_images:
                image = custom_images[0].get('src', '').strip()
                logging.info(f"Imagen encontrada via patrón personalizado '{CUSTOM_IMAGE_PATTERN}' (primera encontrada): {image}")

    # Si no se encontró ninguna imagen
    if not image:
        image = "Image not found"

    # Extract description
    description = ''
    # Recorrer los DESCRIPTION_TAGS definidos en CONFIG.py
    for desc_tag in DESCRIPTION_TAGS:
        logging.info({'Se va a procesar': desc_tag})

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

        logging.info({'Número de elementos encontrados': len(elements)})

        for i, element in enumerate(elements):
            # Usar la función inteligente para extraer texto
            text_content = extract_text_smart(element)
            if text_content.strip():
                if description:  # Si ya hay contenido, agregar separador
                    description += '\n\n'
                description += text_content.strip()
                logging.info({f'description elemento {i+1}': text_content[:200] + '...' if len(text_content) > 200 else text_content})

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
        for price_tag in PRICE_TAGS:
            # Si el precio se encuentra por 'id' además de por 'class'
            if "id" in price_tag:
                # Buscar por id también
                elements = soup.find_all(price_tag["tag"], id=price_tag["id"])
            else:
                # Buscar solo por clase
                elements = soup.find_all(price_tag["tag"], class_=lambda c: c and price_tag["class"] in c)

            for element in elements:
                # Buscar primero dentro del <ins> (precio actual si hay descuento)
                ins_element = element.find("ins")
                if ins_element:
                    price_bdi = ins_element.find("bdi")
                    price_text = price_bdi.get_text(strip=True) if price_bdi else ins_element.get_text(strip=True)
                else:
                    # Si no hay <ins>, tomar el precio desde el <bdi> dentro del <p> o <span>
                    price_bdi = element.find("bdi")
                    price_text = price_bdi.get_text(strip=True) if price_bdi else element.get_text(strip=True)

                prices = extract_prices(price_text)
                price_list.extend(prices)

        price = "Price not found" if not price_list else format_price(price_list[0])  # Tomar el primer precio correcto

    in_stock = True
    if CHECK_STOCK:
        for stock_tag in STOCK_TAGS:
            tag = soup.find(stock_tag["tag"], class_=stock_tag["class"])
            if tag and STOCK_TEXT.lower() in tag.get_text().lower():
                in_stock = False
                break


    return {
        "image": image,
        "description": description.strip(),
        "price": price,
        "in_stock": in_stock
    }



async def fetch_details(session, url, title, semaphore, max_retries=3):
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": "https://www.google.com/",
                    "DNT": "1",
                }
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

                async with session.get(url, timeout=timeout, headers=headers) as response:
                    if response.status == 403:
                        logging.warning(f"Access forbidden (403) to {url}. Attempt {attempt} of {max_retries}")
                        if attempt < max_retries:
                            delay = 2 ** attempt
                            logging.info(f"Retrying {url} in {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logging.error(f"Failed to fetch {url} after {max_retries} attempts due to 403 Forbidden.")
                            return ('discarded', {'url': url, 'title': title, 'error': "Access forbidden (403)"})

                    elif response.status != 200:
                        logging.warning(f"Status code: {response.status}")
                        return ('discarded', {'url': url, 'title': title, 'error': f"Status code: {response.status}"})

                    content = await response.text()
                    soup = BeautifulSoup(content, 'lxml')
                    details = fetch_product_details_from_soup(soup)

                    if details["price"] == "Price not found":
                        logging.warning("Price not found")
                        return ('discarded', {'url': url, 'title': title})

                    if CHECK_STOCK and not details["in_stock"]:
                        return ('without_stock', {
                            "url": url,
                            "title": title,
                            "image": details["image"],
                            "description": details["description"],
                            "price": details["price"],
                            "in_stock": details["in_stock"]
                        })

                    return ('in_stock', {
                        "url": url,
                        "title": title,
                        "image": details["image"],
                        "description": details["description"],
                        "price": details["price"],
                        "in_stock": details["in_stock"]
                    })

            except Exception as e:
                logging.error(f"Error fetching details for {url}: {e}")
                return ('discarded', {'url': url, 'title': title, 'error': str(e)})
            
async def fetch_product_details(urls_titles, max_concurrent_requests=10):
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent_requests)

    in_stock_products = []
    without_stock_products = []
    discarded_products = []

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_details(session, url_title["url"], url_title["title"], semaphore) for url_title in urls_titles]
        results = await asyncio.gather(*tasks)

    for status, data in results:
        if status == 'in_stock':
            in_stock_products.append(data)
        elif status == 'without_stock':
            without_stock_products.append(data)
        elif status == 'discarded':
            discarded_products.append(data)
        else:
            # Handle errors or other statuses if needed
            pass

    return in_stock_products, without_stock_products, discarded_products

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


if __name__ == "__main__":
    # Sample URL to test the function
    test_url = "https://www.example.com"

    # Asynchronous call to fetch the title of the test URL
    async def main():
        # Define logging level
        logging.basicConfig(level=logging.INFO, encoding='utf-8')

        # Single URL title fetching
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(1)  # Only one request at a time
            title_result = await fetch_title(session, test_url, semaphore)
            print(f"Fetched title for {test_url}: {title_result}")

    # Run the asynchronous main function
    asyncio.run(main())