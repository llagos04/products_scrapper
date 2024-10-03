# price es un conjunto, así que extraemos el valor
price_set = {"7,95€ El precio original era: 7,95€.5,50€El precio actual es: 5,50€."}  # Este es el conjunto inicial
price = next(iter(price_set))  # Extraemos el único valor dentro del conjunto

# Si se encuentra un precio, formatearlo correctamente
if price and price != "Precio no disponible":
    try:
        # Caso específico para el formato con "precio original" y "precio actual"
        if "El precio actual es:" in price:
            # Extraer el último precio del string
            price_actual = price.split("El precio actual es:")[-1].strip()

            # Eliminar el símbolo de € y cualquier espacio antes de convertir a float
            price_clean = price_actual.replace('€', '').strip()

            # Reemplazar la coma por un punto para convertir correctamente en float
            price_clean = price_clean.replace(',', '.')

            # Intentar convertir el precio a un número flotante
            price_float = float(price_clean)

            # Formatear el precio con dos decimales y agregar el símbolo €
            price = f"{price_float:,.2f}€".replace('.', ',')  # Formatear el precio
        else:
            # Si no se encuentra el patrón específico, procesar como antes
            # Eliminar el símbolo de € y cualquier espacio antes de convertir a float
            price_clean = price.replace('€', '').strip()

            # Reemplazar la coma por un punto para convertir correctamente en float
            price_clean = price_clean.replace(',', '.')

            # Intentar convertir el precio a un número flotante
            price_float = float(price_clean)

            # Formatear el precio con dos decimales y agregar el símbolo €
            price = f"{price_float:,.2f}€".replace('.', ',')  # Formatear el precio
    except ValueError:
        # Si falla la conversión, se deja el precio como está
        pass

print(price)
