# EXECUTION PARAMETERS
ROOT_URL = "https://kundebrand.com/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 1000
GENERAL_BATCH_SIZE = 50

USE_RATE_LIMIT=False

# IGNORE URLS WITH:
IGNORE_URLS_WITH = ""

# WEBSITE_DETAILS
IMAGE_CLASSES = [
    'zoomContainer',
]
NO_OG_IMAGE = False

TITLE_TAGS = [
    {"tag": "h1", "class": "product-single__title"},
]
NO_OG_TITLE = True

DESCRIPTION_TAGS = [
    {"tag": "div", "class": "short-description col-sm-12 value content"},
]
NO_OG_DESCRIPTION = False

PRICE_TAGS = [
    {"tag": "span", "class": "product-single__price"}
]

# TITLE FETCH BATCH SIZE
CONCURRENT_REQUESTS = 10

# REQUEST TIMEOUT
REQUEST_TIMEOUT = 15

# LLM BATCH SIZE
LLM_BATCH_SIZE = 20

# LLM MODEL
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2

# LLM PROMPT
# Required
PRODUCTS_SOLD = "Ukeleles, guitarras, flautas y accesorios de musica"
# Not required
PRODUCT_EXAMPLES = [
    "Artemis",
    "Zeus",
    "Kunde Moon 26",
    "Kunde Sun Eclipse 23' EQ",
    "Boomwhackers Kunde",
    "Pack Kunde Pluto + Libro 'Ukecole'",
    "Mercury school - Ukelele para la escuela",
    "Llibre Ukelele per a mans menudes",
    "Funda Ukelele Kunde 21' colores variados",
    "Pack Kunde Mercury + Libro 'Uke'"
]
# Not required
CATEGORIES_EXAMPLES = [
]
