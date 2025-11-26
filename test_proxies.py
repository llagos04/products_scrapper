#!/usr/bin/env python3
"""
Script de prueba para validar el funcionamiento del sistema de proxies
"""
import asyncio
import logging
import sys
import os

# Añadir el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fetcher import proxy_manager, get_random_headers
import aiohttp


async def test_single_proxy(proxy_url, test_url="http://httpbin.org/ip"):
    """
    Prueba un proxy individual
    """
    try:
        headers = get_random_headers()
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(test_url, proxy=proxy_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    real_ip = data.get('origin', 'Unknown')
                    print(f"✅ Proxy {proxy_url} funciona - IP real: {real_ip}")
                    proxy_manager.mark_proxy_success(proxy_url)
                    return True
                else:
                    print(f"❌ Proxy {proxy_url} falló - Status: {response.status}")
                    proxy_manager.mark_proxy_failed(proxy_url)
                    return False
    except (aiohttp.ClientHttpProxyError, aiohttp.ClientConnectorError) as e:
        print(f"❌ Proxy {proxy_url} error de conexión: {e}")
        proxy_manager.mark_proxy_failed(proxy_url)
        return False
    except Exception as e:
        print(f"❌ Proxy {proxy_url} error: {e}")
        proxy_manager.mark_proxy_failed(proxy_url)
        return False


async def test_all_proxies():
    """
    Prueba todos los proxies disponibles
    """
    print("🧪 Probando todos los proxies disponibles...")
    print(f"Proxies configurados: {len(proxy_manager.proxies)}")

    working_proxies = []
    failed_proxies = []

    for i, proxy in enumerate(proxy_manager.proxies[:5], 1):  # Probar solo los primeros 5
        print(f"\n[{i}/{min(5, len(proxy_manager.proxies))}] Probando {proxy}")
        if await test_single_proxy(proxy):
            working_proxies.append(proxy)
        else:
            failed_proxies.append(proxy)

    print("
📊 Resultados:"    print(f"✅ Proxies funcionales: {len(working_proxies)}")
    print(f"❌ Proxies fallidos: {len(failed_proxies)}")
    print(".1f"
    return working_proxies


async def test_proxy_rotation():
    """
    Prueba la rotación de proxies
    """
    print("\n🔄 Probando rotación de proxies...")

    proxies_used = set()
    for i in range(10):
        proxy = proxy_manager.get_next_proxy()
        if proxy:
            proxies_used.add(proxy)
            print(f"Rotación {i+1}: {proxy}")
        else:
            print(f"Rotación {i+1}: Sin proxy disponible")
            break

    print(f"Proxies únicos usados en rotación: {len(proxies_used)}")


async def test_fetch_free_proxies():
    """
    Prueba la función de obtener proxies gratuitos
    """
    print("\n🌐 Probando obtención de proxies gratuitos...")

    try:
        proxies = await proxy_manager.fetch_free_proxies(limit=10)
        print(f"Proxies obtenidos: {len(proxies)}")
        for proxy in proxies[:3]:  # Mostrar primeros 3
            print(f"  - {proxy}")
        return proxies
    except Exception as e:
        print(f"Error obteniendo proxies gratuitos: {e}")
        return []


async def test_with_proxy_vs_without():
    """
    Compara el rendimiento con y sin proxies
    """
    print("\n⚡ Comparando rendimiento con/sin proxies...")

    test_url = "http://httpbin.org/get"
    headers = get_random_headers()

    # Sin proxy
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            start_time = asyncio.get_event_loop().time()
            async with session.get(test_url, timeout=5) as response:
                if response.status == 200:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    print(".2f"    except Exception as e:
        print(f"Sin proxy - Error: {e}")

    # Con proxy
    proxy = proxy_manager.get_next_proxy()
    if proxy:
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(test_url, proxy=proxy, timeout=5) as response:
                    if response.status == 200:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        print(".2f"                        proxy_manager.mark_proxy_success(proxy)
                    else:
                        print(f"Con proxy - Status: {response.status}")
                        proxy_manager.mark_proxy_failed(proxy)
        except Exception as e:
            print(f"Con proxy - Error: {e}")
            proxy_manager.mark_proxy_failed(proxy)


async def main():
    """
    Función principal de pruebas
    """
    print("🚀 Iniciando pruebas del sistema de proxies")
    print("=" * 50)

    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Mostrar configuración actual
    print(f"📋 Configuración:")
    print(f"  - Uso de proxies: {'Activado' if proxy_manager.use_proxies else 'Desactivado'}")
    print(f"  - Proxies disponibles: {len(proxy_manager.proxies)}")
    if not proxy_manager.use_proxies:
        print("  ⚠️  Los proxies están DESACTIVADOS por defecto (usar solo con proxies reales)")
    if len(proxy_manager.proxies) > 0 and "example.com" in proxy_manager.proxies[0]:
        print("  ⚠️  Los proxies incluidos son SOLO EJEMPLOS - no funcionarán")
        print("     Configura proxies reales o usa AUTO_FETCH_PROXIES")
    print()

    # Ejecutar pruebas
    await test_all_proxies()
    await test_proxy_rotation()

    if proxy_manager.use_proxies:
        await test_fetch_free_proxies()
        await test_with_proxy_vs_without()

    # Mostrar estadísticas finales
    print("\n📈 Estadísticas finales:")
    stats = proxy_manager.get_proxy_stats()
    for proxy, stat in stats.items():
        status = "✅" if stat['success'] > 0 else "❌" if stat['fail'] > 0 else "⏳"
        print(f"  {status} {proxy}: {stat['success']} exitosos, {stat['fail']} fallidos")

    print("\n🎉 Pruebas completadas!")


if __name__ == "__main__":
    asyncio.run(main())
