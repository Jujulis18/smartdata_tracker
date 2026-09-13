import json
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import subprocess

if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    subprocess.run(["playwright", "install", "--with-deps"], check=False)

import streamlit as st
import pandas as pd
from datetime import datetime

from scripts.locatorDetector import locatorDetection
from scripts.apiSheet import export_to_google_sheet
from scripts.scraperRealtime import generate_csv_data, scrape_website_sync, progress_callback, log_callback, add_log

if 'SCRAPER_CONFIG' not in st.session_state:
    st.session_state['SCRAPER_CONFIG'] = {}

# --- Sidebar ---
st.sidebar.header("🔑 Google Sheets")
api_key_input = st.sidebar.text_area("Clé JSON du compte de service Google Cloud", height=200)

# Sauvegarde dans le cache Streamlit
if api_key_input:
    st.session_state["google_api_key"] = api_key_input
    st.sidebar.success("✅ Clé enregistrée en mémoire de session")

# --- Page ---
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

# --- Configuration du scraper ---
st.markdown("### ⚙️ Configuration du Scraper")

col1, col2 = st.columns(2)

with col1:
    mode = st.radio("Source de l'URL :", ["📋 Liste Google Sheets", "🖊️ Entrer manuellement"])
    form = st.form("scraper_form")
    
    # prendre les liens depuis mistral_cache.json
    with open("mistral_cache.json", "r") as f:
        mistral_cache = json.load(f)
    urls = list(mistral_cache.keys())
    if mode == "📋 Liste Google Sheets" and urls:
        url = form.selectbox("Choisir une URL :", urls)
    else:
        url = form.text_input("URL cible :", "")
        category = form.text_input("Catégorie :", "")
    submit = form.form_submit_button("🔎 Get locators →")

    if submit and url:
        with st.spinner("Détection des locators en cours..."):
            st.session_state.SCRAPER_CONFIG = locatorDetection(url)
        st.success("✅ Locators détectés !")
        st.markdown("### 🎯 Locators utilisés :")
        st.json(st.session_state.SCRAPER_CONFIG)
    elif submit and not url:
        st.warning("⚠️ Merci d’entrer ou de sélectionner une URL.")
            

with col2:
    st.subheader("Scrapper parameters:")
    max_pages = st.number_input("Pages max", value=10, min_value=1, max_value=50)
    delay_seconds = st.number_input("Délai entre pages (s)", value=5, min_value=1, max_value=10)

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

        if "google_api_key" in st.session_state:
            if st.button("📤 Exporter vers Google Sheets"):
                sheet_url = export_to_google_sheet(st.session_state.articles_data)
                if sheet_url:
                    st.success(f"✅ Export réussi ! [Ouvrir le Google Sheet]({sheet_url})")
        else:
            st.info("➡️ Ajoutez d’abord votre clé API Google dans la sidebar pour activer l’export Sheets.")


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
    

    
    try:
        add_log("🚀 Initialisation du scraping...", "info")
        # pourquoi SCRAPER_CONFIG n'est pas utilisé. remis par default?
        results = scrape_website_sync(max_pages, delay_seconds, progress_callback, log_callback, progress_bar, status_text, articles_container, log_container)
        
        st.session_state.scraping_results = results
        st.session_state.articles_data = results['articles']
        add_log("🎉 Scraping terminé avec succès!", "success")
        
    except Exception as e:
        add_log(f"❌ Erreur: {str(e)}", "error")
    finally:
        st.session_state.is_scraping = False
        progress_bar.progress(1.0)
        status_text.text("Scraping terminé!")
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
    
   