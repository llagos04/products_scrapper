import asyncio
import logging
from src.fetcher import fetch_product_details
from colorama import init, Fore, Style
from CONFIG import ROOT_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
init()

async def test_fetcher():
    print(f"{Fore.CYAN}Testing new fetcher logic with a URL from {ROOT_URL}...{Style.RESET_ALL}")
    
    # Use a known URL or just the root if it's a shop page, but ideally a product page
    test_urls = [ROOT_URL] 
    
    print(f"Fetching details for: {test_urls}")
    
    products, discarded = await fetch_product_details(test_urls, max_concurrent_requests=1)
    
    print(f"\n{Fore.GREEN}Products found: {len(products)}{Style.RESET_ALL}")
    for p in products:
        print(f"  - Title: {p['title']}")
        print(f"  - Price: {p['price']}")
        print(f"  - Image: {p['image']}")
        print(f"  - Description length: {len(p['description'])}")
        
    print(f"\n{Fore.YELLOW}Discarded: {len(discarded)}{Style.RESET_ALL}")
    for d in discarded:
        print(f"  - URL: {d['url']}")
        print(f"  - Error: {d.get('error', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_fetcher())
