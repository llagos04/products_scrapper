#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras de rate limiting
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CONFIG import ROOT_URL, CONCURRENT_REQUESTS
from src.fetcher import fetch_titles
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_rate_limiting():
    """
    Prueba el rate limiting con unas pocas URLs del sitio actual
    """
    print(f"Probando rate limiting con {ROOT_URL}")
    print("=" * 50)

    # Crear algunas URLs de prueba basadas en el sitio actual
    test_urls = [
        f"{ROOT_URL}",
        f"{ROOT_URL}productos/",  # URL común para productos
        f"{ROOT_URL}categoria/",  # URL común para categorías
    ]

    print(f"Haciendo {len(test_urls)} peticiones de prueba con concurrencia = {CONCURRENT_REQUESTS}")
    print("Monitorea los logs para ver los delays de rate limiting...")
    print()

    try:
        # Hacer las peticiones
        results = await fetch_titles(test_urls, max_concurrent_requests=CONCURRENT_REQUESTS)

        print("\nResultados:")
        print("-" * 30)
        for result in results:
            status = "OK" if "not found" not in result['title'].lower() else "Not Found"
            print(f"URL: {result['url']}")
            print(f"Title: {result['title'][:50]}...")
            print(f"Status: {status}")
            print()

        print("Prueba completada exitosamente!")
        print("Revisa los logs para confirmar que el rate limiting está funcionando.")

    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rate_limiting())
