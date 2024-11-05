import asyncio
import logging
import time
from bs4 import BeautifulSoup
import aiohttp
from CONFIG import IMAGE_CLASSES, TITLE_TAGS, DESCRIPTION_TAGS, PRICE_TAGS, LOWER_PRICE, CHECK_STOCK, STOCK_TAGS, STOCK_TEXT, OG_IMAGE, OG_DESCRIPTION, OG_TITLE, REQUEST_TIMEOUT, TITLE_SEPARATORS, MODIFY_DESCRIPTION, DELETE_DESCRIPTION_CHARACTERS
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
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive'
                }
                timeout = aiohttp.ClientTimeout(total=5)  # Total timeout of 5 seconds

                async with session.get(url, timeout=timeout, headers=headers) as response:
                    if response.status != 200:
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
                    return None
            except Exception as e:
                logging.exception(f"Attempt {attempt}: Error fetching title from {url}: {e}")
                return None

def format_title(title):
    if not title:
        return None
    for separator in TITLE_SEPARATORS:
        if separator in title:
            parts = title.split(separator)
            return parts[0].strip()
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
    # Extract image URL
    image = None
    if OG_IMAGE:
        meta_image = soup.find("meta", property="og:image")
        if meta_image:
            image = meta_image.get("content", "").strip()

    if not image:
        for img_class in IMAGE_CLASSES:
            img_tag = soup.find("img", class_=img_class)
            if img_tag:
                image = img_tag.get("src", "").strip()
                if image:
                    break
        else:
            image = "Image not found"

    # Extract description
    description = None
    # Recorrer los DESCRIPTION_TAGS definidos en CONFIG.py
    for desc_tag in DESCRIPTION_TAGS:
        # Intentamos encontrar todos los divs que contienen la clase
        logging.info({'Se va a procesar': desc_tag})
        divs = soup.find_all(desc_tag["tag"], class_=desc_tag["class"])
        logging.info({'divs': divs})

        # Verificamos cada div para asegurarnos de que tiene exactamente la clase que queremos
        for div in divs:
            # Verificar que el div tiene exactamente la clase especificada
            if div.get("class") == [desc_tag["class"]]:  
                # Extraer el contenido HTML interno del div
                logging.info({'div': div})
                html_content = div.decode_contents()
                logging.info({'html_content': html_content})
                
                # **Limpieza del HTML**
                # Crear un objeto BeautifulSoup
                soup_desc = BeautifulSoup(html_content, 'html.parser')
                

                logging.debug(f"HTML content being parsed: {html_content[:500]}")
                
                # Reemplazar <br> con saltos de línea
                for br in soup_desc.find_all("br"):
                    br.replace_with("\n")
                
                # Eliminar párrafos vacíos y espacios no rompientes
                for p in soup_desc.find_all('p'):
                    # Eliminar espacios no rompientes
                    for elem in p.contents:
                        if isinstance(elem, str):
                            elem.replace_with(elem.replace('\xa0', ' '))
                    if not p.get_text(strip=True):
                        p.decompose()
                
                # Eliminar etiquetas vacías como <div>, <span>
                for tag in soup_desc.find_all():
                    if tag.name in ['div', 'span', 'p'] and not tag.get_text(strip=True):
                        tag.decompose()
                
                # Obtener el HTML limpio
                clean_html = str(soup_desc)
                
                # **Conversión a Markdown**
                description = md(clean_html)
                
                # **Postprocesamiento del texto Markdown**
                # Eliminar espacios en blanco al inicio y final
                description = description.strip()
                
                # Reemplazar múltiples líneas en blanco por una sola
                description = re.sub(r'\n\s*\n+', '\n\n', description)
                
                # Eliminar líneas que contienen solo espacios
                description = '\n'.join([line.rstrip() for line in description.splitlines() if line.strip()])
                
                logging.info({'description': description})

                break  # Rompemos el bucle si encontramos la descripción

        if description:  # Rompemos si ya hemos encontrado una descripción válida
            break

    # Si no se encontró ninguna descripción válida
    if not description:
        description = "Description not found"
    else:
        # Formatear la descripción
        description = format_description(description)


    # Extract prices
    price_list = []
    for price_tag in PRICE_TAGS:
        tag = soup.find(price_tag["tag"], class_=price_tag["class"])
        if tag:
            price_text = tag.get_text().strip()
            prices = extract_prices(price_text)
            price_list.extend(prices)

    if not price_list:
        price = "Price not found"
    else:
        # Choose the lowest price if LOWER_PRICE is True
        if LOWER_PRICE:
            price = format_price(min(price_list))
        else:
            price = format_price(price_list[0])  # Use the first found price if not selecting the lowest

    # Check stock availability
    in_stock = True
    if CHECK_STOCK:
        for stock_tag in STOCK_TAGS:
            tag = soup.find(stock_tag["tag"], class_=stock_tag["class"])
            if tag and STOCK_TEXT.lower() in tag.get_text().lower():
                in_stock = False
                break

    return {
        "image": image,
        "description": description,
        "price": price,
        "in_stock": in_stock
    }

async def fetch_details(session, url, title, semaphore):
    async with semaphore:
        try:
            headers = {
                # Your headers here
            }
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

            async with session.get(url, timeout=timeout, headers=headers) as response:
                if response.status != 200:
                    logging.warning(f"Status code: {response.status}")
                                        # Include the URL in discarded products
                    return ('discarded', {'url': url, 'title': title})

                content = await response.text()
                soup = BeautifulSoup(content, 'lxml')
                logging.info({'soup': soup})
                details = fetch_product_details_from_soup(soup)

                # If no price is found, discard
                if details["price"] == "Price not found":
                    logging.warning("Price not found")
                    return ('discarded', {'url': url, 'title': title})

                # If product is out of stock
                if CHECK_STOCK and not details["in_stock"]:
                    return ('without_stock', {
                        "url": url,
                        "title": title,
                        "image": details["image"],
                        "description": details["description"],
                        "price": details["price"],
                        "in_stock": details["in_stock"]
                    })

                # Product is in stock and has price
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
            # Include the URL in discarded products
            return ('discarded', {'url': url, 'title': title})

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