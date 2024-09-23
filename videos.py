# Librerías necesarias
import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from colorama import Fore

load_dotenv()  # Cargar variables de entorno

##################################################################################################
#################################### Leer el txt #################################################
##################################################################################################

def read_video_links(file_path):
    with open(file_path, 'r') as file:
        video_links = [line.strip() for line in file]
    return video_links

##################################################################################################
###################### Extracción de Metadatos con la API de YouTube #############################
##################################################################################################

def get_video_metadata(video_id):
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YouTube API key not found in environment variables.")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    try:
        request = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            print(f"No metadata found for video ID: {video_id}")
            return None

        video_info = response['items'][0]['snippet']
        statistics = response['items'][0]['statistics']

        return {
            'title': video_info['title'],
            'description': video_info['description'],
            'publishedAt': video_info['publishedAt'],
            'channelTitle': video_info['channelTitle'],
            'viewCount': statistics.get('viewCount', 'N/A'),
            'likeCount': statistics.get('likeCount', 'N/A'),
            'commentCount': statistics.get('commentCount', 'N/A')
        }
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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

    Contexto: Durante la conversación entre un asistente virtual y un cliente, cuando se detecta una keyword en la respuesta del asistente, se envía un video relevante que ayude al cliente.

    Rol: Tu tarea es generer una lista de posibles keywords para enviar el vídeo. Para ello se te proporciona el título y la descricpión de dicho vídeo.

    Especificaciones: Las keywords que generes deben ser muy específicas, concretas y únicas para ese vídeo.

    Keywords que no puedes generar: Kit Camper, Kit Mueble, Kit Mueblre Camper, Camperizar, Camperización.

    Ejemplos de keywords que debes generar en función del vídeo:
    - Título del vídeo: "Citroën Jumpy Camper, Peugeot Expert Camper, Opel Vivaro Camper, Toyota Proace Camper". Keywords: Jumpy, Expert, Vivaro, Proace.
    - Título del vídeo: "Bateria Camper - Bateria Auxiliar Furgoneta Camper - Instalación 2a Bateria Camper Sin Homologación". Keywords: Batería.
    - Título del vídeo: "Kit Mueble Camper VW Touran - Camperizar VW Touran - Camperización VW Touran". Keywords: Touran.

    Información del vídeo:
    - Título: {title}
    - Descripción: {description}

    Respuesta: Lista de una a cuatro keywords separadas por comas. Contra menos keywords contenga la lista, mejor para el sistema.

    """
}

# Obtener modelo LLM
def get_llm():
    return ChatOpenAI(**llm_config)

# Generar respuesta
def get_response(title, description):
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
    video_links = read_video_links('videos.txt')
    result_data = []

    for index, link in enumerate(video_links, start=1):
        print(f"Procesando video {index}/{len(video_links)}: {link}")
        video_id = link.split('v=')[-1]
        metadata = get_video_metadata(video_id)
        
        if metadata:
            keywords = get_response(metadata['title'], metadata['description'])
            
            # Crear el enlace del iframe
            iframe_link = f"https://www.youtube.com/embed/{video_id}"
            
            result_data.append({
                'Link': link,
                'Iframe Link': iframe_link,
                'Title': metadata['title'],
                'Keywords': keywords,
            })
            print(f"Generadas keywords para el video: {metadata['title']}")
            print(f"Keywords: {keywords}")
            print(f"Iframe Link: {iframe_link}")
        else:
            print(f"No se pudo obtener metadatos para el video: {link}")
    
    save_to_excel(result_data, 'video_keywords.xlsx')
    print("Keywords, metadatos y enlaces de iframe guardados en video_keywords.xlsx")

if __name__ == '__main__':
    main()





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

        # Verificar si los metadatos existen
        if not og_title or not og_image or not og_description:
            print(f"No se encontraron metadatos Open Graph en la URL: {url}")
            return None

        title = og_title["content"].strip()
        image = og_image["content"].strip()
        description = og_description["content"].strip()
        
        # Posibles selectores para el precio
        price_selectors = [
            {"tag": "span", "class": "product-price"},
            {"tag": "span", "class": "price"},
            {"tag": "span", "class": "Price"},
            {"tag": "span", "class": "ProductMeta__Price"},
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
            'name': title,
            'image_url': image,
            'description': description,
            'price': price,
            'url': url
        }
    except Exception as e:
        print(f"Error al procesar la URL {url}: {e}")
        return None    