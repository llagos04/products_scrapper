# EXECUTION PARAMETERS
# ROOT_URL = "https://www.tumundosmartphone.com/"
# ROOT_URL = "https://www.lamparas.es/"
# ROOT_URL = "https://naturalezagrow.com/"
# ROOT_URL = "https://valkanik.com/"
# ROOT_URL = "https://sismalaser.es"
# ROOT_URL = "https://worldshishas.com/"
ROOT_URL = "https://www.casasantander.com/"

TARGET_PRODUCTS_N = 3000
GENERAL_BATCH_SIZE = 5

MAX_SITEMAPS = 5

USE_RATE_LIMIT = False

# IGNORE URLS WITH:
IGNORE_URLS_WITH = ""

# WEBSITE_DETAILS
OG_IMAGE = True
IMAGE_CLASSES = [
    'zoomContainer',
]

# Title
OG_TITLE = True
TITLE_TAGS = [
    {"tag": "h1", "class": "h1 page-title"},
]
TITLE_SEPARATORS = [" | "]

# Description
OG_DESCRIPTION = False
DESCRIPTION_TAGS = [
    {"tag": "div", "class": "mh-estate__section"}, # Worldshishas
    #{"tag": "div", "class": "rte-content"}, # Valkanik
    # {"tag": "div", "class": "short-description"}, # Naturaleza Grow
    # {"tag": "section", "class": "product-description-short"}, # lamparas.es
    # {"tag": "section", "class": "product-description-section block-section"}, # TuMundoSmathpone
]
MODIFY_DESCRIPTION = True
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]


# Price config
PRICE_TAGS = [
            {"tag": "div", "class": "mh-estate__details__price"} # Worldshishas
            #{"tag": "span", "class": "product-price current-price-value"}, # Valkanik
            # {"tag": "span", "class": "price"}, # Naturaleza Grow
            # {"tag": "span", "class":"current-price-value"}, # lamparas.es
            # {"tag": "span", "class":" precios"}, # TuMundoSmathpone
            ]
LOWER_PRICE = True

# No stock
CHECK_STOCK = False
STOCK_TAGS = [
    {"tag": "p", "class": "stock"} # Worldshishas
]
STOCK_TEXT = "Sin stock" # Worldshishas

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
