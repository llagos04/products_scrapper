# EXECUTION PARAMETERS
ROOT_URL = "https://www.canelonsbarcelona.com/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 1000
GENERAL_BATCH_SIZE = 50

# IGNORE URLS WITH:
IGNORE_URLS_WITH = "?order="

# apply rate limit when the responses are 429
USE_RATE_LIMIT = False

# WEBSITE_DETAILS
IMAGE_CLASSES = [
]
NO_OG_IMAGE = False

TITLE_TAGS = [
    {"tag": "h1", "class": "product-name"},
    # {"tag": "h1", "class": "product-name hidden-sm-down heading-title text-uppercase"},
]
NO_OG_TITLE = False

DESCRIPTION_TAGS = [
    # {"tag": "div", "class": "short-description col-sm-12 value content"},
]
NO_OG_DESCRIPTION = False

PRICE_TAGS = [
    {"tag": "div", "class": "current-price"},
    # {"tag": "p", "class": "price"}
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
PRODUCTS_SOLD = "Comida preparada: canalones con o sin gluten, canalones con o sin lactosa, canalones rebozados, croquetas, pollo y verduras al horno"
# Not required
PRODUCT_EXAMPLES = [
    "6 CANELONS DE CARN SENSE BEIXAMEL",
    "CROQUETES DE POLLASTRE AMB PERNIL IBÈRIC",
    "CROQUETES DE CABRALES AMB CEBA CARAMEL.LITZADA",
    "CANELONS VEGANS",
    "CANELONS DE PEIX I MARISC AMB BEIXAMEL"
]

# Not required
CATEGORIES_EXAMPLES = [
    "Canalones",
    "Croquetas",
    "Pollo y verduras al horno",
]
