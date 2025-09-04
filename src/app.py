"""
Web Scraper Pro - Application principale
Point d'entrée Streamlit
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from modules.session_manager import SessionManager
from modules.ui_components import UIComponents
from scripts.scraper import WebScraper
from config.settings import APP_CONFIG, SCRAPER_CONFIG


def main():
    """Fonction principale de l'application"""
    
    # Configuration de la page
    st.set_page_config(
        page_title=APP_CONFIG['page_title'],
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state=APP_CONFIG['sidebar_state']
    )
    
    # Initialisation du gestionnaire de session
    session_manager = SessionManager()
    session_manager.initialize_session()
    
    # Initialisation des composants UI
    ui = UIComponents()
    
    # Affichage du header
    ui.render_header()
    
    # Configuration du scraper
    ui.render_scraper_config()
    
    # Interface de contrôle
    ui.render_controls()
    
    # Processus de scraping
    if st.session_state.is_scraping:
        scraper = WebScraper(SCRAPER_CONFIG)
        ui.handle_scraping_process(scraper)
    
    # Affichage des résultats
    if st.session_state.scraping_results and not st.session_state.is_scraping:
        ui.render_results()
    
    # Sidebar
    ui.render_sidebar()


if __name__ == "__main__":
    main()