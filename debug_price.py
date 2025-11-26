#!/usr/bin/env python3
"""
Script simple para debuggear la extracción de precios
"""

import re
import html
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def extract_prices(text):
    """
    Extrae todos los precios del texto, devolviendo una lista de precios numéricos.
    Detecta tanto precios con '€' delante como detrás del número.
    """
    # Limpiar el texto de entidades HTML y caracteres especiales
    text = html.unescape(text)  # Convertir &nbsp; a espacios, etc.

    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'\s+', ' ', text).strip()

    logging.info(f"Texto después de limpieza: '{text}' (repr: {repr(text)})")

    # Expresión regular mejorada para detectar precios con formato europeo
    # Detecta precios con '€' delante o detrás del número
    prices = re.findall(r'€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)(?:\s*€)?', text)

    logging.info(f"Precios encontrados por regex: {prices}")

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

def test_price_extraction():
    """Prueba la extracción de precios con el HTML específico del usuario"""

    # HTML del usuario
    html_content = '''
    <span class="woocommerce-Price-amount amount"><bdi>17,90&nbsp;<span class="woocommerce-Price-currencySymbol">€</span></bdi></span>
    '''

    print("HTML original:")
    print(repr(html_content))

    # Simular lo que hace BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')

    # Buscar el elemento con el selector configurado
    price_element = soup.find("span", class_="woocommerce-Price-amount amount")

    if not price_element:
        print("❌ No se encontró el elemento con el selector correcto")
        return

    print("✅ Elemento encontrado:", price_element)

    # Buscar <bdi> (como hace el código actual)
    price_bdi = price_element.find("bdi")
    if price_bdi:
        print(f"✅ Encontrado <bdi>: {price_bdi}")
        price_text = price_bdi.get_text(strip=True)
        print(f"📝 Texto extraído del <bdi>: '{price_text}' (repr: {repr(price_text)})")
    else:
        print("❌ No se encontró <bdi>")
        price_text = price_element.get_text(strip=True)
        print(f"📝 Texto extraído del elemento: '{price_text}' (repr: {repr(price_text)})")

    # Extraer precios
    prices = extract_prices(price_text)
    print(f"📝 Precios extraídos: {prices}")

    if prices:
        print(f"✅ Precio encontrado: {prices[0]}")
    else:
        print("❌ No se pudieron extraer precios")

def test_regex_directly():
    """Prueba diferentes textos con la regex"""
    test_texts = [
        "17,90&nbsp;€",
        "17,90 €",
        "17,90€",
        "€17,90",
        "17.90€",
        "17,90"
    ]

    print("\n" + "="*50)
    print("PRUEBA DIRECTA DE REGEX")
    print("="*50)

    for text in test_texts:
        print(f"\nTexto original: '{text}' (repr: {repr(text)})")
        # Limpiar como hace la función
        cleaned = html.unescape(text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        print(f"Texto limpiado: '{cleaned}' (repr: {repr(cleaned)})")

        prices = re.findall(r'€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)(?:\s*€)?', cleaned)
        print(f"Precios encontrados: {prices}")

if __name__ == "__main__":
    print("DEBUG DE EXTRACCIÓN DE PRECIOS")
    print("="*50)
    test_price_extraction()
    test_regex_directly()

