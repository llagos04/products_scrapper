# EXECUTION PARAMETERS
ROOT_URL = "https://depataverde.es/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 1000
GENERAL_BATCH_SIZE = 50

USE_RATE_LIMIT=True

# IGNORE URLS WITH:
IGNORE_URLS_WITH = "pt-pt"

# WEBSITE_DETAILS
IMAGE_CLASSES = [
    'zoomContainer',
]
NO_OG_IMAGE = False

TITLE_TAGS = [
    {"tag": "h1", "class": "product-name hidden-sm-down heading-title text-uppercase"},
]
NO_OG_TITLE = False

DESCRIPTION_TAGS = [
    {"tag": "div", "class": "short-description col-sm-12 value content"},
]
NO_OG_DESCRIPTION = False

PRICE_TAGS = [
    {"tag": "p", "class": "price"}
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
PRODUCTS_SOLD = "Artículos relacionados con el CBD: flores, aceites, cosmetica, hachis, ..."

# Not required
PRODUCT_EXAMPLES = [
    "OG Kush CBD | La auténtica Flor OG 100% Legal ✅",
    "Strawberry CBD | Flor de Cáñamo TOP Primera Clase ✅",
    "【Aceite CBD 30% 】| Treinta Por Ciento al Mejor Precio",
    "Skywalker CBD OG | Flor Premium Máxima CALIDAD ✅",
    "Comprar grinder / CALIDAD al mejor PRECIO / De Pata Verde ✅",
    "Flores CBD Preimum |【Cata 2023 Calidad Máxima】:",
]
# Not required
CATEGORIES_EXAMPLES = [
    "Flores CBD",
    "Aceites CBD",
    "Cosmeticos CBD",
]
