# Librerías necesarias
import ast
import asyncio
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import aiohttp  # Asegúrate de tener esta línea
import html2text
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import time
from colorama import Fore, Style


from urllib.parse import urljoin, urlparse

load_dotenv()  # Cargar variables de entorno

metadata = {
    "domain": "https://nude-project.com/es",
    "process_batch": 20,
    "timeout": 20,
    "metadata_batch": 3,
    "llm_select_batch": 20,
    "url_limit": 1000,
}

##################################################################################################
######################### Leer el txt ó scrapear todos los urls ##################################
##################################################################################################

def read_products_links(file_path):
    with open(file_path, 'r') as file:
        products_links = [line.strip() for line in file]
    return products_links

def get_all_urls(domain, max_urls=metadata["url_limit"]):
    print("Buscando urls...")
    visited = set()  # Conjunto para almacenar las URLs ya visitadas
    urls_to_visit = [domain]  # Lista de URLs pendientes de visitar
    all_urls = []  # Lista para almacenar todas las URLs encontradas

    # Mientras haya URLs por visitar y no se haya alcanzado el máximo de URLs
    while urls_to_visit and len(all_urls) < max_urls:
        current_url = urls_to_visit.pop(0)
        if current_url not in visited:
            visited.add(current_url)
            try:
                response = requests.get(current_url)
                if response.status_code == 200:
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Buscar todas las etiquetas <a> con enlaces
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        # Convertir los enlaces relativos en absolutos
                        full_url = urljoin(domain, href)
                        # Validar que la URL pertenece al mismo dominio
                        if is_same_domain(domain, full_url) and full_url not in visited:
                            urls_to_visit.append(full_url)
                            all_urls.append(full_url)
                            # print(f"Full url {full_url}")
                            if len(all_urls) >= max_urls:
                                break
            except Exception as e:
                print(f"get_all_urls: Error al acceder a {current_url}: {e}")

    return all_urls

# Verificar si una URL pertenece al mismo dominio
def is_same_domain(base_url, target_url):
    base_domain = urlparse(base_url).netloc
    target_domain = urlparse(target_url).netloc
    return base_domain == target_domain

def save_urls_to_txt(urls, file_name):
    with open(file_name, 'w') as file:
        for url in urls:
            file.write(url + '\n')


##################################################################################################
###################### Extracción de Metadatos con Open Graph ####################################
##################################################################################################

