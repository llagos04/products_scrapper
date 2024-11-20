import asyncio
import logging
import time
from bs4 import BeautifulSoup
import aiohttp
from CONFIG import IMAGE_CLASSES, TITLE_TAGS, DESCRIPTION_TAGS, PRICE_TAGS, LOWER_PRICE, CHECK_STOCK, STOCK_TAGS, STOCK_TEXT, OG_IMAGE, OG_DESCRIPTION, OG_TITLE, REQUEST_TIMEOUT, TITLE_SEPARATORS, MODIFY_DESCRIPTION, DESCRIPTION_ID, DELETE_DESCRIPTION_CHARACTERS, CHECK_PRICE
import re
from markdownify import markdownify as md
import re


async def fetch_title(session, url, semaphore, max_retries=3):
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/85.0.4183.83 Safari/537.36',
                    'Accept-Language': 'es-ES,es;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive'
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

def extract_prices(text):
    """
    Extrae todos los precios del texto, devolviendo una lista de precios numéricos.
    """
    # Expresión regular para números con separadores de miles y decimales en formato europeo
    prices = re.findall(r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)\s*€', text)
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


def fetch_product_details_from_soup(soup):
    """
    Fetch product details from BeautifulSoup object and check for stock if needed.

    :param soup: BeautifulSoup object.
    :return: A dictionary with 'image', 'description', 'price', and 'in_stock'.
    """
    # Extract image URLs
    image = None
    if OG_IMAGE:
        meta_image = soup.find("meta", property="og:image")
        if meta_image:
            image = meta_image.get("content", "").strip()

    if not image:
        # Buscar todas las URLs de imágenes dentro de los divs con la clase específica
        easyzoom_divs = soup.find_all("div", class_="easyzoom easyzoom-product")
        image_urls = []

        for div in easyzoom_divs:
            img_tag = div.find("a", class_="js-easyzoom-trigger")
            if img_tag and img_tag.get("href"):
                image_urls.append(img_tag.get("href").strip())
        
        # Si encontramos al menos una URL, tomamos la primera como `image`
        if image_urls:
            image = image_urls[0]

        # En caso de que no se encuentre ninguna URL, usar IMAGE_CLASSES como respaldo
        if not image:
            for img_class in IMAGE_CLASSES:
                img_tag = soup.find("a", class_=img_class)
                if img_tag:
                    image = img_tag.get("href", "").strip()
                    if image:
                        break
            else:
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

        logging.info({'elements': elements})

        for element in elements:
            # Extraer el texto incluyendo elementos anidados
            text_content = element.get_text(separator='\n').strip()
            description += f"\n{text_content}"
            logging.info({'description': description})

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
    if CHECK_PRICE:
        price_list = []
    else:
        price_list = [0]
    for price_tag in PRICE_TAGS:
        tag = soup.find(price_tag["tag"], class_=price_tag["class"])
        if tag:
            price_text = tag.get_text().strip()
            prices = extract_prices(price_text)
            price_list.extend(prices)

    price = "Price not found" if not price_list else format_price(min(price_list) if LOWER_PRICE else price_list[0])

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
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/85.0.4183.83 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive'
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