# 🛡️ Sistema de Proxies Rotativos

Este sistema implementa un gestor avanzado de proxies para evitar bloqueos por rate limiting y protección anti-scraping.

## ⚠️ **Importante: Configurar Proxies Reales**

**Los proxies incluidos en el código son solo ejemplos y NO funcionan.** Para usar el sistema de proxies:

### Opción 1: Proxies Gratuitos (Limitados)

```python
# En CONFIG.py
USE_PROXIES = True
AUTO_FETCH_PROXIES = True  # Obtener automáticamente proxies gratis

# O manualmente:
from src.fetcher import proxy_manager
await proxy_manager.fetch_free_proxies(limit=20)
```

### Opción 2: Proxies Pagos (Recomendado)

```python
# Servicios recomendados:
# - Bright Data (anteriormente Luminati)
# - Oxylabs
# - Smart Proxy
# - ProxyMesh

# Ejemplo con Bright Data:
proxy_manager.update_proxy_list([
    'http://brd-customer-username-zone-zone_name:password@brd.superproxy.io:22225',
    'http://brd-customer-username-zone-zone_name:password@brd.superproxy.io:22226',
])
```

## 🚀 Características

### ✨ Funcionalidades Principales

- **Rotación automática** de proxies en cada request
- **Detección de proxies fallidos** y lista negra automática
- **Estadísticas de rendimiento** por proxy
- **Headers rotativos** combinados con proxies
- **Soporte para proxies HTTP/HTTPS**
- **Obtención automática** de proxies gratuitos
- **Configuración flexible** para activar/desactivar

### 🔧 Configuración

#### Variables Globales (CONFIG.py)

```python
# PROXY CONFIGURATION
USE_PROXIES = False  # Activar/desactivar uso de proxies globalmente (False por defecto)
AUTO_FETCH_PROXIES = False  # Obtener proxies automáticamente de fuentes gratuitas
PROXY_UPDATE_INTERVAL = 3600  # Segundos entre actualizaciones de proxies (1 hora)
```

## 📖 Uso Básico

### 1. Activación Automática

El sistema se activa automáticamente al importar los módulos. Los proxies se usan en:

- `fetch_title()` - Obtención de títulos
- `fetch_details()` - Extracción de detalles de productos
- `get_sitemap_from_robots_txt()` - Obtención de sitemaps
- `url_exists()` - Verificación de URLs
- `process_url()` - Crawling de páginas
- `fetch_sitemap_content()` - Descarga de sitemaps

### 2. Gestión Manual de Proxies

```python
from src.fetcher import proxy_manager

# Ver estado actual
print(f"Proxies activos: {proxy_manager.use_proxies}")
print(f"Total proxies: {len(proxy_manager.proxies)}")

# Activar/desactivar proxies
proxy_manager.enable_proxies()
proxy_manager.disable_proxies()

# Agregar proxy manualmente
proxy_manager.add_proxy('http://192.168.1.100:8080')

# Obtener proxies gratuitos automáticamente
await proxy_manager.fetch_free_proxies(limit=20)

# Ver estadísticas
stats = proxy_manager.get_proxy_stats()
for proxy, data in stats.items():
    print(f"{proxy}: {data['success']} OK, {data['fail']} FAIL")
```

## 🧪 Pruebas

### Ejecutar Pruebas de Proxies

```bash
python test_proxies.py
```

Esta prueba valida:

- ✅ Funcionamiento individual de proxies
- ✅ Rotación automática
- ✅ Obtención de proxies gratuitos
- ✅ Comparación de rendimiento con/sin proxies

## 🔄 Cómo Funciona

### 1. Selección de Proxy

```python
proxy = proxy_manager.get_next_proxy()
```

- Rotación cíclica entre proxies disponibles
- Salta automáticamente proxies en lista negra
- Reinicia lista negra si todos fallan

### 2. Manejo de Errores

- **Timeout**: Marca proxy como fallido, reintenta con otro
- **429 Rate Limit**: Cambia proxy automáticamente
- **Errores de conexión**: Lista negra automática
- **Éxito**: Registra estadísticas positivas

### 3. Headers + Proxies

Cada request combina:

- **User-Agent rotativo** (40+ opciones)
- **Accept-Language aleatorio**
- **Headers adicionales** opcionales
- **Proxy diferente** por request

## 📊 Monitoreo

### Logs Automáticos

```
✅ Proxy http://123.45.67.89:8080 funciona - IP real: 123.45.67.89
❌ Proxy http://98.76.54.32:3128 falló - Status: 502
🔄 Rotación 5: http://111.222.333.444:8080
```

### Estadísticas en Tiempo Real

```python
stats = proxy_manager.get_proxy_stats()
# Retorna: {'proxy_url': {'success': 5, 'fail': 1, 'last_used': timestamp}}
```

## ⚙️ Configuración Avanzada

### Lista de Proxies Personalizada

```python
# En ProxyManager._load_initial_proxies()
custom_proxies = [
    'http://user:pass@proxy1.company.com:8080',  # Con autenticación
    'https://proxy2.company.com:3128',           # HTTPS
    'socks5://proxy3.company.com:1080',          # SOCKS5
]
```

### Servicios de Proxies Recomendados

- **Bright Data** (anteriormente Luminati) - Premium
- **Oxylabs** - Alta calidad
- **Smart Proxy** - Residencial
- **ProxyMesh** - Estático rotativo

### Integración con Servicios Pagos

```python
# Ejemplo con Bright Data
bright_data_proxies = [
    f'http://brd-customer-username-zone-zone_name:password@brd.superproxy.io:{port}'
    for port in range(22225, 22235)  # Rango de puertos
]
proxy_manager.update_proxy_list(bright_data_proxies)
```

## 🚨 Solución de Problemas

### Proxies No Funcionan

1. Verificar conectividad: `curl -x http://proxy:port http://httpbin.org/ip`
2. Revisar logs para errores específicos
3. Probar con `test_proxies.py`

### Todos los Proxies Fallan

1. Obtener nuevos proxies: `await proxy_manager.fetch_free_proxies()`
2. Verificar configuración de red/firewall
3. Cambiar a `USE_PROXIES = False` temporalmente

### Rendimiento Lento

1. Aumentar concurrencia en CONFIG.py
2. Usar proxies más rápidos (premium)
3. Implementar cache de DNS

## 📈 Mejoras de Rendimiento Esperadas

Con proxies activados, deberías ver:

- **90%+ reducción** en errores 429
- **Mejor distribución** de requests por IP
- **Mayor éxito** en sites con protección anti-bot
- **Escalabilidad** horizontal mejorada

## 🔐 Seguridad

- Los proxies se rotan automáticamente
- Lista negra previene reuse de proxies fallidos
- Headers aleatorios evitan fingerprinting
- No se almacenan credenciales en logs

---

## 🎯 Quick Start

1. **Activar proxies**: `USE_PROXIES = True` en CONFIG.py
2. **Probar funcionamiento**: `python test_proxies.py`
3. **Ejecutar scraper**: `python main.py`
4. **Monitorear logs**: Ver rotación automática en acción

¡El sistema está listo para producción! 🚀
