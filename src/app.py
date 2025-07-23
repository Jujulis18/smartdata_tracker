import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from io import StringIO
import logging

st.set_page_config(
    page_title="Web Scraper Pro",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des variables de session
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None
if 'scraping_logs' not in st.session_state:
    st.session_state.scraping_logs = []
if 'articles_data' not in st.session_state:
    st.session_state.articles_data = []
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False

# Header principal
st.markdown("""
<div style="text-align: center; padding: 2rem; background: rgba(255, 255, 255, 0.15); 
           backdrop-filter: blur(20px); border-radius: 20px; margin-bottom: 2rem;
           box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
    <h1 style="color: white; font-size: 2.5rem; margin-bottom: 0.5rem;">🕷️ Web Scraper Pro</h1>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem;">
        Extraction automatique d'article
    </p>
</div>
""", unsafe_allow_html=True)

# Configuration du scraper
SCRAPER_CONFIG = {
    "url": "https://www.therapixel.fr/blog/",
    "locator_title": "h3 > a",
    "locator_description": ".entry-content > p",
    "locator_date": ".entry-date",
    "locator_link": ".entry-image > a",
    "locator_next_page": ".pagination .page-next",
    "category": "medical"
}

# Configuration du scraper
st.markdown("### ⚙️ Configuration du Scraper")

col1, col2 = st.columns(2)

with col1:
    form = st.form('my_animal')
    
    url = form.text_input('URL cible:', SCRAPER_CONFIG['url'])
    sentence = form.text_input('Catégorie:', SCRAPER_CONFIG['category'])
    submit = form.form_submit_button('Get locators ->')

    st.markdown("### 🎯 Locators utilisés")
    st.code(f"""
    Titre: {SCRAPER_CONFIG['locator_title']}
    Description: {SCRAPER_CONFIG['locator_description']}
    Date: {SCRAPER_CONFIG['locator_date']}
    Pagination: {SCRAPER_CONFIG['locator_next_page']}
    """, language="css")

with col2:
    max_pages = st.number_input("Pages max", value=10, min_value=1, max_value=50)
    delay_seconds = st.number_input("Délai entre pages (s)", value=5, min_value=1, max_value=10)

def add_log(message, log_type="info"):
    st.session_state.scraping_logs.append({
        "message": message,
        "type": log_type
    })

def scrape_website_sync(max_pages, delay, progress_callback=None, log_callback=None):
    """
    Fonction de scraping synchrone utilisant Playwright
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if log_callback:
            log_callback("❌ Playwright non installé. Installez avec: pip install playwright", "error")
            log_callback("📋 Puis exécutez: playwright install", "info")
        return {"articles": [], "total_pages": 0, "total_articles": 0}
    
    articles = []
    current_page = 1
    
    with sync_playwright() as p:
        if log_callback:
            log_callback("🚀 Démarrage du navigateur...", "info")
        
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            if log_callback:
                log_callback(f"🌐 Navigation vers {SCRAPER_CONFIG['url']}", "info")
            
            page.goto(SCRAPER_CONFIG['url'])
            
            has_more = True
            previous_first_title = ""
            previous_url = page.url
            
            while has_more and current_page <= max_pages:
                if log_callback:
                    log_callback(f"📄 Scraping de la page {current_page}...", "info")
                
                # Attendre que les articles se chargent
                try:
                    page.wait_for_selector(SCRAPER_CONFIG['locator_title'], timeout=10000)
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Timeout en attendant les articles: {str(e)}", "warning")
                    break
                
                # Extraire les articles de la page courante
                page_articles = extract_articles_from_page_sync(page, SCRAPER_CONFIG, log_callback)
                
                articles.extend(page_articles)
                
                if log_callback:
                    log_callback(f"✅ Page {current_page} terminée - {len(page_articles)} articles trouvés", "success")
                
                if progress_callback:
                    progress_callback(current_page, len(articles))
                
                # Stocker le premier titre pour détecter les changements
                if page_articles:
                    previous_first_title = page_articles[0].get('title', '')
                
                previous_url = page.url
                
                # Tenter de cliquer sur la page suivante
                has_more = click_next_page_sync(page, SCRAPER_CONFIG['locator_next_page'], 
                                              previous_first_title, previous_url, log_callback)
                
                if has_more:
                    current_page += 1
                    time.sleep(delay)
                else:
                    if log_callback:
                        log_callback("🏁 Plus de pages à scraper", "info")
        
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Erreur pendant le scraping: {str(e)}", "error")
        
        finally:
            browser.close()
    
    if log_callback:
        log_callback(f"🎉 Scraping terminé: {len(articles)} articles sur {current_page} pages", "success")
    
    return {
        "articles": articles,
        "total_pages": current_page,
        "total_articles": len(articles)
    }

def extract_articles_from_page_sync(page, config, log_callback=None):
    """
    Extraire les articles de la page courante (version synchrone)
    """
    articles = []
    
    try:
        # Récupérer tous les titres
        title_elements = page.query_selector_all(config['locator_title'])
        
        # Récupérer les descriptions
        description_elements = page.query_selector_all(config['locator_description'])
        descriptions = []
        for desc_el in description_elements:
            desc_text = desc_el.text_content()
            descriptions.append(desc_text.strip() if desc_text else '')
        
        # Récupérer les dates
        date_elements = page.query_selector_all(config['locator_date'])
        dates = []
        for date_el in date_elements:
            date_text = date_el.text_content()
            dates.append(date_text.strip() if date_text else '')
        
        # Traiter chaque article
        for i, title_el in enumerate(title_elements):
            try:
                title = title_el.text_content()
                href = title_el.get_attribute('href')
                
                if not title or not title.strip():
                    continue
                
                # Construire l'URL complète
                if href:
                    link = href
                else:
                    link = ''
                
                # Récupérer description et date si disponibles
                description = descriptions[i] if i < len(descriptions) else ''
                date = dates[i] if i < len(dates) else ''
                
                article = {
                    'title': title.strip(),
                    'description': description,
                    'url': link,
                    'date': date,
                    'category': config['category']
                }
                
                articles.append(article)
                
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ Erreur lors de l'extraction d'un article: {str(e)}", "warning")
                continue
    
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erreur lors de l'extraction des articles: {str(e)}", "error")
    
    return articles

def click_next_page_sync(page, selector, previous_first_title, previous_url, log_callback=None):
    """
    Cliquer sur le bouton page suivante et vérifier le changement (version synchrone)
    """
    try:
        next_btn = page.locator(selector)
        count = next_btn.count()
        
        if count == 0:
            return False
        
        is_visible = next_btn.is_visible()
        is_enabled = next_btn.is_enabled()
        
        if not (is_visible and is_enabled):
            return False
        
        if log_callback:
            log_callback("👆 Clic sur page suivante...", "info")
        
        next_btn.click()
        
        # Méthode 1: Attendre le changement d'URL
        try:
            page.wait_for_function(
                f"window.location.href !== '{previous_url}'",
                timeout=3000
            )
            return True
        except:
            pass
        
        # Méthode 2: Attendre le changement du premier titre
        try:
            escaped_title = previous_first_title.replace("'", "\\'")
            page.wait_for_function(
                f"""
                () => {{
                    const el = document.querySelector('{SCRAPER_CONFIG["locator_title"]}');
                    const newTitle = el ? el.textContent.trim() : null;
                    return newTitle && newTitle !== '{escaped_title}';
                }}
                """,
                timeout=3000
            )
            return True
        except:
            if log_callback:
                log_callback("⏳ Aucun changement détecté après le clic", "warning")
            return False
    
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erreur lors du clic sur page suivante: {str(e)}", "error")
        return False

def generate_csv_data(articles):
    """Générer les données CSV"""
    df = pd.DataFrame(articles)
    return df.to_csv(index=False)

# Section des contrôles
st.markdown("### 🎮 Contrôles")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🚀 Lancer le scraping", disabled=st.session_state.is_scraping, type="primary"):
        st.session_state.is_scraping = True
        st.session_state.scraping_logs = []
        st.session_state.articles_data = []
        st.rerun()

with col2:
    if st.session_state.scraping_results and not st.session_state.is_scraping:
        csv_data = generate_csv_data(st.session_state.articles_data)
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv_data,
            file_name=f"articles_scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Processus de scraping
if st.session_state.is_scraping:
    st.markdown("### 📊 Scraping en cours...")
    
    # Colonnes pour les résultats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Console de scraping")
        log_container = st.container()
        
    with col2:
        st.markdown("#### 📄 Articles extraits")
        articles_container = st.container()
    
    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Callbacks pour mise à jour en temps réel
    def progress_callback(current_page, total_articles):
        progress = current_page / max_pages
        progress_bar.progress(progress)
        status_text.text(f"Page {current_page}/{max_pages} - {total_articles} articles trouvés")
        
        # Afficher les articles dans le conteneur
        if st.session_state.articles_data:
            with articles_container:
                df_preview = pd.DataFrame(st.session_state.articles_data[-5:])  # Derniers 5 articles
                st.dataframe(df_preview[['title', 'date']], use_container_width=True)
    
    def log_callback(message, log_type):
        add_log(message, log_type)
        # Afficher les logs en temps réel
        with log_container:
            for log in st.session_state.scraping_logs[-10:]:  # Derniers 10 logs
                st.markdown(f"""
                <div class="log-{log['type']}"> {log['message']}</div>
                """, unsafe_allow_html=True)
    
    try:
        add_log("🚀 Initialisation du scraping...", "info")
        
        results = scrape_website_sync(max_pages, delay_seconds, progress_callback, log_callback)
        
        st.session_state.scraping_results = results
        st.session_state.articles_data = results['articles']
        add_log("🎉 Scraping terminé avec succès!", "success")
        
    except Exception as e:
        add_log(f"❌ Erreur: {str(e)}", "error")
    finally:
        st.session_state.is_scraping = False
        progress_bar.progress(1.0)
        status_text.text("Scraping terminé!")
        time.sleep(2)
        st.rerun()

# Affichage des résultats
if st.session_state.scraping_results and not st.session_state.is_scraping:
    results = st.session_state.scraping_results
    
    # Métriques finales
    st.markdown("### ✅ Mission accomplie ! Scraping terminé avec succès")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h2 style="color: #166534; margin: 0;">{}</h2>
            <p style="color: #6b7280; margin: 0;">Pages scrapées</p>
        </div>
        """.format(results['total_pages']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2 style="color: #166534; margin: 0;">{}</h2>
            <p style="color: #6b7280; margin: 0;">Articles trouvés</p>
        </div>
        """.format(results['total_articles']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h2 style="color: #166534; margin: 0;">CSV</h2>
            <p style="color: #6b7280; margin: 0;">Format export</p>
        </div>
        """, unsafe_allow_html=True)
    
   
    
    # Tableau des articles
    st.markdown("### 📋 Articles extraits")
    if st.session_state.articles_data:
        df = pd.DataFrame(st.session_state.articles_data)
        st.dataframe(df, use_container_width=True)
    
    # Prévisualisation CSV
    st.markdown("### 📄 Aperçu du fichier CSV généré")
    if st.session_state.articles_data:
        csv_preview = generate_csv_data(st.session_state.articles_data)
        st.code(csv_preview[:1000] + "..." if len(csv_preview) > 1000 else csv_preview, language="csv")
        st.info(f"💡 Fichier CSV de {len(st.session_state.articles_data)} articles prêt pour l'importation")

# Console des logs
if st.session_state.scraping_logs:
    with st.expander("📊 Console de scraping détaillée"):
        for log in st.session_state.scraping_logs:
            st.markdown(f"""
            <div class="log-{log['type']}"> {log['message']}</div>
            """, unsafe_allow_html=True)

# Sidebar avec informations
with st.sidebar:
    st.markdown("### 📋 Configuration actuelle")
    st.info(f"""
    **URL:** {SCRAPER_CONFIG['url']}
    
    **Pages max:** {max_pages}
    
    **Délai:** {delay_seconds}s
    
    **Catégorie:** {SCRAPER_CONFIG['category']}
    """)
    
    if st.session_state.scraping_results:
        st.markdown("### 📊 Statistiques")
        st.success(f"**Pages scrapées:** {st.session_state.scraping_results['total_pages']}")
        st.success(f"**Articles trouvés:** {st.session_state.scraping_results['total_articles']}")
    
    st.markdown("### ℹ️ Instructions")
    st.markdown("""
    1. **Configurez** les paramètres de scraping
    2. **Lancez** le processus avec le bouton
    3. **Suivez** les logs en temps réel
    4. **Téléchargez** le fichier CSV final
    
   """)
    
   