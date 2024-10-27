import asyncio
import logging
import time
from bs4 import BeautifulSoup
import aiohttp
from CONFIG import IMAGE_CLASSES, TITLE_TAGS, DESCRIPTION_TAGS, PRICE_TAGS, LOWER_PRICE, CHECK_STOCK, STOCK_TAGS, STOCK_TEXT, NO_OG_IMAGE, NO_OG_DESCRIPTION, NO_OG_TITLE, REQUEST_TIMEOUT
import re


async def fetch_title(session, url, semaphore, max_retries=3):
    """
    Asynchronously fetch the title of a web page, with retries on timeout.

    :param session: The aiohttp client session.
    :param url: The URL to fetch.
    :param semaphore: Semaphore to limit concurrent requests.
    :param max_retries: Maximum number of retries on timeout.
    :return: A dictionary with 'url' and 'title'.
    """
    async with semaphore:
        # Remove the initial fixed delay as we handle delays during retries
        # await asyncio.sleep(0.5)
        for attempt in range(1, max_retries + 1):
            try:
                # Custom headers to mimic a real browser
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

                    # Parse the HTML content efficiently
                    soup = BeautifulSoup(content, 'lxml')

                    # Try to extract the Open Graph title
                    title = None
                    if not NO_OG_TITLE:
                        og_title = soup.find("meta", property="og:title")
                        if og_title and og_title.get("content"):
                            title = og_title.get("content")

                    # try other title tags
                    if not title:
                        # Iterate through each specified tag and attribute in TITLE_TAGS
                        for entry in TITLE_TAGS:
                            # Use ** to unpack dictionary entries as keyword arguments
                            title = soup.find(entry["tag"], class_=entry.get("class"))
                            if title:
                                # Extract text and strip any excess whitespace
                                title = title.get_text(strip=True)
                                break

                    return {'url': url, 'title': "Title not found" if not title else title}
            except asyncio.TimeoutError:
                logging.warning(f"Attempt {attempt}: Timed out fetching {url}")
                if attempt < max_retries:
                    # Exponential backoff delay
                    delay = 2 ** attempt  # e.g., 2, 4, 8 seconds
                    logging.info(f"Retrying {url} in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"Failed to fetch {url} after {max_retries} attempts due to timeout.")
                    return None
            except Exception as e:
                #logging.exception(f"Attempt {attempt}: Error fetching title from {url}: {e}")
                return None
            
def format_title(title):
    if not title:
        return None
    title = re.split(r'\s[-|]\s', title)[0]
    return title

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

    logging.info(f"Found {len(filtered_results)} unique titles")

    return filtered_results

def fetch_product_details_from_soup(soup):
    """
    Fetch product details from BeautifulSoup object and check for stock if needed.

    :param soup: BeautifulSoup object.
    :return: A dictionary with 'image', 'description', 'price', and 'in_stock'.
    """

    # Extract image URL
    image = None
    if not NO_OG_IMAGE:
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
    if not NO_OG_DESCRIPTION:
        meta_description = soup.find("meta", property="og:description")
        if meta_description:
            description = meta_description.get("content", "").strip()

    if not description:
        for desc_tag in DESCRIPTION_TAGS:
            tag = soup.find(desc_tag["tag"], class_=desc_tag["class"])
            if tag:
                description = tag.get_text().strip()
                if description:
                    break
        else:
            description = "Description not found"

    # Extract price
    price = None
    for price_tag in PRICE_TAGS:
        tag = soup.find(price_tag["tag"], class_=price_tag["class"])
        if tag:
            price = tag.get_text().strip()
            if price:
                break
    else:
        price = "Price not found"

    if price != "Price not found":
        # Format price
        formatted_price = price.replace("€", "").replace(",", ".").strip()
        try:
            price_value = float(formatted_price)
            formatted_price = f"{price_value:.2f}€"
            price = formatted_price
        except ValueError:
            pass

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
    """
    Asynchronously fetch product details for a URL.

    :param session: The aiohttp client session.
    :param url: The URL to fetch.
    :param title: The title of the product.
    :param semaphore: Semaphore to limit concurrent requests.
    :return: A dictionary with 'url', 'title', and 'details' or None if out of stock.
    """
    async with semaphore:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/85.0.4183.83 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive'
            }
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)  # Total timeout of 5 seconds

            async with session.get(url, timeout=timeout, headers=headers) as response:
                if response.status != 200:
                    logging.error(f"Failed to fetch {url}, status code: {response.status}")
                    return None

                content = await response.text()

                # Parse the HTML content efficiently
                soup = BeautifulSoup(content, 'lxml')

                details = fetch_product_details_from_soup(soup)

                # If product is out of stock, save it in a separate file and skip
                if CHECK_STOCK and not details["in_stock"]:
                    logging.info(f"Product {url} is out of stock.")
                    with open('products_without_stock.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{title}\nURL: {url}\nPrice: {details['price']}\n\n")
                    return None  # Do not return product details if out of stock

                return {
                    "url": url,
                    "title": title,
                    "image": details["image"],
                    "description": details["description"],
                    "price": details["price"]
                }

        except Exception as e:
            logging.error(f"Error fetching details for {url}: {e}")
            return None

async def fetch_product_details(urls_titles, max_concurrent_requests=10):
    """
    Asynchronously fetch product details for a list of URLs.

    :param urls_titles: List of dictionaries with 'url' and 'title'.
    :param max_concurrent_requests: Maximum number of concurrent requests.
    :return: List of dictionaries with 'url', 'title', and 'details'.
    """
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent_requests)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for url_titles in urls_titles:
            tasks.append(fetch_details(session, url_titles["url"], url_titles["title"], semaphore))
        
        # Gather all tasks
        results = await asyncio.gather(*tasks)

        # Filter out any None results (products without price)
        valid_results = [result for result in results if result is not None]

        logging.info(f"Found {len(valid_results)} products with valid prices")

    return valid_results



if __name__ == "__main__":
    # Sample URL to test the function
    test_url = "https://www.example.com"

    # Asynchronous call to fetch the title of the test URL
    async def main():
        # Define logging level
        logging.basicConfig(level=logging.INFO)

        # Single URL title fetching
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(1)  # Only one request at a time
            title_result = await fetch_title(session, test_url, semaphore)
            print(f"Fetched title for {test_url}: {title_result}")

    # Run the asynchronous main function
    asyncio.run(main())