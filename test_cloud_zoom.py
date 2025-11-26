#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de imágenes cloud-zoom
"""
import logging
from bs4 import BeautifulSoup
import sys
import os

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fetcher import fetch_product_details_from_soup

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_cloud_zoom_extraction():
    """Prueba la extracción de imágenes usando el HTML de ejemplo"""

    # HTML de ejemplo proporcionado por el usuario
    html_content = '''
    <div id="wrap" style="top:0px;z-index:9999;position:relative;">
        <a href="https://www.tiendafetichista.com/media/catalog/product/cache/2/image/650x650/9df78eab33525d08d6e5fb8d27136e95/c/o/collares-bdsm-cuero-3-argollas.jpg" class="cloud-zoom product-image-gallery" id="zoom1" rel="position:'inside',showTitle:false,lensOpacity:0.5,smoothMove:3,zoomWidth:427,zoomHeight:275,adjustX:0,adjustY:0" style="position: relative; display: block;">
            <img id="image-main" class="gallery-image visible" src="https://www.tiendafetichista.com/media/catalog/product/cache/2/image/364x/040ec09b1e35df139433887a97daa66f/c/o/collares-bdsm-cuero-3-argollas.jpg" alt="Collar BDSM de cuero con las 3 argollas " title="Collar BDSM de cuero con las 3 argollas " itemprop="image" style="display: block;">
        </a>
        <div class="mousetrap" style="background-image: url(&quot;data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7&quot;); width: 364px; height: 364px; top: 0px; left: 0px; position: absolute; z-index: 9999;"></div>
    </div>
    '''

    # Crear objeto BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')

    # Llamar a la función de extracción
    details = fetch_product_details_from_soup(soup)

    print("=" * 80)
    print("RESULTADO DE LA EXTRACCIÓN:")
    print("=" * 80)
    print(f"Imagen extraída: {details['image']}")

    # Verificar si la extracción fue exitosa
    expected_url = "https://www.tiendafetichista.com/media/catalog/product/cache/2/image/650x650/9df78eab33525d08d6e5fb8d27136e95/c/o/collares-bdsm-cuero-3-argollas.jpg"

    if details['image'] == expected_url:
        print("✅ ¡ÉXITO! La imagen se extrajo correctamente.")
        return True
    else:
        print("❌ ERROR: La imagen no se extrajo correctamente.")
        print(f"Esperado: {expected_url}")
        print(f"Obtenido: {details['image']}")
        return False

if __name__ == "__main__":
    success = test_cloud_zoom_extraction()
    sys.exit(0 if success else 1)