def get_product_metadata(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"get_product_metadata: Error al acceder a la URL: {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer metadatos Open Graph
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        og_description = soup.find("meta", property="og:description")

        # Verificar si los metadatos existen
        if not og_title or not og_image or not og_description:
            # print(f"get_product_metadata: No se encontraron metadatos Open Graph en la URL: {url}")
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
        print(f"get_product_metadata: Error al procesar la URL {url}: {e}")
        return None

def extract_and_clean_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
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
        
        # print("extract_and_clean_html: Content extracted and cleaned from:", url)
        return clean_text, metadata

    except requests.exceptions.RequestException as e:
        # print(f"extract_and_clean_html: Error al hacer la solicitud a {url}: {e}")
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



# Semáforo para limitar el número de peticiones simultáneas
sem = asyncio.Semaphore(metadata["process_batch"])  # Considera reducir el número de conexiones simultáneas

async def fetch(session, link):
    async with sem:  # Limita el número de peticiones concurrentes
        start_time = time.perf_counter()  # Iniciar el temporizador
        try:
            # print(f"Iniciando procesamiento del link: {link}")
            timeout = aiohttp.ClientTimeout(total=metadata["timeout"])  # Timeout total de 10 segundos
            async with session.get(link, timeout=timeout) as response:
                if response.status != 200:
                    # print(f"fetch: Error al acceder a la URL: {link}, Status: {response.status}")
                    return None

                content = await response.text()

                # Parsear solo el contenido necesario
                soup = BeautifulSoup(content, 'lxml')

                # Extraer metadatos Open Graph
                og_title = soup.find("meta", property="og:title")

                # Verificar si los metadatos existen
                if og_title and og_title.get("content"):
                    result = {
                        "link": link,
                        "title": og_title["content"]
                    }
                else:
                    # print(f"fetch: No se encontraron metadatos Open Graph en la URL: {link}")
                    result = None

        except asyncio.TimeoutError:
            # print(f"fetch: Timeout al acceder a la URL {link}")
            result = None
        except Exception as e:
            # print(f"fetch: Error al procesar la URL {link}: {e}")
            result = None

        end_time = time.perf_counter()  # Finalizar el temporizador
        elapsed_time = end_time - start_time
        # print(f"Finalizado procesamiento del link: {link}, Tiempo: {elapsed_time:.2f} segundos")
        return result

async def process_links_async(links):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in links:
            task = asyncio.ensure_future(fetch(session, link))
            tasks.append(task)

        # Ejecutar las tareas y esperar los resultados, capturando excepciones
        linksWithTitle = await asyncio.gather(*tasks, return_exceptions=True)

        # Manejar resultados y excepciones
        processed_links = []
        for result in linksWithTitle:
            if isinstance(result, Exception):
                print(f"Se capturó una excepción en una tarea: {result}")
            elif result is not None:
                processed_links.append(result)

        print(f"Total de links procesados: {len(processed_links)} de {len(links)}")
        

        # Borrar posibles elementos repetidos
        seen_titles = set()
        unique_links = []

        for item in processed_links:
            if item["title"] not in seen_titles:
                unique_links.append(item)
                seen_titles.add(item["title"])

        print(f"Total de links unicos: {len(unique_links)} de {len(processed_links)} procesados")

        return unique_links
        
def process_links(links):
    return asyncio.run(process_links_async(links))


#Función asincrona para extraer metadatos
async def extract_metadata_async(processed_links):
    async def process_single_product(link):
        # print(f"Procesando producto: {link}")

        # Obtener metadatos del producto y verificar que existan
        metadata = await asyncio.to_thread(get_product_metadata, link)
        if metadata is None:
            # print(f"No se encontraron metadatos para la URL: {link}. Se omite este enlace.")
            return None

        clean_text, content_metadata = await asyncio.to_thread(extract_and_clean_html, link)
        
        if clean_text:
            # Aquí puedes generar las keywords si lo deseas
            keywords = ""
            
            return {
                'url': metadata['url'],
                'name': metadata['name'],
                'description': metadata['description'],
                'image_url': metadata['image_url'],
                'price': metadata['price'],
                'keywords': keywords,
                'cleaned_content': clean_text,
            }
        else:
            # print(f"No se pudo obtener y procesar el contenido para el producto: {link}")
            return None

    result_data = []
    
    # Procesar en lotes de metadata["metadata_batch"] productos a la vez
    for i in range(0, len(processed_links), metadata["metadata_batch"]):
        batch_links = processed_links[i:i+metadata["metadata_batch"]]
        tasks = [process_single_product(link) for link in batch_links]
        results = await asyncio.gather(*tasks)

        # Filtrar resultados no válidos y agregar a result_data
        result_data.extend([r for r in results if r is not None])

    return result_data



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

    """,
    "product_selection_prompt": """
    A continuación, vas a recibir una lista de elementos en formato de lista de Python, donde cada elemento es un diccionario con las claves "link" y "title". Por ejemplo:

    [
        {"link": "https://ejemplo.com/producto123", "title": "Camiseta Blanca de Algodón - Talla M"},
        {"link": "https://ejemplo.com/categorias/camisetas", "title": "Camisetas"},
        {"link": "https://ejemplo.com/info/envios", "title": "Información de Envíos"},
        ...
    ]

    Tu tarea es la siguiente:

    - **Identificar** los títulos que corresponden a **páginas de productos individuales**.
    - **Ejemplos de títulos de productos**:
        - "Zapatos Deportivos Modelo X123"
        - "Vestido Rojo de Fiesta - Edición Limitada"
        - "Reloj Inteligente Serie 5"
    - Estos títulos suelen ser descriptivos y específicos, incluyendo detalles como color, modelo, talla o características únicas.
    - **No seleccionar** títulos que correspondan a:
    - **Categorías de productos**: Ejemplo: "Camisetas", "Pantalones", "Accesorios"
    - **Información general**: Ejemplo: "Contacto", "Política de Devolución", "Términos y Condiciones", "Buscar"
    - **Páginas de ayuda o soporte**: Ejemplo: "Preguntas Frecuentes", "Soporte al Cliente"

    **Instrucciones adicionales:**

    - **Salida**: Devuelve una lista en formato de lista de Python que contenga únicamente los enlaces ("link") de las páginas identificadas como productos.
    - **Formato estricto**: No añadas ninguna indicación extra, texto adicional ni comentarios antes o después de la lista.
    - **Ejemplo de salida**:

    ["https://ejemplo.com/producto123", "https://ejemplo.com/producto456"]

    Esta es la lista de elementos que debes procesar:
    """,


    "product_selection_prompt_deprecated": """
    A continuación vas a recibir una lista de elementos con este formato: 
    {"link":"", corresponde al link (url) de la página
     "title":"", corresponde al og:title de la página
    }
    El link y el title de cada uno de los elementos se corresponde con una de las páginas de una web e-commerce.
    Debes identificar los títulos que corresponden a páginas de productos y seleccionar sus links correspondientes. 
    Asegúrate de NO seleccionar páginas de categorías de productos o de información general. Por ejemplo si el e-commerce es de ropa no debes seleccionar las páginas: "CAMISETAS[...]", "PANTALONES[...]", "Buscar" ó "Políticas de devolución"... En general te debes asegurar que la página seleccionada es de un producto.
    Tu output debe ser una lista en formato de lista de python con los links de las páginas que has identificado que son productos. No añadas ninguna indicación extra o texto ni antes ni después de la lista de links.
    Esta es la lista de elementos:
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

async def select_product_links_async(links_with_title, i):
    llm = get_llm()
    max_attempts = 3
    attempt = 0
    llm_processed_links = None

    while attempt < max_attempts:

        attempt += 1
        try:
            # Preparar el prompt
            prompt = prompts["product_selection_prompt"] + "\n" + str(links_with_title)

            messages = [HumanMessage(content=prompt)]
            print(f"Ejecutando intento: {attempt} del intérvalo {i}")

            # Realizar la invocación de forma asincrónica
            response = await asyncio.to_thread(llm.invoke, messages)

            response_text = response.content.strip()

            # Intentar analizar response_text como una lista de Python
            try:
                llm_processed_links = ast.literal_eval(response_text)
                if isinstance(llm_processed_links, list):
                    # Se analizó correctamente una lista
                    break
                else:
                    print(f"Intento {attempt}: La respuesta del LLM no es una lista.")
            except Exception as e:
                print(f"Intento {attempt}: Error al analizar la respuesta del LLM como lista: {e}")
        except Exception as e:
            print(f"Intento {attempt}: Error durante la invocación al LLM: {e}")

    if llm_processed_links is None or not isinstance(llm_processed_links, list):
        print("Error: El LLM no devolvió una lista válida después de 3 intentos.")
        # Manejar el error según sea necesario, por ejemplo, devolver una lista vacía o lanzar una excepción
        return []
    else:
        return llm_processed_links
    
async def process_selected_links_async(unique_links):
    selected_links = []

    async def process_batch_with_delay(batch, delay):
        # Esperar el tiempo especificado antes de iniciar la tarea
        await asyncio.sleep(delay)
        # Ejecutar la llamada asincrónica
        return await select_product_links_async(batch, i)

    tasks = []
    # Procesar en bloques de  metadata["llm_select_batch"] links
    for i in range(0, len(unique_links), metadata["llm_select_batch"]):
        batch = unique_links[i:i +  metadata["llm_select_batch"]]  # Crear lotes de  metadata["llm_select_batch"] enlaces
        # print(f"Programando lote de links desde {i} hasta {i + len(batch)} con un retraso de {i // metadata["llm_select_batch"] * 0.5} segundos")

        # Crear una tarea para cada batch con un retardo incremental de 0.5s por cada lote
        task = asyncio.create_task(process_batch_with_delay(batch, i //  metadata["llm_select_batch"] * 0.5))
        tasks.append(task)

    # Ejecutar todas las tareas en paralelo
    result_batches = await asyncio.gather(*tasks)

    # Acumular los resultados
    for result_batch in result_batches:
        selected_links.extend(result_batch)

    return selected_links





##################################################################################################
################################# Guardar Resultados en Excel #####################################
##################################################################################################
def save_to_excel(data, file_name):
    df = pd.DataFrame(data)
    
    # Asegurarse de que todas las columnas esperadas existen
    columns_to_select = ['name', 'url', 'description', 'image_url', 'keywords', 'price', 'cleaned_content']
    available_columns = [col for col in columns_to_select if col in df.columns]
    
    if available_columns:
        df = df[available_columns]  # Reorganizar las columnas según las disponibles
    else:
        print("No se encontraron las columnas esperadas en los datos.")
        print("Datos recibidos en 'data':")
        print(data)  # Imprimir el contenido completo de 'data'
        print("\nEstructura de 'data':")
        for index, item in enumerate(data):
            print(f"\nItem {index + 1}:")
            if isinstance(item, dict):
                for key, value in item.items():
                    print(f"  - {key}: {type(value)}")
            else:
                print(f"  - {item}: {type(item)}")
    
    df.to_excel(file_name, index=False)


##################################################################################################
##################################### Programa Principal #########################################
##################################################################################################


def main():
    domain = metadata["domain"]
    
    # Temporizar el proceso de get_all_urls
    print(Fore.YELLOW + Style.BRIGHT + "Iniciando proceso de obtención de URLs..." + Style.RESET_ALL)
    start_time = time.time()
    product_links = get_all_urls(domain, max_urls=metadata["url_limit"])
    print("Urls totales: ")
    print(len(product_links))
    product_links = list(set(product_links))
    end_time = time.time()
    print("Urls unicos: ")
    print(len(product_links))
    print(Fore.YELLOW + Style.BRIGHT + f"Proceso de obtención de URLs finalizado en {end_time - start_time:.2f} segundos." + Style.RESET_ALL)
    
    # Guardar URLs en archivo
    save_urls_to_txt(product_links, 'urls_encontrados.txt')

    # Temporizar el proceso de process_links
    print(Fore.GREEN + Style.BRIGHT + "Iniciando proceso de procesamiento de links..." + Style.RESET_ALL)
    start_time = time.time()
    processed_links = process_links(product_links)
    end_time = time.time()
    print(Fore.GREEN + Style.BRIGHT + f"Proceso de procesamiento de links finalizado en {end_time - start_time:.2f} segundos." + Style.RESET_ALL)

   
    #Temporizar el proceso de selección de links con LLM
    print(Fore.BLUE + Style.BRIGHT + "Iniciando proceso selección de productos..." + Style.RESET_ALL)
    start_time = time.time()

    # Ejecutar la nueva función asíncrona para obtener selected_links
    selected_links = asyncio.run(process_selected_links_async(processed_links))

    end_time = time.time()
    print(Fore.BLUE + Style.BRIGHT + f"Proceso de selección de productos finalizado en {end_time - start_time:.2f} segundos." + Style.RESET_ALL)
    print(f"Total de links seleccionados: {len(selected_links)} de {len(processed_links)} procesados")


    # Temporizar el bucle de procesamiento de productos (ahora asincrónico)
    print(Fore.CYAN + Style.BRIGHT + "Iniciando extracción metadatos de productos..." + Style.RESET_ALL)
    start_time = time.time()

    # Ejecutar la nueva función asíncrona
    result_data = asyncio.run(extract_metadata_async(selected_links))

    end_time = time.time()
    print(Fore.CYAN + Style.BRIGHT + f"Procesamiento extracción metadatos finalizado en {end_time - start_time:.2f} segundos." + Style.RESET_ALL)

    # Eliminar productos duplicados basados en el título
    unique_data = []
    seen_titles = set()
    for item in result_data:
        if item['name'] not in seen_titles:
            unique_data.append(item)
            seen_titles.add(item['name'])

    # Guardar resultados en Excel
    save_to_excel(unique_data, 'product_keywords.xlsx')
    print(Fore.MAGENTA + Style.BRIGHT + "Datos guardados en product_keywords.xlsx" + Style.RESET_ALL)



if __name__ == '__main__':
    main()
