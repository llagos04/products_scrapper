#!/usr/bin/env python3
"""
Test rápido del fix del sitemap
"""
import sys
import os
import asyncio

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crawler import Crawler

async def quick_test():
    print("Probando fix del sitemap para growindustry.es...")
    try:
        crawler = Crawler('https://www.growindustry.es', True, [])
        result = await crawler.get_all_urls()
        print(f"Éxito! Se encontraron {len(result)} sitemaps")
        for i, sitemap_data in enumerate(result[:3], 1):  # Mostrar primeros 3
            print(f"Sitemap {i}: {sitemap_data['sitemap']} - {len(sitemap_data['urls'])} URLs")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())

