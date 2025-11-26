#!/usr/bin/env python3
"""
Script de prueba para verificar que el crawler usa correctamente el rate limiting
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CONFIG import ROOT_URL
from src.crawler import Crawler
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_crawler_rate_limiting():
    """
    Prueba que el crawler aplique correctamente el rate limiting
    """
    print(f"Probando rate limiting en crawler para: {ROOT_URL}")
    print("=" * 50)

    try:
        # Crear instancia del crawler
        crawler = Crawler(ROOT_URL, True, [])

        # Probar la función de robots.txt (que debería usar rate limiting)
        print("Probando obtención de robots.txt...")
        sitemap_url = await crawler.get_sitemap_from_robots_txt()
        print(f"Resultado: {sitemap_url}")

        # Si hay sitemap, probar obtener su contenido
        if sitemap_url:
            print(f"Probando obtención de contenido del sitemap: {sitemap_url}")
            content = await crawler.fetch_sitemap_content(sitemap_url)
            if content:
                print(f"Contenido obtenido exitosamente ({len(content)} caracteres)")
            else:
                print("No se pudo obtener el contenido del sitemap")

        print("\nPrueba completada!")
        print("Revisa los logs para confirmar que el rate limiting está funcionando en todas las peticiones.")

    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crawler_rate_limiting())

