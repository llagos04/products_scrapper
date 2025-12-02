# =============================================================================
# 1. EXECUTION PARAMETERS
# =============================================================================

# Define the root URL of the website to scrape
# ROOT_URL = "https://www.tumundosmartphone.com/"
# ROOT_URL = "https://www.lamparas.es/"
# ROOT_URL = "https://naturalezagrow.com/"
# ROOT_URL = "https://valkanik.com/"
# ROOT_URL = "https://sismalaser.es"
# ROOT_URL = "https://worldshishas.com/"
# ROOT_URL = "https://camperizacion.com"
# ROOT_URL = "https://www.telescopiomania.com/"
# ROOT_URL = "https://fotok.es/"
# ROOT_URL = "https://mommahome.com/"
# ROOT_URL = "https://sismalaser.es/"
# ROOT_URL = "https://www.mobile.de/"
# ROOT_URL = "https://www.casasantander.com/"
# ROOT_URL = "https://kinafoto.com//"
# ROOT_URL = "https://www.beflamboyant.com/"
# ROOT_URL = "https://www.cervi.es/"
# ROOT_URL = "https://caravanas1000.com/"
# ROOT_URL = "https://puertascalvente.com/"
# ROOT_URL = "https://www.vitaliahome.es/"
# ROOT_URL = "https://theplanet.es/"
# ROOT_URL = "https://www.serra.immo/"
# ROOT_URL = "https://cecarn.com/"
# ROOT_URL = "https://shop.maraferrez.com/"
# ROOT_URL = "https://casadefieras.es/"
# ROOT_URL = "https://sibaritat.com/"
# ROOT_URL = "https://www.luzeco.com/"
# ROOT_URL = "https://puertasparachimeneas.com/"
# ROOT_URL = "https://runway.maraferrez.com/"
# ROOT_URL = "https://www.lmrgraphics.com/"
# ROOT_URL = "https://www.viajeteca.net/"
# ROOT_URL = "https://www.trofeoutlet.com/"
# ROOT_URL = "https://shop.skymedic.eu/"
# ROOT_URL = "https://www.xuxes.store/"
# ROOT_URL = "https://ridetoot.com/"
# ROOT_URL = "https://sensoriberia.es/"
# ROOT_URL = "https://www.cepillotecnico.es/"
# ROOT_URL = "https://bronoir.com/"
# ROOT_URL = "https://casasruralesmaribel.es/"
# ROOT_URL = "https://buenahierba.shop/"
# ROOT_URL = "https://www.onlycbdfans.com/"
# ROOT_URL = "https://www.posterandpanel.com/"
# ROOT_URL = "https://lacatalanacbd.com/"
# ROOT_URL = "https://www.cbdstoremalaga.com/"
# ROOT_URL = "https://www.icolorprint.com/"
# ROOT_URL = "https://vioksport.es/"
# ROOT_URL = "https://latiendadelosminerales.com/"
# ROOT_URL = "https://www.juguetesabracadabra.es/"
# ROOT_URL = "https://www.puntlove.es/"
# ROOT_URL = "https://www.armitex.com/"
# ROOT_URL = "https://cannacbdistribution.com/"
# ROOT_URL = "https://www.thegoodshisha.com/"
# ROOT_URL = "https://iberohemp.com/"
# ROOT_URL = "https://fixelmovil.com"
# ROOT_URL = "https://www.tiendafetichista.com/"
# ROOT_URL = "https://www.growindustry.es/"
# ROOT_URL = "https://ecoeko.es/"
# ROOT_URL = "https://www.placeforpros.com/"
ROOT_URL = "https://www.imprentaonline24.es/"

# Target number of products to scrape
TARGET_PRODUCTS_N = 2000

# Batch size for general processing
GENERAL_BATCH_SIZE = 5

# =============================================================================
# 3. SELECTORS & EXTRACTION CONFIGURATION
# =============================================================================

# --- TITLE ---
OG_TITLE = False
TITLE_TAGS = [
    # {"tag": "h1", "class": "product_title entry-title"},
    # {"tag": "h1", "class": "jet-headline jet-headline--direction-horizontal"}, # Sisma Laser
    # ... (add other commented out selectors here if needed) ...
    # {"tag": "h1", "class": "font-heading-extra-bold margin0"}, # Place for Pros
    {"tag": "h3", "class": "awp-tituloH3"}, # Imprenta Online 24
]
TITLE_SEPARATORS = [""]

# --- PRICE ---
CHECK_PRICE = False
LOWER_PRICE = True 
PRICE_TAGS = [
    # {"tag": "span", "class": "woocommerce-Price-amount amount"},
    # ... (add other commented out selectors here if needed) ...
    # {"tag": "div", "class": "price__sale"}, # Place for Pros
    {"tag": "span", "id": "resulPrecioConIva"}, # Imprenta Online 24
]

# --- DESCRIPTION ---
OG_DESCRIPTION = True
MODIFY_DESCRIPTION = False
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]
DESCRIPTION_TAGS = [
    # {"tag": "div", "class": "woocommerce-tabs wc-tabs-wrapper"},
    # ... (add other commented out selectors here if needed) ...
    # {"tag": "div", "class": "product__info-wrapper product__info-wrapper-media-left grid__item por"}, # Place for Pros
    {"tag": "div", "class": "col-md-6 col-lg-5 col-xl-7"}, # Imprenta Online 24
]

# --- IMAGES ---
OG_IMAGE = False
IMAGE_IDS = []
IMAGE_CLASSES = ["d-block w-100 img-fluid"]

# =============================================================================
# 4. ADVANCED / NETWORK CONFIGURATION
# =============================================================================

# Number of concurrent requests for fetching titles
CONCURRENT_REQUESTS = 3

# Request timeout in seconds
REQUEST_TIMEOUT = 20

# --- RATE LIMITING ---
USE_RATE_LIMIT = True
MIN_REQUEST_DELAY = 1.0  # Minimum delay between requests (seconds)
MAX_REQUEST_DELAY = 3.0  # Maximum delay between requests (seconds)
BATCH_DELAY = 1.0        # Delay between batches (seconds)
RATE_LIMIT_BACKOFF_MULTIPLIER = 2.0
MAX_RATE_LIMIT_RETRIES = 5

# --- PROXIES ---
USE_PROXIES = False
AUTO_FETCH_PROXIES = False
PROXY_UPDATE_INTERVAL = 3600
