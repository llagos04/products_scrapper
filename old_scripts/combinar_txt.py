import os

# Definir las rutas de los archivos
current_directory = os.path.dirname(os.path.abspath(__file__))  # Obtener el directorio donde está el script
file1_path = os.path.join(current_directory, 'product_info.txt')
file2_path = os.path.join(current_directory, 'product_info2.txt')

# Función para leer los productos de un archivo txt y almacenarlos en un diccionario
def leer_productos(archivo):
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read().strip()
        
    productos = contenido.split('-------\n')
    productos_dict = {}
    
    for producto in productos:
        if producto.strip():
            lineas = producto.strip().split('\n')
            nombre_producto = lineas[0]  # La primera línea es el nombre del producto
            productos_dict[nombre_producto] = producto  # Guardar el producto entero bajo el nombre como clave
    
    return productos_dict

# Leer los productos de ambos archivos txt
productos_1 = leer_productos(file1_path)
productos_2 = leer_productos(file2_path)

# Unir los productos, eliminando duplicados (basado en el nombre del producto)
productos_unidos = {**productos_1, **productos_2}

# Guardar el resultado en un nuevo archivo txt
output_file_path = os.path.join(current_directory, 'productos_combinados.txt')

with open(output_file_path, 'w', encoding='utf-8') as f:
    for producto in productos_unidos.values():
        f.write(producto + '\n-------\n')

print(f"Archivo combinado guardado como {output_file_path}")
