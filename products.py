# Librerías necesarias
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import html2text
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from colorama import Fore

load_dotenv()  # Cargar variables de entorno

##################################################################################################
#################################### Leer el txt #################################################
##################################################################################################

def read_products_links(file_path):
    with open(file_path, 'r') as file:
        products_links = [line.strip() for line in file]
    return products_links

##################################################################################################
###################### Extracción de Metadatos con Open Graph ####################################
##################################################################################################


def get_product_metadata(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al acceder a la URL: {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer metadatos Open Graph
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        og_description = soup.find("meta", property="og:description")

        title = og_title["content"] if og_title else "Título no disponible"
        image = og_image["content"] if og_image else "Imagen no disponible"
        description = og_description["content"] if og_description else "Descripción no disponible"
        
        # Posibles selectores para el precio
        price_selectors = [
            {"tag": "span", "class": "product-price"},
            {"tag": "span", "class": "price"},
            {"tag": "span", "class": "amount"},
            {"tag": "span", "class": "price-value"},
            {"tag": "span", "class": "price-current"},
            {"tag": "span", "class": "current-price"},
            {"tag": "span", "class": "actual-price"},
            {"tag": "span", "class": "sale-price"},
            {"tag": "div", "class": "price"},
            {"tag": "div", "class": "product-price"},
            {"tag": "div", "class": "price-value"}
        ]

        # Intentar encontrar el precio usando los posibles selectores
        price = None
        for selector in price_selectors:
            price_tag = soup.find(selector["tag"], class_=selector["class"])
            if price_tag:
                price = price_tag.text.strip()
                break

        if not price:
            price = "Precio no disponible"

        return {
            'title': title,
            'image': image,
            'description': description,
            'price': price,
            'url': url
        }
    except Exception as e:
        print(f"Error al procesar la URL {url}: {e}")
        return None



def extract_and_clean_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    metadata = {}
    try:
        # Fetch HTML content from the URL using requests
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad responses (4xx and 5xx)

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        metadata['url'] = url
        metadata['title'] = soup.title.string if soup.title else 'No title found'

        # Exclude elements with class names 'footer' and 'navbar'
        excluded_tagNames = ['footer', 'nav']
        for tag_name in excluded_tagNames:
            for unwanted_tag in soup.find_all(tag_name):
                unwanted_tag.extract()

        
        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        text_content = text_maker.handle(str(soup))
        
        # Clean the extracted text
        clean_text = clean_content(text_content)
        
        print("Content extracted and cleaned from:", url)
        return clean_text, metadata

    except requests.exceptions.RequestException as e:
        print(f"Error al hacer la solicitud a {url}: {e}")
        return None, {"error": f"Request error fetching data from {url}: {e}"}

def clean_content(content):
    # Cleaning patterns
    content = re.sub(r'!\[\]([^)]*\))', '', content)  # Elimina [](url)
    content = re.sub(r'\[.*\s.*\]([^)]*\))', '', content)  # Elimina [text](url)
    content = re.sub(r'\[\s*\]\([^)]*\)', '', content)  # Elimina [ ](url)
    content = re.sub(r'\[!\]\([^)]*\)', '', content)  # Elimina [!](url)
    content = re.sub(r'\[\s*!\[.*\s.*\]([^)]*\))\s*\]\([^)]*\)', '', content)  # Elimina [ ![text](url) ](url)
    content = re.sub(r"(\w)-\n(\w)", r"\1\2", content)  # Combina palabras separadas por guion
    content = re.sub(r"(?<!\n)\n(?!\n)", " ", content)  # Elimina saltos de línea simples
    content = re.sub(r'\n\s*\n', '\n', content)  # Elimina líneas en blanco
    content = re.sub(r'\s*!\s*$', '', content, flags=re.MULTILINE)  # Elimina '!' al final de líneas
    content = re.sub(r'\s+!', ' ', content)  # Elimina '!' solo con espacios alrededor
    content = re.sub(r'~', '', content)  # Elimina el símbolo ~
    content = re.sub(r'!\[.*\s.*\]([^)]*\))', '', content)  # Elimina ![text](url)
    content = re.sub(r'\[.*\s.*\]([^)]*\))', '', content)  # Elimina [text](url)
    content = re.sub(r'\[.*?\]\(.*?\)!\[.*?\]\(.*?\)', '', content)  # Elimina [text](url)![text](url)
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)  # Elimina [ ](url)
    return content

##################################################################################################
#################################### Respuesta IA ################################################
##################################################################################################

# Configuración del modelo LLM
llm_config = {
    "model_name": "gpt-4o-mini",
    "temperature": 0.2,
}

# Definir prompts
prompts = {
    "main_prompt": """

    Contexto: Durante la conversación entre un asistente virtual y un cliente, cuando se detecta una keyword en la respuesta del asistente, se envía un producto relevante relacionado con la conversación al cliente.

    Rol: Tu tarea es generer una lista de posibles keywords para enviar el producto, además de su precio. Para ello se te proporciona el título y el contenido de la página de ese producto.

    Especificaciones: Las keywords que generes deben ser muy específicas, concretas y únicas para ese producto.

    Información del producto:
    - Título: {title}
    - Contenido: {description}

    Respuesta: Precio del producto + lista de cuatro keywords separadas por comas. Ej: Precio€, Keyword1, Keyword2, Keyword3, Keyword4

    """
}

# Obtener modelo LLM
def get_llm():
    return ChatOpenAI(**llm_config)

# Generar respuesta
def get_product_keywords(title, description):
    llm = get_llm()

    # Formatear el prompt con el título y la descripción
    prompt_formatted = prompts["main_prompt"].format(title=title, description=description)

    # Crear el mensaje
    messages = [HumanMessage(content=prompt_formatted)]

    # Invocar el LLM con los mensajes
    response = llm.invoke(messages)

    return response.content.strip()

##################################################################################################
################################# Guardar Resultados en Excel #####################################
##################################################################################################

def save_to_excel(data, file_name):
    df = pd.DataFrame(data)
    df.to_excel(file_name, index=False)

##################################################################################################
##################################### Programa Principal #########################################
##################################################################################################

def main():
    product_links = read_products_links('products.txt')
    result_data = []

    for index, link in enumerate(product_links, start=1):
        print(f"Procesando producto {index}/{len(product_links)}: {link}")
        clean_text, metadata = extract_and_clean_html(link)
        
        if clean_text:
            keywords = get_product_keywords(metadata['title'], clean_text)
            
            result_data.append({
                'Link': metadata['url'],
                'Title': metadata['title'],
                'Cleaned Content': clean_text,
                'Keywords': keywords,
            })
            print(f"Generadas keywords para el producto: {metadata['title']}")
            print(f"Keywords: {keywords}")
        else:
            print(f"No se pudo obtener y procesar el contenido para el producto: {link}")
    
    save_to_excel(result_data, 'product_keywords.xlsx')
    print("Keywords, metadatos y contenido limpio guardados en product_keywords.xlsx")

if __name__ == '__main__':
    main()

