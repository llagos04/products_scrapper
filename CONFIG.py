# EXECUTION PARAMETERS
# ROOT_URL = "https://www.tumundosmartphone.com/"
# ROOT_URL = "https://www.lamparas.es/"
# ROOT_URL = "https://naturalezagrow.com/"
# ROOT_URL = "https://valkanik.com/"
# ROOT_URL = "https://sismalaser.es"
# ROOT_URL = "https://worldshishas.com/"
# ROOT_URL = "https://camperizacion.com"
# ROOT_URL = "https://www.telescopiomania.com/"
# ROOT_URL = "https://fotok.es/"
# ROOT_URL = "https://mommahome.com/"
# ROOT_URL = "https://sismalaser.es/"
# ROOT_URL = "https://www.mobile.de/"
# ROOT_URL = "https://www.casasantander.com/"
# ROOT_URL = "https://kinafoto.com//"
# ROOT_URL = "https://www.beflamboyant.com/"
# ROOT_URL = "https://www.cervi.es/"
# ROOT_URL = "https://caravanas1000.com/"
# ROOT_URL = "https://puertascalvente.com/"
# ROOT_URL = "https://www.vitaliahome.es/"
# ROOT_URL = "https://theplanet.es/"
# ROOT_URL = "https://www.serra.immo/"
# ROOT_URL = "https://cecarn.com/"
# ROOT_URL = "https://shop.maraferrez.com/"
# ROOT_URL = "https://casadefieras.es/"
# ROOT_URL = "https://sibaritat.com/"
# ROOT_URL = "https://www.luzeco.com/"
# ROOT_URL = "https://puertasparachimeneas.com/"
# ROOT_URL = "https://runway.maraferrez.com/"
# ROOT_URL = "https://www.lmrgraphics.com/"
ROOT_URL = "https://www.viajeteca.net/"

USE_PLAYWRIGHT = False

TARGET_PRODUCTS_N = 2000
GENERAL_BATCH_SIZE = 5

MAX_SITEMAPS = 5
CHECK_SITEMAP = True
MAX_URLS = 1000  # Máximo de URLs a procesar

USE_RATE_LIMIT = False

# IGNORE URLS WITH:
IGNORE_URLS_WITH = "https://www.kiwichi.com?add-to-cart=5767"

# WEBSITE_DETAILS
OG_IMAGE = False
IMAGE_IDS = [
    'bigpic',
]
IMAGE_CLASSES = [

]

# Custom image pattern for specific websites
CUSTOM_IMAGE_PATTERN = "viajeteca.net/fotos/"  # Pattern to search in img src attribute
MODIFY_IMAGE_URL = False #cervi.es


# Title
OG_TITLE = False
TITLE_TAGS = [
    # {"tag": "h1", "class": "product_title entry-title"},
    # 
    # {"tag": "h1", "class": "jet-headline jet-headline--direction-horizontal"}, # Sisma Laser
    # {"tag": "div", "class": "elementor-element elementor-element-110cb77 elementor-widget elementor-widget-heading"}, # Kinafoto
    # {"tag": "h1", "class": "h2 product-single__title"}, # Beflamboyant
    # {"tag": "div", "class": "cls1156General"},
    # {"tag": "h1", "class": "product_title entry-title elementor-heading-title elementor-size-default"},
    # {"tag": "h1", "class": "product_title entry-title wd-entities-title"},
    # {"tag": "h1", "class": "brxe-heading"}, # Vitalia
    # {"tag": "h2", "class": "brxe-heading text-body"}, # The Planet
    # {"tag": "h1", "class": ""}, # Serra
    # {"tag": "h1", "class": ""}, # Cecarn
    # {"tag": "h1", "class": ""}, # Maraferrez
    # {"tag": "h1", "class": "product__heading h1"}, # Casa de Fieras
    # {"tag": "h1", "class": "h1 product-detail-name"}, # Sibaritat
    # {"tag": "h1", "class": "h1 page-title"}, # Luzeco
    # {"tag": "h1", "itemprop": "name"}, # Puertas Parachimeneas
    # {"tag": "h1", "class": "product_title entry-title wd-entities-title"}, # MaraFerrez
    # {"tag": "h1", "class": ""}, # LMRGraphics
    {"tag": "h1", "class": ""}, # Viajeteca
]
TITLE_SEPARATORS = ["-"]

