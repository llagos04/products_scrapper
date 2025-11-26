#!/usr/bin/env python3
"""
Script de prueba para verificar que el fix del sitemap funcione correctamente.
"""
import asyncio
import logging
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crawler import Crawler

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_sitemap_fix():
    """Prueba el fetching del sitemap de growindustry.es"""
    domain = "https://www.growindustry.es"
    crawler = Crawler(domain, is_javascript_driven=True, ignore_links=[])

    print(f"Probando fetching del sitemap para: {domain}")
    print("=" * 60)

    try:
        # Obtener todos los sitemaps y URLs
        all_sitemaps = await crawler.get_all_urls()

        print(f"\nResultado: Se encontraron {len(all_sitemaps)} sitemaps")
        print("-" * 40)

        for i, sitemap_data in enumerate(all_sitemaps, 1):
            sitemap_url = sitemap_data['sitemap']
            urls = sitemap_data['urls']
            print(f"\nSitemap {i}: {sitemap_url}")
            print(f"URLs encontradas: {len(urls)}")

            # Mostrar primeras 5 URLs como ejemplo
            if urls:
                print("Primeras URLs:")
                for j, url in enumerate(urls[:5], 1):
                    print(f"  {j}. {url}")
                if len(urls) > 5:
                    print(f"  ... y {len(urls) - 5} más")

        print("\n" + "=" * 60)
        print("Prueba completada exitosamente!")

    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sitemap_fix())
