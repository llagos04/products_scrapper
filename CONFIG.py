# EXECUTION PARAMETERS
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
ROOT_URL = "https://www.casasantander.com/"

TARGET_PRODUCTS_N = 4000
GENERAL_BATCH_SIZE = 5

MAX_SITEMAPS = 5
CHECK_SITEMAP = True
MAX_URLS = 1000  # Máximo de URLs a procesar

USE_RATE_LIMIT = False

# IGNORE URLS WITH:
IGNORE_URLS_WITH = ""

# WEBSITE_DETAILS
OG_IMAGE = True
IMAGE_CLASSES = [
    'easyzoom easyzoom-product is-ready',
]

# Title
OG_TITLE = True
TITLE_TAGS = [
    # {"tag": "h1", "class": "product_title entry-title"},
    # 
    {"tag": "h1", "class": "jet-headline jet-headline--direction-horizontal"}, # Sisma Laser
]
TITLE_SEPARATORS = ["Sector", "Máq", "Acc", "Fres"]

# Description
OG_DESCRIPTION = False
DESCRIPTION_TAGS = [
    # {"tag": "div", "class": "woocommerce-tabs wc-tabs-wrapper"}, # Worldshishas
    # {"tag": "div", "class": "rte-content"}, # Valkanik
    # {"tag": "div", "class": "short-description"}, # Naturaleza Grow
    # {"tag": "section", "class": "product-description-short"}, # lamparas.es
    # {"tag": "section", "class": "product-description-section block-section"}, # TuMundoSmathpone
    # {"tag": "div", "class": "tab-content"}, # TelescopioMania
    # {"tag": "div", "class": "tab-content"}, # FotoK
    # {"tag": "div", "class": "tab-content"}, # Momma Home
    # {"tag": "div", "id": "descripcion"}, # Sisma Laser
    # {"tag": "div", "id": "caracteristicas"}, # Sisma Laser
    # {"tag": "div", "class": "A3G6X lAeeF vTKPY"}, # mobile.de
    {"tag": "section", "id": "fichapropiedad-bloquedescripcion"}, # Casasantander
    {"tag": "section", "id": "fichapropiedad-bloquecaracteristicas"}, # Casasantander
]
DESCRIPTION_ID = "product-infos-tabs-content"
MODIFY_DESCRIPTION = True
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]


# Price config
CHECK_PRICE = True
PRICE_TAGS = [
            # {"tag": "span", "class": "woocommerce-Price-amount amount"} # Worldshishas
            # {"tag": "span", "class": "product-price current-price-value"}, # Valkanik
            # {"tag": "span", "class": "price"}, # Naturaleza Grow
            # {"tag": "span", "class":"current-price-value"}, # lamparas.es
            # {"tag": "span", "class":" precios"}, # TuMundoSmathpone
            # {"tag": "span", "class": "product-price current-price-value"}, # , FotoK
            # {"tag": "span", "class": "zgAoK dNpqi"}, # Momma Home
            {"tag": "div", "class": "fichapropiedad-precio"}, # Casasantander
            ]
LOWER_PRICE = True

# No stock
CHECK_STOCK = False
STOCK_TAGS = [
    # {"tag": "p", "class": "stock"} # Worldshishas
    {"tag": "span", "class": "js-product-availability badge badge-warning product-unavailable-allow-oosp"} # Valkanik
]
STOCK_TEXT = "Consultar" # Worldshishas

# TITLE FETCH BATCH SIZE
CONCURRENT_REQUESTS = 10

# REQUEST TIMEOUT
REQUEST_TIMEOUT = 20




################ Deprecated ################

# LLM BATCH SIZE
LLM_BATCH_SIZE = 30

# LLM MODEL
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2

# LLM PROMPT
# Required
PRODUCTS_SOLD = "Venden artículos de ropa sobretodo, jerseys, camisas, pantalones, faldas, bisuteria,... Tambien tienen artículos de decoracion como candelabros, centros de mesa, espejos, alfombras, iluminacion, ..."
# Not required
PRODUCT_EXAMPLES = [
]
# Not required
CATEGORIES_EXAMPLES = [
    "TEXTIL HOGAR archivos - Pompas y Regalos",
    "Ambientador Pulverizador archivos - Pompas y Regalos",
    "Velas archivos - Pompas y Regalos",
    ]
