#!/usr/bin/env python3
"""
Script para probar la nueva lógica de extracción de imágenes de viajeteca.net
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fetcher import fetch_product_details_from_soup
from CONFIG import CUSTOM_IMAGE_PATTERN
from bs4 import BeautifulSoup
import aiohttp

async def test_improved_image_extraction():
    """
    Prueba la nueva lógica de extracción de imágenes usando la función actualizada
    """
    # URL de ejemplo que contiene la imagen mencionada por el usuario
    test_url = "https://www.viajeteca.net/viajes-fin-de-curso/viaje-fin-de-curso-madrid-primaria"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'lxml')

                    print("=" * 80)
                    print("PRUEBA DE LA LÓGICA CONFIGURABLE DE EXTRACCIÓN DE IMÁGENES")
                    print("=" * 80)
                    print(f"Patrón configurado: CUSTOM_IMAGE_PATTERN = '{CUSTOM_IMAGE_PATTERN}'")
                    print("=" * 80)

                    # Mostrar ejemplos de otros patrones posibles
                    print("\n💡 EJEMPLOS DE PATRONES QUE PUEDES CONFIGURAR:")
                    print("   'example.com/images/'     - Para imágenes en carpeta /images/")
                    print("   'shop.com/products/'      - Para imágenes en carpeta /products/")
                    print("   'store.net/uploads/'      - Para imágenes en carpeta /uploads/")
                    print("   '.jpg'                     - Para cualquier imagen JPG")
                    print("   '/media/catalog/'          - Para tiendas Magento")
                    print("=" * 80)

                    # Usar la función mejorada para extraer detalles del producto
                    product_details = fetch_product_details_from_soup(soup)

                    print(f"\nImagen extraída: {product_details['image']}")

                    if product_details['image'] != "Image not found":
                        print("✅ ¡Éxito! Se encontró una imagen de producto")
                        print(f"URL de la imagen: {product_details['image']}")

                        # Verificar si es la imagen específica que mencionó el usuario
                        if "7607_P601_5758p296viajefindecursoamadrid.png" in product_details['image']:
                            print("🎯 ¡Perfecto! Se extrajo exactamente la imagen solicitada por el usuario")
                        elif "viajeteca.net/fotos/" in product_details['image']:
                            print("✅ Se extrajo una imagen del patrón correcto (/fotos/)")
                        else:
                            print("⚠️  Se extrajo una imagen pero no del patrón esperado")
                    else:
                        print("❌ No se pudo extraer ninguna imagen")

                    print(f"\nDescripción extraída: {product_details['description'][:200]}...")
                    print(f"Precio extraído: {product_details['price']}")
                    print(f"Stock disponible: {product_details['in_stock']}")

                else:
                    print(f"Error: No se pudo acceder a la URL. Status code: {response.status}")

    except Exception as e:
        print(f"Error durante la prueba: {e}")

if __name__ == "__main__":
    asyncio.run(test_improved_image_extraction())