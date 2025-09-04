"""
Composants UI pour l'interface Streamlit
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from config.config_settings import SCRAPER_CONFIG, LIMITS_CONFIG
from scripts.csv_generator import CSVGenerator
from .session_manager import SessionManager


class UIComponents:
    """Composants d'interface utilisateur pour Streamlit"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.csv_generator = CSVGenerator()
    
    def render_header(self):
        """Affiche l'en-tête principal de l'application"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: rgba(255, 255, 255, 0.15); 
                   backdrop-filter: blur(20px); border-radius: 20px; margin-bottom: 2rem;
                   box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
            <h1 style="color: white; font-size: 2.5rem; margin-bottom: 0.5rem;">🕷️ Web Scraper Pro</h1>
            <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem;">
                Extraction automatique d'articles - Version modulaire
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_scraper_config(self):
        """Affiche la section de configuration du scraper"""
        st.markdown("### ⚙️ Configuration du Scraper")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_basic_config()
        
        with col2:
            self._render_advanced_config()
    
    def _render_basic_config(self):
        """Affiche la configuration de base"""
        with st.form('scraper_config'):
            url = st.text_input('URL cible:', SCRAPER_CONFIG['url'])
            category = st.text_input('Catégorie:', SCRAPER_CONFIG['category'])
            submit = st.form_submit_button('Valider configuration')
            
            if submit:
                # Mettre à jour la configuration
                st.session_state.current_config = {
                    **SCRAPER_CONFIG,
                    'url': url,
                    'category': category
                }
                st.success("✅ Configuration mise à jour!")
        
        # Afficher les locators utilisés
        st.markdown("### 🎯 Sélecteurs CSS utilisés")
        config_to_show = st.session_state.get('current_config', SCRAPER_CONFIG)
        
        st.code(f"""
