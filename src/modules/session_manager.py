"""
Gestionnaire de session Streamlit
Centralise la gestion des variables de session
"""

import streamlit as st
from typing import Dict, Any, List


class SessionManager:
    """Gestionnaire des variables de session Streamlit"""
    
    def __init__(self):
        self.default_values = {
            'scraping_results': None,
            'scraping_logs': [],
            'articles_data': [],
            'is_scraping': False,
            'current_config': None
        }
    
    def initialize_session(self) -> None:
        """Initialise les variables de session avec des valeurs par défaut"""
        for key, default_value in self.default_values.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def reset_scraping_session(self) -> None:
        """Réinitialise les variables liées au scraping"""
        st.session_state.scraping_results = None
        st.session_state.scraping_logs = []
        st.session_state.articles_data = []
        st.session_state.is_scraping = False
    
    def start_scraping(self) -> None:
        """Démarre une nouvelle session de scraping"""
        st.session_state.is_scraping = True
        st.session_state.scraping_logs = []
        st.session_state.articles_data = []
    
    def stop_scraping(self) -> None:
        """Arrête la session de scraping"""
        st.session_state.is_scraping = False
    
    def add_log(self, message: str, log_type: str = "info") -> None:
        """Ajoute un log à la session"""
        st.session_state.scraping_logs.append({
            "message": message,
            "type": log_type
        })
    
    def update_articles(self, articles: List[Dict[str, Any]]) -> None:
        """Met à jour les articles dans la session"""
        st.session_state.articles_data = articles
    
    def set_results(self, results: Dict[str, Any]) -> None:
        """Définit les résultats finaux du scraping"""
        st.session_state.scraping_results = results
        st.session_state.articles_data = results.get('articles', [])
    
    def get_results(self) -> Dict[str, Any]:
        """Récupère les résultats du scraping"""
        return st.session_state.scraping_results
    
    def get_articles(self) -> List[Dict[str, Any]]:
        """Récupère la liste des articles"""
        return st.session_state.articles_data
    
    def get_logs(self) -> List[Dict[str, str]]:
        """Récupère les logs de scraping"""
        return st.session_state.scraping_logs
    
    def is_scraping_active(self) -> bool:
        """Vérifie si le scraping est en cours"""
        return st.session_state.is_scraping
    
    def has_results(self) -> bool:
        """Vérifie si des résultats sont disponibles"""
        return st.session_state.scraping_results is not None