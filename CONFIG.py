# EXECUTION PARAMETERS
ROOT_URL = "https://worldshishas.com/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 10000
GENERAL_BATCH_SIZE = 10

USE_RATE_LIMIT=False

# IGNORE URLS WITH:
IGNORE_URLS_WITH = ""

# WEBSITE_DETAILS
IMAGE_CLASSES = [
    'zoomContainer',
]
NO_OG_IMAGE = False

TITLE_TAGS = [
    {"tag": "h1", "class": "h1 page-title"},
]
NO_OG_TITLE = False

DESCRIPTION_TAGS = [
    {"tag": "div", "class": "short-description col-sm-12 value content"},
]
NO_OG_DESCRIPTION = False

# Price config
PRICE_TAGS = [
            {"tag": "p", "class": "price"}
            ]
LOWER_PRICE = True

# No stock
CHECK_STOCK = True
STOCK_TAGS = [
    {"tag": "p", "class": "stock"}
]
STOCK_TEXT = "Sin stock"

# TITLE FETCH BATCH SIZE
CONCURRENT_REQUESTS = 10

# REQUEST TIMEOUT
REQUEST_TIMEOUT = 20

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
