import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import ast
from CONFIG import LLM_MODEL, LLM_TEMPERATURE, PRODUCTS_SOLD, CATEGORIES_EXAMPLES, PRODUCT_EXAMPLES
import logging

# Generate product examples string
product_examples_str = ""
if len(PRODUCT_EXAMPLES) > 0:
    product_examples_str += "    - **Ejemplos de títulos de productos**:\n"
    product_examples_str += ''.join(f"       - {example}\n" for example in PRODUCT_EXAMPLES)

# Generate categories examples string
categories_examples_str = "    - **Categorias de productos**."
if len(CATEGORIES_EXAMPLES) > 0:
    categories_examples_str += "**Ejemplos de categorías de productos**:\n"
    categories_examples_str += ''.join(f"       - {example}\n" for example in CATEGORIES_EXAMPLES)

product_selection_prompt = f"""
A continuación, vas a recibir una lista de elementos en formato de lista de Python, donde cada elemento es un diccionario con las claves "link" y "title". Por ejemplo:

[
    {{"link": "https://ejemplo.com/producto123", "title": "{PRODUCT_EXAMPLES[0] if len(PRODUCT_EXAMPLES) > 0 else 'Producto 123'}"}},
    {{"link": "https://ejemplo.com/producto156", "title": "{PRODUCT_EXAMPLES[1] if len(PRODUCT_EXAMPLES) > 1 else 'Producto 156'}"}},
    {{"link": "https://ejemplo.com/info/envios", "title": "Información de Envíos"}},
    ...
]

Tu tarea es la siguiente:

- **Identificar** los títulos que corresponden a **páginas de productos individuales** en el contexto de una tienda online que vende {PRODUCTS_SOLD}
{product_examples_str}
- Los títulos suelen ser descriptivos y específicos, incluyendo detalles como color, modelo, talla o características únicas.
- **No seleccionar** títulos que correspondan a:
{categories_examples_str}
    - **Información general**: Ejemplo: "Contacto", "Política de Devolución", "Términos y Condiciones", "Buscar"
    - **Páginas de ayuda o soporte**: Ejemplo: "Preguntas Frecuentes", "Soporte al Cliente"

**Instrucciones adicionales:**

- **Salida**: Devuelve una lista en formato de lista de Python que contenga únicamente los enlaces ("link") de las páginas identificadas como productos.
- **Formato estricto**: No añadas ninguna indicación extra, texto adicional ni comentarios antes o después de la lista.
- **Ejemplo de salida**:

["https://ejemplo.com/producto123", "https://ejemplo.com/producto156"]

Esta es la lista de elementos que debes procesar:
"""

def get_llm():
    return ChatOpenAI(
        model_name=LLM_MODEL,
        temperature=LLM_TEMPERATURE
    )

async def process_batch(llm, batch):
    max_attempts = 3
    attempt = 0
    llm_processed_links = None

    while attempt < max_attempts:
        attempt += 1
        try:
            # Prepare the prompt
            prompt = f"{product_selection_prompt}\n\n{str(batch)}"

            messages = [HumanMessage(content=prompt)]
            # print(f"Attempt: {attempt}")
            # print(f"Prompt: {prompt}")

            # Use the asynchronous method directly
            response = await llm.ainvoke(messages)

            response_text = response.content.strip()
            # print(f"Response: {response_text}")

            # Try to parse response_text as a Python list
            try:
                llm_processed_links = ast.literal_eval(response_text)
                if isinstance(llm_processed_links, list):
                    # Parsed a list correctly
                    break
                else:
                    print(f"Attempt {attempt}: The LLM response is not a list.")
            except Exception as e:
                print(f"Attempt {attempt}: Error parsing the LLM response as list: {e}")
        except Exception as e:
            print(f"Attempt {attempt}: Error during LLM invocation: {e}")

    if llm_processed_links is None or not isinstance(llm_processed_links, list):
        print("Error: The LLM did not return a valid list after 3 attempts.")
        # Handle the error as needed, e.g., return an empty list or raise an exception
        return []
    else:
        return llm_processed_links

async def select_product_urls(urls_titles, llm_batch_size, max_concurrent_requests=5):
    product_urls = []

    # Create a single LLM instance
    llm = get_llm()

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def process_batch_semaphore(batch):
        async with semaphore:
            return await process_batch(llm, batch)

    # Create tasks for all batches
    tasks = []
    for i in range(0, len(urls_titles), llm_batch_size):
        batch = urls_titles[i:i + llm_batch_size]
        logging.debug(f"Processing batch {i // llm_batch_size + 1}")
        task = asyncio.create_task(process_batch_semaphore(batch))
        tasks.append(task)

    # Execute tasks concurrently with concurrency limit
    result_batches = await asyncio.gather(*tasks)

    # Accumulate the results
    for result_batch in result_batches:
        product_urls.extend(result_batch)

    # get the titles back for each url
    product_urls_titles = []
    for url_titles in urls_titles:
        url = url_titles['url']
        title = url_titles['title']
        if url in product_urls:
            product_urls_titles.append({'url': url, 'title': title})

    return product_urls_titles