Titre: {config_to_show['locator_title']}
Description: {config_to_show['locator_description']}
Date: {config_to_show['locator_date']}
Pagination: {config_to_show['locator_next_page']}
        """, language="css")
    
    def _render_advanced_config(self):
        """Affiche la configuration avancée"""
        st.markdown("### ⚙️ Paramètres avancés")
        
        max_pages = st.number_input(
            "Pages maximum", 
            value=LIMITS_CONFIG['default_pages'],
            min_value=LIMITS_CONFIG['min_pages'],
            max_value=LIMITS_CONFIG['max_pages_limit']
        )
        
        delay_seconds = st.number_input(
            "Délai entre pages (secondes)", 
            value=LIMITS_CONFIG['default_delay'],
            min_value=LIMITS_CONFIG['min_delay'],
            max_value=LIMITS_CONFIG['max_delay']
        )
        
        # Stocker les paramètres dans la session
        st.session_state.max_pages = max_pages
        st.session_state.delay_seconds = delay_seconds
        
        # Options avancées dans un expander
        with st.expander("🔧 Options avancées"):
            st.checkbox("Mode verbeux", value=True, key="verbose_mode")
            st.checkbox("Validation des données", value=True, key="validate_data")
            st.selectbox(
                "Format d'export", 
                ["CSV", "Excel", "JSON"], 
                index=0,
                key="export_format"
            )
    
    def render_controls(self):
        """Affiche la section des contrôles"""
        st.markdown("### 🎮 Contrôles")
        
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            start_button = st.button(
                "🚀 Lancer le scraping", 
                disabled=self.session_manager.is_scraping_active(),
                type="primary"
            )
            
            if start_button:
                self.session_manager.start_scraping()
                st.rerun()
        
        with col2:
            if self.session_manager.has_results() and not self.session_manager.is_scraping_active():
                self._render_download_button()
        
        with col3:
            if st.button("🔄 Reset", type="secondary"):
                self.session_manager.reset_scraping_session()
                st.rerun()
        
        with col4:
            if st.button("📊 Stats"):
                self._show_statistics_modal()
    
    def _render_download_button(self):
        """Affiche le bouton de téléchargement"""
        articles = self.session_manager.get_articles()
        
        if st.session_state.get('export_format') == 'Excel':
            # Export Excel (non implémenté dans cet exemple)
            st.info("Export Excel - Fonctionnalité à venir")
        else:
            # Export CSV
            csv_data = self.csv_generator.generate_csv_data(articles)
            filename = self.csv_generator.generate_filename()
            
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
    
    def handle_scraping_process(self, scraper):
        """Gère le processus de scraping avec interface temps réel"""
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
        
        # Conteneurs pour mise à jour en temps réel
        self.log_container = log_container
        self.articles_container = articles_container
        self.progress_bar = progress_bar
        self.status_text = status_text
        
        # Lancer le scraping
        self._execute_scraping(scraper)
    
    def _execute_scraping(self, scraper):
        """Exécute le scraping avec callbacks"""
        try:
            max_pages = st.session_state.get('max_pages', LIMITS_CONFIG['default_pages'])
            delay = st.session_state.get('delay_seconds', LIMITS_CONFIG['default_delay'])
            
            # Configuration à utiliser
            config = st.session_state.get('current_config', SCRAPER_CONFIG)
            scraper.config = config
            
            self.session_manager.add_log("🚀 Initialisation du scraping...", "info")
            
            results = scraper.scrape_website(
                max_pages=max_pages,
                delay=delay,
                progress_callback=self._progress_callback,
                log_callback=self._log_callback
            )
            
            self.session_manager.set_results(results)
            self.session_manager.add_log("🎉 Scraping terminé avec succès!", "success")
            
        except Exception as e:
            self.session_manager.add_log(f"❌ Erreur: {str(e)}", "error")
        finally:
            self.session_manager.stop_scraping()
            self.progress_bar.progress(1.0)
            self.status_text.text("Scraping terminé!")
            time.sleep(2)
            st.rerun()
    
    def _progress_callback(self, current_page: int, total_articles: int):
        """Callback pour la mise à jour de la progression"""
        max_pages = st.session_state.get('max_pages', LIMITS_CONFIG['default_pages'])
        progress = current_page / max_pages
        
        self.progress_bar.progress(progress)
        self.status_text.text(f"Page {current_page}/{max_pages} - {total_articles} articles trouvés")
        
        # Afficher les derniers articles
        articles = self.session_manager.get_articles()
        if articles:
            with self.articles_container:
                df_preview = pd.DataFrame(articles[-5:])  # Derniers 5 articles
                if not df_preview.empty:
                    st.dataframe(
                        df_preview[['title', 'date']] if 'date' in df_preview.columns else df_preview[['title']], 
                        use_container_width=True
                    )
    
    def _log_callback(self, message: str, log_type: str):
        """Callback pour les logs en temps réel"""
        self.session_manager.add_log(message, log_type)
        
        # Afficher les derniers logs
        with self.log_container:
            recent_logs = self.session_manager.get_logs()[-10:]  # Derniers 10 logs
            for log in recent_logs:
                log_class = f"log-{log['type']}" if 'type' in log else "log-info"
                st.markdown(f"""
                <div class="{log_class}"> {log.get('message', log)}</div>
                """, unsafe_allow_html=True)
    
    def render_results(self):
        """Affiche les résultats finaux du scraping"""
        if not self.session_manager.has_results():
            st.info("💡 Aucun résultat à afficher. Lancez un scraping pour voir les données.")
            return
        
        articles = self.session_manager.get_articles()
        st.markdown("### 📊 Résultats du scraping")
        
        # Métriques en haut
        self._render_metrics(articles)
        
        # Onglets pour différentes vues
        tab1, tab2, tab3 = st.tabs(["📋 Tableau", "📊 Analyse", "🔍 Détails"])
        
        with tab1:
            self._render_results_table(articles)
        
        with tab2:
            self._render_results_analysis(articles)
        
        with tab3:
            self._render_results_details(articles)
    
    def _render_metrics(self, articles: List[Dict[str, Any]]):
        """Affiche les métriques principales"""
        if not articles:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📄 Articles extraits",
                value=len(articles)
            )
        
        with col2:
            # Calculer les articles avec description
            articles_with_desc = sum(1 for art in articles if art.get('description', '').strip())
            st.metric(
                label="📝 Avec description",
                value=articles_with_desc,
                delta=f"{(articles_with_desc/len(articles)*100):.1f}%" if articles else "0%"
            )
        
        with col3:
            # Calculer les articles avec date
            articles_with_date = sum(1 for art in articles if art.get('date', '').strip())
            st.metric(
                label="📅 Avec date",
                value=articles_with_date,
                delta=f"{(articles_with_date/len(articles)*100):.1f}%" if articles else "0%"
            )
        
        with col4:
            # Calculer la longueur moyenne des titres
            avg_title_length = sum(len(art.get('title', '')) for art in articles) / len(articles) if articles else 0
            st.metric(
                label="📏 Longueur moy. titre",
                value=f"{avg_title_length:.0f} car."
            )
    
    def _render_results_table(self, articles: List[Dict[str, Any]]):
        """Affiche le tableau des résultats"""
        if not articles:
            st.warning("Aucun article à afficher")
            return
        
        # Créer DataFrame
        df = pd.DataFrame(articles)
        
        # Options de filtrage
        st.markdown("#### 🔍 Filtres")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'date' in df.columns:
                filter_date = st.checkbox("Filtrer par date")
                if filter_date:
                    # Filtre de date (simplifié)
                    recent_only = st.checkbox("Articles récents seulement")
                    if recent_only:
                        # Logique de filtrage par date
                        pass
        
        with col2:
            search_term = st.text_input("🔍 Rechercher dans les titres:")
            if search_term:
                mask = df['title'].str.contains(search_term, case=False, na=False)
                df = df[mask]
        
        # Afficher le tableau
        st.markdown("#### 📋 Données extraites")
        
        # Colonnes à afficher
        columns_to_show = ['title']
        if 'description' in df.columns:
            columns_to_show.append('description')
        if 'date' in df.columns:
            columns_to_show.append('date')
        if 'url' in df.columns:
            columns_to_show.append('url')
        
        # Configuration de l'affichage
        column_config = {
            'title': st.column_config.TextColumn(
                'Titre',
                help='Titre de l\'article',
                max_chars=100
            ),
            'description': st.column_config.TextColumn(
                'Description',
                help='Description de l\'article',
                max_chars=150
            ),
            'date': st.column_config.TextColumn(
                'Date',
                help='Date de publication'
            ),
            'url': st.column_config.LinkColumn(
                'URL',
                help='Lien vers l\'article'
            )
        }
        
        st.dataframe(
            df[columns_to_show],
            use_container_width=True,
            column_config=column_config,
            hide_index=True
        )
    
    def _render_results_analysis(self, articles: List[Dict[str, Any]]):
        """Affiche l'analyse des résultats"""
        if not articles:
            st.warning("Aucune donnée à analyser")
            return
        
        st.markdown("#### 📊 Analyse des données")
        
        # Graphiques d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des longueurs de titre
            title_lengths = [len(art.get('title', '')) for art in articles]
            
            st.markdown("##### Longueur des titres")
            df_lengths = pd.DataFrame({
                'Longueur': title_lengths
            })
            
            st.bar_chart(df_lengths['Longueur'].value_counts().head(10))
        
        with col2:
            # Présence des champs
            st.markdown("##### Complétude des données")
            
            completeness = {
                'Titre': sum(1 for art in articles if art.get('title', '').strip()),
                'Description': sum(1 for art in articles if art.get('description', '').strip()),
                'Date': sum(1 for art in articles if art.get('date', '').strip()),
                'URL': sum(1 for art in articles if art.get('url', '').strip())
            }
            
            df_completeness = pd.DataFrame(
                list(completeness.items()),
                columns=['Champ', 'Nombre']
            )
            
            st.bar_chart(df_completeness.set_index('Champ'))
        
        # Statistiques textuelles
        st.markdown("#### 📈 Statistiques")
        
        # Mots les plus fréquents dans les titres
        if articles:
            all_titles = ' '.join([art.get('title', '') for art in articles])
            words = all_titles.lower().split()
            
            # Filtrer les mots trop courts
            words = [word for word in words if len(word) > 3]
            
            if words:
                from collections import Counter
                word_freq = Counter(words).most_common(10)
                
                st.markdown("##### 🔤 Mots les plus fréquents")
                df_words = pd.DataFrame(word_freq, columns=['Mot', 'Fréquence'])
                st.dataframe(df_words, use_container_width=True, hide_index=True)
    
    def _render_results_details(self, articles: List[Dict[str, Any]]):
        """Affiche les détails des résultats"""
        if not articles:
            st.warning("Aucun détail à afficher")
            return
        
        st.markdown("#### 🔍 Détails des articles")
        
        # Sélecteur d'article
        article_titles = [f"{i+1}. {art.get('title', 'Sans titre')[:50]}..." 
                         for i, art in enumerate(articles)]
        
        selected_idx = st.selectbox(
            "Sélectionner un article:",
            range(len(articles)),
            format_func=lambda x: article_titles[x]
        )
        
        if selected_idx is not None:
            article = articles[selected_idx]
            
            # Afficher les détails
            st.markdown("##### 📄 Informations détaillées")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Titre:** {article.get('title', 'N/A')}")
                
                if article.get('description'):
                    st.markdown(f"**Description:**")
                    st.text_area(
                        "Description complète:",
                        value=article['description'],
                        height=150,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                
                if article.get('url'):
                    st.markdown(f"**URL:** [{article['url']}]({article['url']})")
            
            with col2:
                st.markdown("**Métadonnées:**")
                
                if article.get('date'):
                    st.info(f"📅 Date: {article['date']}")
                
                if article.get('category'):
                    st.info(f"🏷️ Catégorie: {article['category']}")
                
                # Statistiques de l'article
                stats = {
                    "Longueur titre": len(article.get('title', '')),
                    "Longueur description": len(article.get('description', '')),
                    "Mots titre": len(article.get('title', '').split()),
                    "Mots description": len(article.get('description', '').split())
                }
                
                for key, value in stats.items():
                    st.metric(key, value)
    
    def _show_statistics_modal(self):
        """Affiche une modal avec les statistiques détaillées"""
        with st.expander("📊 Statistiques détaillées", expanded=True):
            logs = self.session_manager.get_logs()
            articles = self.session_manager.get_articles()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📋 Logs de session")
                st.metric("Nombre de logs", len(logs))
                
                if logs:
                    log_types = {}
                    for log in logs:
                        log_type = log.get('type', 'info') if isinstance(log, dict) else 'info'
                        log_types[log_type] = log_types.get(log_type, 0) + 1
                    
                    for log_type, count in log_types.items():
                        st.metric(f"Logs {log_type}", count)
            
            with col2:
                st.markdown("##### 🕒 Informations de session")
                
                if hasattr(st.session_state, 'scraping_start_time'):
                    start_time = st.session_state.scraping_start_time
                    duration = datetime.now() - start_time
                    st.metric("Durée session", f"{duration.seconds}s")
                
                st.metric("Articles en mémoire", len(articles) if articles else 0)
                
                # Configuration actuelle
                config = st.session_state.get('current_config', {})
                if config:
                    st.markdown("**Configuration active:**")
                    st.json(config)
    
    def render_logs(self):
        """Affiche la section des logs"""
        st.markdown("### 📋 Logs de session")
        
        logs = self.session_manager.get_logs()
        
        if not logs:
            st.info("Aucun log disponible pour cette session.")
            return
        
        # Options de filtrage des logs
        col1, col2 = st.columns(2)
        
        with col1:
            log_filter = st.selectbox(
                "Filtrer par type:",
                ["Tous", "info", "success", "error", "warning"]
            )
        
        with col2:
            max_logs = st.number_input(
                "Nombre maximum de logs:",
                min_value=10,
                max_value=1000,
                value=100
            )
        
        # Filtrer les logs
        filtered_logs = logs
        if log_filter != "Tous":
            filtered_logs = [
                log for log in logs 
                if (isinstance(log, dict) and log.get('type') == log_filter)
            ]
        
        # Limiter le nombre
        filtered_logs = filtered_logs[-max_logs:]
        
        # Afficher les logs
        for log in reversed(filtered_logs):  # Plus récents en premier
            if isinstance(log, dict):
                log_type = log.get('type', 'info')
                message = log.get('message', str(log))
                timestamp = log.get('timestamp', '')
            else:
                log_type = 'info'
                message = str(log)
                timestamp = ''
            
            # Style selon le type
            if log_type == 'error':
                st.error(f"{timestamp} {message}")
            elif log_type == 'success':
                st.success(f"{timestamp} {message}")
            elif log_type == 'warning':
                st.warning(f"{timestamp} {message}")
            else:
                st.info(f"{timestamp} {message}")
    
    def render_custom_css(self):
        """Ajoute du CSS personnalisé pour l'interface"""
        st.markdown("""
        <style>
        /* Styles pour les logs */
        .log-info {
            color: #1f77b4;
            font-family: monospace;
            font-size: 0.9em;
            margin: 2px 0;
        }
        
        .log-success {
            color: #2ca02c;
            font-family: monospace;
            font-size: 0.9em;
            margin: 2px 0;
        }
        
        .log-error {
            color: #d62728;
            font-family: monospace;
            font-size: 0.9em;
            margin: 2px 0;
        }
        
        .log-warning {
            color: #ff7f0e;
            font-family: monospace;
            font-size: 0.9em;
            margin: 2px 0;
        }
        
        /* Amélioration de l'interface */
        .stButton > button {
            width: 100%;
        }
        
        .metric-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)