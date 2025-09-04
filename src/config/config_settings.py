"""
Configuration centralisée de l'application
"""

# Configuration de l'application Streamlit
APP_CONFIG = {
    "page_title": "Web Scraper Pro",
    "page_icon": "🕷️",
    "layout": "wide",
    "sidebar_state": "expanded"
}

# Configuration par défaut du scraper
SCRAPER_CONFIG = {
    "url": "https://www.therapixel.fr/blog/",
    "locator_title": "h3 > a",
    "locator_description": ".entry-content > p",
    "locator_date": ".entry-date",
    "locator_link": ".entry-image > a",
    "locator_next_page": ".pagination .page-next",
    "category": "medical"
}

# Configuration des limites
LIMITS_CONFIG = {
    "max_pages_limit": 50,
    "min_pages": 1,
    "default_pages": 10,
    "max_delay": 10,
    "min_delay": 1,
    "default_delay": 5
}

# Configuration des timeouts
TIMEOUT_CONFIG = {
    "page_load": 10000,
    "element_wait": 3000,
    "navigation_wait": 3000
}

# Messages d'erreur
ERROR_MESSAGES = {
    "playwright_missing": "❌ Playwright non installé. Installez avec: pip install playwright",
    "playwright_install": "📋 Puis exécutez: playwright install",
    "timeout_error": "⚠️ Timeout en attendant les articles",
    "extraction_error": "❌ Erreur lors de l'extraction des articles",
    "click_error": "❌ Erreur lors du clic sur page suivante",
    "scraping_error": "❌ Erreur pendant le scraping"
}

# Messages de succès
SUCCESS_MESSAGES = {
    "browser_start": "🚀 Démarrage du navigateur...",
    "navigation": "🌐 Navigation vers {url}",
    "page_scraping": "📄 Scraping de la page {page}...",
    "page_complete": "✅ Page {page} terminée - {count} articles trouvés",
    "click_next": "👆 Clic sur page suivante...",
    "scraping_complete": "🎉 Scraping terminé: {articles} articles sur {pages} pages",
    "no_more_pages": "🏁 Plus de pages à scraper"
}