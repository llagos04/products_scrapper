import pandas as pd
import os

# Definir las rutas de los archivos
current_directory = os.path.dirname(os.path.abspath(__file__))  # Obtener el directorio donde está el script
file1_path = os.path.join(current_directory, 'product_keywords.xlsx')
file2_path = os.path.join(current_directory, 'product_keywords2.xlsx')

# Leer los dos archivos Excel
df1 = pd.read_excel(file1_path)
df2 = pd.read_excel(file2_path)

# Combinar los dos dataframes y eliminar duplicados basados en la columna 'name'
combined_df = pd.concat([df1, df2]).drop_duplicates(subset=['name']).reset_index(drop=True)

# Guardar el resultado en un nuevo archivo Excel
output_file_path = os.path.join(current_directory, 'productos_combinados.xlsx')
combined_df.to_excel(output_file_path, index=False)

print(f"Archivo combinado guardado como {output_file_path}")