# Description
OG_DESCRIPTION = False
DESCRIPTION_TAGS = [
    # {"tag": "div", "class": "woocommerce-tabs wc-tabs-wrapper"}, # Worldshishas
    # {"tag": "div", "class": "rte-content"}, # Valkanik
    # {"tag": "div", "class": "short-description"}, # Naturaleza Grow
    # {"tag": "section", "class": "product-description-short"}, # lamparas.es
    # {"tag": "section", "class": "product-description-section block-section"}, # TuMundoSmathpone
    # {"tag": "div", "class": "tab-content"}, # TelescopioMania
    # {"tag": "div", "class": "tab-content"}, # FotoK
    # {"tag": "div", "class": "tab-content"}, # Momma Home
    # {"tag": "div", "id": "descripcion"}, # Sisma Laser
    # {"tag": "div", "id": "caracteristicas"}, # Sisma Laser
    # {"tag": "div", "class": "A3G6X lAeeF vTKPY"}, # mobile.de
    # {"tag": "section", "id": "fichapropiedad-bloquedescripcion"}, # Casasantander
    # {"tag": "section", "id": "fichapropiedad-bloquecaracteristicas"}, # Casasantander
    # {"tag": "div", "class": "elementor-element elementor-element-94f67fd elementor-widget elementor-widget-woocommerce-product-content"}, # Kinafoto
    # {"tag": "div", "class": "collapsible-content__inner rte"}, # Beflamboyant
    # {"tag": "div", "class": "product-page-sections"}, # Kiwichi
    # {"tag": "div", "class": "claseGrupo"}, # FotoK
    # {"tag": "div", "class": "dvDescripcionITR3"}, # FotoK
    # {"tag": "div", "class": "elementor-element elementor-element-f1e1dcd e-con-full e-flex e-con e-child"}, # caravanas1000
    # {"tag": "div", "class": "elementor-element elementor-element-e140c15 e-con-full e-flex e-con e-child"}, # caravanas1000
    # {"tag": "div", "class": "elementor-element elementor-element-8390e4c e-flex e-con-boxed e-con e-child"}, # caravanas1000
    # {"tag": "div", "class": "woocommerce-product-details__short-description"},
    # {"tag": "div", "class": "elementor-column elementor-col-100 elementor-top-column elementor-element elementor-element-3e169063"},
    # {"tag": "div", "class": "wd-negative-gap elementor-section elementor-top-section elementor-element elementor-element-19f8fab2 elementor-section-boxed elementor-section-height-default elementor-section-height-default"},
    # {"tag": "div", "class": "product-tabs-wrapper"},
    # {"tag": "div", "id": "brxe-fniuvm"}, # Vitalia
    # {"tag": "div", "id": "brxe-aqerrc"}, # Vitalia
    # {"tag": "div", "id": "brxe-khpzid"}, # Vitalia
    # # {"tag": "div", "id": "brxe-mbehmy"}, # Vitalia
    # {"tag": "div", "id": "brxe-djakzg"}, # The Planet
    # {"tag": "div", "id": "brxe-bovnji"}, # The Planet
    # {"tag": "div", "id": "brxe-tgtzer"}, # The Planet
    # {"tag": "div", "id": "brxe-yuyoqv"}, # The Planet
    # {"tag": "div", "class": "property-overview-wrap property-section-wrap"}, # Serra
    # {"tag": "div", "class": "bdescription-content"}, # Serra
    # {"tag": "ul", "class": "list-2-cols list-unstyled"}, # Serra
    # {"tag": "div", "class": "woocommerce et-dynamic-content-woo et-dynamic-content-woo--product_description"}, # Cecarn
    # {"tag": "div", "class": "product__description rte quick-add-hidden"}, # Maraferrez
    # {"tag": "pickup-availability", "class": "product__pickup-availabilities no-js-hidden"}, # Casa de Fieras
    # {"tag": "div", "class": "product__description rte"}, # Casa de Fieras
    # {"tag": "accordion-tab", "class": "product__accordion accordion"}, # Casa de Fieras
    # {"tag": "div", "class": "more-info-product"}, # Casa de Fieras
    # {"tag": "div", "class": "more-info-product"}, # Sibaritat
    # {"tag": "div", "class": "col-sm-12 mt10"}, # Luzeco
    # {"tag": "div", "class": "col-md-12 second-tabs"}, # Luzeco
    # {"tag": "div", "class": "rte align_justify"}, # Puertas Parachimeneas
    # {"tag": "div", "class": "wd-accordion-item"}, # Puertas Parachimeneas
    # {"tag": "div", "class": "col-xxl-3"}, # LMRGraphics
    {"tag": "div", "id": "head_panel02"}, # Viajeteca
]
DESCRIPTION_ID = ""
MODIFY_DESCRIPTION = False
DELETE_DESCRIPTION_CHARACTERS = ["---", "\\"]


