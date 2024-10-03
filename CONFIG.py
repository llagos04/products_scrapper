# EXECUTION PARAMETERS
ROOT_URL = "https://kundebrand.net/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 1000
GENERAL_BATCH_SIZE = 5

# WEBSITE_DETAILS
IMAGE_CLASSES = [
    'd-block img-fluid',
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
]

# TITLE FETCH BATCH SIZE
CONCURRENT_REQUESTS = 10

# REQUEST TIMEOUT
REQUEST_TIMEOUT = 15

# LLM BATCH SIZE
LLM_BATCH_SIZE = 50

# LLM MODEL
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2

# LLM PROMPT
# Required
PRODUCTS_SOLD = "Ukeleles, guitarras, flautas y accesorios"
# Not required
PRODUCT_EXAMPLES = [
]
# Not required
CATEGORIES_EXAMPLES = [
]
