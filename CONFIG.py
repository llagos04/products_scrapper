# EXECUTION PARAMETERS
ROOT_URL = "https://nude-project.com/"
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

# LLM BATCH SIZE
LLM_BATCH_SIZE = 50

# LLM MODEL
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2

# LLM PROMPT
# Required
PRODUCTS_SOLD = "ropa, camisetas, pantalones..."
# Not required
PRODUCT_EXAMPLES = [
        "Máquina de Soldadura Láser LM-C Industria | Sisma Láser España | Fabricante de Máquinas Láser",
        "Máquina de Grabado y Marcado Láser BIG SMARK Industria | Sisma Láser España | Fabricante de Máquinas Láser",
        "Máquina de Soldadura Láser LM-D READY Joyería | Sisma Láser España | Fabricante de Máquinas Láser",
        "Máquina de Soldadura Láser LM-D READY Dental | Sisma Láser España | Fabricante de Máquinas Láser",
]
# Not required
CATEGORIES_EXAMPLES = [
        "Máquinas Láser Industrial",
        "Máquinas Láser Joyería",
        "Máquinas Láser Dental"
]