# Price config
CHECK_PRICE = False
PRICE_TAGS = [
            # {"tag": "span", "class": "woocommerce-Price-amount amount"} # Worldshishas
            # {"tag": "span", "class": "product-price current-price-value"}, # Valkanik
            # {"tag": "span", "class": "price"}, # Naturaleza Grow
            # {"tag": "span", "class":"current-price-value"}, # lamparas.es
            # {"tag": "span", "class":" precios"}, # TuMundoSmathpone
            # {"tag": "span", "class": "product-price current-price-value"}, # , FotoK
            # {"tag": "span", "class": "zgAoK dNpqi"}, # Momma Home
            # {"tag": "div", "class": "fichapropiedad-precio"}, # Casasantander
            # {"tag": "div", "class": "elementor-element elementor-element-0bfe5ae elementor-widget elementor-widget-woocommerce-product-price"}, # Kinafoto
            # {"tag": "div", "class": "product-block product-block--price"}, # Beflamboyant
            # {"tag": "p", "class": "price product-page-price "}, # Kiwichi
            # {"tag": "'p'", "class": "price"}, # , FotoK
            # {"tag": "p", "class": "price"}
            # {"tag": "div", "id": "brxe-nichlb"} # The Planet
            # {"tag": "li", "class": "item-price"} # Serra
            # {"tag": "span", "class": "woocommerce-Price-amount amount"} # Cecarn
            # {"tag": "div", "class": "price price--large price--show-badge"}, # Maraferrez
            # {"tag": "div", "class": "price__container"} # Maraferrez
            # {"tag": "span", "class": "price-item price-item--regular"}, # Casa de Fieras
            # {"tag": "span", "class": "current-price-value"}, # Sibaritat
            # {"tag": "span", "class": "current-price"}, # Luzeco
            # {"tag": "span", "id": "our_price_display"}, # Puertas Parachimeneas
            # {"tag": "p", "class": "price"}, # Puertas Parachimeneas
            {"tag": "span", "class": "offer-price"}, # Puertas Parachimeneas


            ]
LOWER_PRICE = False

# No stock
CHECK_STOCK = False
STOCK_TAGS = [
    # {"tag": "p", "class": "stock"} # Worldshishas
    {"tag": "span", "class": "js-product-availability badge badge-warning product-unavailable-allow-oosp"} # Valkanik
]
STOCK_TEXT = "Consultar" # Worldshishas

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
