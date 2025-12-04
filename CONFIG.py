# =============================================================================
# 1. EXECUTION PARAMETERS
# =============================================================================

# Define the root URL of the website to scrape

ROOT_URL = "https://almabebe.com"

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
    {"tag": "h1", "class": "product_title entry-title elementor-heading-title elementor-size-default"},
]
TITLE_SEPARATORS = [""]

# --- PRICE ---
CHECK_PRICE = True
LOWER_PRICE = True 
PRICE_TAGS = [
    {"tag": "span", "class": "woocommerce-Price-amount amount"},
]

# --- DESCRIPTION ---
OG_DESCRIPTION = False
MODIFY_DESCRIPTION = False
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]
DESCRIPTION_TAGS = [
    {"tag": "div", "class": "woocommerce-Tabs-panel woocommerce-Tabs-panel--description panel entry-content wc-tab"},
]

# --- IMAGES ---
OG_IMAGE = True
IMAGE_IDS = []
IMAGE_CLASSES = [""]

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
MAX_REQUEST_DELAY = 1.0  # Maximum delay between requests (seconds)
BATCH_DELAY = 1.0        # Delay between batches (seconds)
RATE_LIMIT_BACKOFF_MULTIPLIER = 2.0
MAX_RATE_LIMIT_RETRIES = 5

# --- PROXIES ---
USE_PROXIES = False
AUTO_FETCH_PROXIES = False
PROXY_UPDATE_INTERVAL = 3600
