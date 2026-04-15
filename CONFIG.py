# =============================================================================
# 1. EXECUTION PARAMETERS
# =============================================================================

# Define the root URL of the website to scrape
ROOT_URL = "https://lafuente.es/"

# Directly specify the sitemap URL (bypass robots.txt search). Leave empty to search automatically.
SITEMAP_URL = ""



# Target number of products to scrape
TARGET_PRODUCTS_N = 1000

# Batch size for general processing
GENERAL_BATCH_SIZE = 5

# =============================================================================
# 1.5. MANUAL LINKS FALLBACK
# =============================================================================
# Used when no sitemap is found. The scraper will extract up to MAX_PRODUCTS_PER_MANUAL_LINK
# products from each of these landing pages.
MANUAL_LINKS = [
]
MAX_PRODUCTS_PER_MANUAL_LINK = 900

# =============================================================================
# 2. SELECTORS & EXTRACTION CONFIGURATION
# =============================================================================

# --- TITLE ---
OG_TITLE = False
TITLE_TAGS = [
    {"tag": "h1", "class": "product_title entry-title"},
]
TITLE_SEPARATORS = [""]

# --- PRICE ---
CHECK_PRICE = True
LOWER_PRICE = False 
PRICE_TAGS = [
    {"tag": "p", "class": "price"},
]

# --- DESCRIPTION ---
OG_DESCRIPTION = False
MODIFY_DESCRIPTION = False
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]
DESCRIPTION_TAGS = [
    {"tag": "div", "class": "product_meta"},

]

# --- SUPPORT LINKS ---
SUPPORT_LINKS_TAGS = [
]


# --- IMAGES ---
OG_IMAGE = True
IMAGE_TAGS = [
    {"tag": "img", "class": "js-qv-product-cover"}
]


# --- STOCK ---
CHECK_STOCK = False
STOCK_TAGS = [
    {"tag": "div", "class": "stock_prod"},
]
STOCK_IN_PATTERNS = ["En stock"]
STOCK_OUT_PATTERNS = ["No hay stock"]


# =============================================================================
# 3. ADVANCED / NETWORK CONFIGURATION
# =============================================================================

# Number of concurrent requests for fetching titles
CONCURRENT_REQUESTS = 20
NUM_WORKERS = 5 # Number of parallel workers

# Request timeout in seconds
REQUEST_TIMEOUT = 20

# --- RATE LIMITING ---
USE_RATE_LIMIT = True
MIN_REQUEST_DELAY = 1.0  # Minimum delay between requests (seconds)
MAX_REQUEST_DELAY = 1.0  # Maximum delay between requests (seconds)
BATCH_DELAY = 1.0        # Delay between batches (seconds)
RATE_LIMIT_BACKOFF_MULTIPLIER = 2.0
MAX_RATE_LIMIT_RETRIES = 5
HTML_LOAD_DELAY = 0 # Delay in seconds to wait after fetching HTML (Note: this only waits, it does not execute JS with aiohttp)

# --- PROXIES ---
USE_PROXIES = False
AUTO_FETCH_PROXIES = False
PROXY_UPDATE_INTERVAL = 3600