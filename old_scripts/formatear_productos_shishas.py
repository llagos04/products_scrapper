import pandas as pd
import re

# Cargar el archivo Excel
# Asegúrate de cambiar "nombre_del_archivo.xlsx" por el nombre real del archivo
df = pd.read_excel('excel_miarcade.xlsx')

# Función para formatear la columna 'price'
def format_price(price):
    # Caso 1: Si el precio ya está en el formato correcto
    if re.match(r'^\d+,\d{2}€$', price.strip()):
        return price.strip()

    # Caso 2: Si el precio contiene un texto con el precio anterior y actual
    # Se busca el último precio en la cadena
    match = re.findall(r'(\d+,\d{2}€)', price)
    if match:
        return match[-1]  # Tomamos el último precio

    # Si no hay coincidencia, devolver el valor original
    return price

# Aplicar la función a la columna 'price'
df['price'] = df['price'].apply(format_price)

# Guardar el resultado en un nuevo archivo Excel
df.to_excel('excel_miarcade_formateado.xlsx', index=False)

print("El archivo ha sido formateado y guardado como 'excel_worldshishas_formateado.xlsx'.")
