# EXECUTION PARAMETERS
ROOT_URL = "https://www.tiendanimal.es/"
#ROOT_URL = "https://sismalaser.es"
#ROOT_URL = "https://worldshishas.com/"
TARGET_PRODUCTS_N = 1000
GENERAL_BATCH_SIZE = 100

# WEBSITE_DETAILS
IMAGE_CLASSES = [
    'details-gallery_picture details-gallery_photoswipe-index-0',
]
NO_OG_IMAGE = False

TITLE_TAGS = [
    {"tag": "h1", "class": "h1 page-title"},
]
NO_OG_TITLE = False

DESCRIPTION_TAGS = [
    {"tag": "div", "class": "elementor-element elementor-element-1441408 elementor-widget elementor-widget-text-editor"},
    {"tag": "div", "class": "elementor-element elementor-element-13672bc elementor-widget elementor-widget-text-editor"},
    {"tag": "div", "class": "elementor-element elementor-element-b8ce3c3 elementor-widget elementor-widget-text-editor"},
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
PRODUCTS_SOLD = "Productos para animales"
# Not required
PRODUCT_EXAMPLES = [
]
# Not required
CATEGORIES_EXAMPLES = [
        "Perros",
        "Gatos",
        "Conejos",
        "Otros animales",
]
