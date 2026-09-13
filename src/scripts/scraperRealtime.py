import streamlit as st
import time
import pandas as pd

# Configuration du scraper


#{
#    "url": "https://www.therapixel.fr/blog/",
#    "locator_title": "h3 > a",
#    "locator_description": ".entry-content > p",
#    "locator_date": ".entry-date",
#    "locator_link": ".entry-image > a",
#    "locator_next_page": ".pagination .page-next",
#    "category": "medical"
#}


def generate_csv_data(articles):
    """Générer les données CSV"""
    df = pd.DataFrame(articles)
    return df.to_csv(index=False)

def scrape_website_sync(max_pages, delay, progress_callback, log_callback, progress_bar, status_text, articles_container, log_container):
    """
    Fonction de scraping synchrone utilisant Playwright
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if log_callback:
            log_callback("❌ Playwright non installé. Installez avec: pip install playwright", "error", log_container)
            log_callback("📋 Puis exécutez: playwright install", "info", log_container)
        return {"articles": [], "total_pages": 0, "total_articles": 0}
    
    articles = []
    current_page = 1
    SCRAPER_CONFIG = st.session_state.SCRAPER_CONFIG
    
    with sync_playwright() as p:
        if log_callback:
            log_callback("🚀 Démarrage du navigateur...", "info", log_container)
        
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            if log_callback:
                log_callback(f"🌐 Navigation vers {SCRAPER_CONFIG['url']}", "info", log_container)
            
            page.goto(SCRAPER_CONFIG['url'])
            
            has_more = True
            previous_first_title = ""
            previous_url = page.url
            
            while has_more and current_page <= max_pages:
                if log_callback:
                    log_callback(f"📄 Scraping de la page {current_page}...", "info", log_container)
                
                # Attendre que les articles se chargent
                try:
                    page.wait_for_selector(SCRAPER_CONFIG['locator_title'], timeout=10000)
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Timeout en attendant les articles: {str(e)}", "warning", log_container)
                    break
                
                # Extraire les articles de la page courante
                page_articles = extract_articles_from_page_sync(page, SCRAPER_CONFIG, log_callback, log_container)
                
                articles.extend(page_articles)
                
                if log_callback:
                    log_callback(f"✅ Page {current_page} terminée - {len(page_articles)} articles trouvés", "success", log_container)
                
                if progress_callback:
                    progress_callback(current_page, len(articles), max_pages, progress_bar, status_text, articles_container)
                
                # Stocker le premier titre pour détecter les changements
                if page_articles:
                    previous_first_title = page_articles[0].get('title', '')
                
                previous_url = page.url
                
                # Tenter de cliquer sur la page suivante
                has_more = click_next_page_sync(page, SCRAPER_CONFIG['locator_next_page'], 
                                              previous_first_title, previous_url, log_callback, log_container)
                
                if has_more:
                    current_page += 1
                    time.sleep(delay)
                else:
                    if log_callback:
                        log_callback("🏁 Plus de pages à scraper", "info", log_container)
        
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Erreur pendant le scraping: {str(e)}", "error", log_container)
        
        finally:
            browser.close()
    
    if log_callback:
        log_callback(f"🎉 Scraping terminé: {len(articles)} articles sur {current_page} pages", "success", log_container)
    
    return {
        "articles": articles,
        "total_pages": current_page,
        "total_articles": len(articles)
    }

def extract_articles_from_page_sync(page, config, log_callback, log_container):
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
                    log_callback(f"⚠️ Erreur lors de l'extraction d'un article: {str(e)}", "warning", log_container)
                continue
    
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erreur lors de l'extraction des articles: {str(e)}", "error", log_container)
    
    return articles

def click_next_page_sync(page, selector, previous_first_title, previous_url, log_callback, log_container):
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
            log_callback("👆 Clic sur page suivante...", "info", log_container)
        
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
                log_callback("⏳ Aucun changement détecté après le clic", "warning", log_container)
            return False
    
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erreur lors du clic sur page suivante: {str(e)}", "error", log_container)
        return False

# Callbacks pour mise à jour en temps réel
def progress_callback(current_page, total_articles, max_pages, progress_bar, status_text, articles_container):
    progress = current_page / max_pages
    progress_bar.progress(progress)
    status_text.text(f"Page {current_page}/{max_pages} - {total_articles} articles trouvés")
    
    # Afficher les articles dans le conteneur
    if st.session_state.articles_data:
        with articles_container:
            df_preview = pd.DataFrame(st.session_state.articles_data[-5:])  # Derniers 5 articles
            st.dataframe(df_preview[['title', 'date']], use_container_width=True)

def log_callback(message, log_type, log_container):
    add_log(message, log_type)
    # Afficher les logs en temps réel
    with log_container:
        for log in st.session_state.scraping_logs[-10:]:  # Derniers 10 logs
            st.markdown(f"""
            <div class="log-{log['type']}"> {log['message']}</div>
            """, unsafe_allow_html=True)

def add_log(message, log_type="info"):
    st.session_state.scraping_logs.append({
        "message": message,
        "type": log_type
    })