"""
Module de scraping web avec Playwright
Gère l'extraction d'articles de sites web
"""

import time
from typing import Dict, List, Any, Callable, Optional
from config.settings import TIMEOUT_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES
from scripts.locator import LocatorManager
from utils.logger import ScrapingLogger


class WebScraper:
    """Classe principale pour le scraping web"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.locator_manager = LocatorManager(config)
        self.logger = ScrapingLogger()
    
    def scrape_website(self, max_pages: int, delay: int, 
                      progress_callback: Optional[Callable] = None,
                      log_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Lance le scraping du site web
        
        Args:
            max_pages: Nombre maximum de pages à scraper
            delay: Délai entre les pages en secondes
            progress_callback: Fonction de callback pour la progression
            log_callback: Fonction de callback pour les logs
            
        Returns:
            Dict contenant les résultats du scraping
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if log_callback:
                log_callback(ERROR_MESSAGES["playwright_missing"], "error")
                log_callback(ERROR_MESSAGES["playwright_install"], "info")
            return {"articles": [], "total_pages": 0, "total_articles": 0}
        
        articles = []
        current_page = 1
        
        with sync_playwright() as p:
            if log_callback:
                log_callback(SUCCESS_MESSAGES["browser_start"], "info")
            
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                if log_callback:
                    log_callback(SUCCESS_MESSAGES["navigation"].format(
                        url=self.config['url']), "info")
                
                page.goto(self.config['url'])
                
                has_more = True
                previous_first_title = ""
                previous_url = page.url
                
                while has_more and current_page <= max_pages:
                    if log_callback:
                        log_callback(SUCCESS_MESSAGES["page_scraping"].format(
                            page=current_page), "info")
                    
                    # Attendre que les articles se chargent
                    if not self._wait_for_articles(page, log_callback):
                        break
                    
                    # Extraire les articles de la page courante
                    page_articles = self._extract_articles_from_page(page, log_callback)
                    articles.extend(page_articles)
                    
                    if log_callback:
                        log_callback(SUCCESS_MESSAGES["page_complete"].format(
                            page=current_page, count=len(page_articles)), "success")
                    
                    if progress_callback:
                        progress_callback(current_page, len(articles))
                    
                    # Stocker le premier titre pour détecter les changements
                    if page_articles:
                        previous_first_title = page_articles[0].get('title', '')
                    
                    previous_url = page.url
                    
                    # Tenter de cliquer sur la page suivante
                    has_more = self._click_next_page(page, previous_first_title, 
                                                   previous_url, log_callback)
                    
                    if has_more:
                        current_page += 1
                        time.sleep(delay)
                    else:
                        if log_callback:
                            log_callback(SUCCESS_MESSAGES["no_more_pages"], "info")
            
            except Exception as e:
                if log_callback:
                    log_callback(f"{ERROR_MESSAGES['scraping_error']}: {str(e)}", "error")
            
            finally:
                browser.close()
        
        if log_callback:
            log_callback(SUCCESS_MESSAGES["scraping_complete"].format(
                articles=len(articles), pages=current_page), "success")
        
        return {
            "articles": articles,
            "total_pages": current_page,
            "total_articles": len(articles)
        }
    
    def _wait_for_articles(self, page, log_callback: Optional[Callable] = None) -> bool:
        """Attend que les articles se chargent sur la page"""
        try:
            page.wait_for_selector(self.config['locator_title'], 
                                 timeout=TIMEOUT_CONFIG['page_load'])
            return True
        except Exception as e:
            if log_callback:
                log_callback(f"{ERROR_MESSAGES['timeout_error']}: {str(e)}", "warning")
            return False
    
    def _extract_articles_from_page(self, page, log_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extrait les articles de la page courante"""
        try:
            return self.locator_manager.extract_articles(page)
        except Exception as e:
            if log_callback:
                log_callback(f"{ERROR_MESSAGES['extraction_error']}: {str(e)}", "error")
            return []
    
    def _click_next_page(self, page, previous_first_title: str, previous_url: str,
                        log_callback: Optional[Callable] = None) -> bool:
        """Clique sur le bouton page suivante et vérifie le changement"""
        try:
            next_btn = page.locator(self.config['locator_next_page'])
            count = next_btn.count()
            
            if count == 0:
                return False
            
            is_visible = next_btn.is_visible()
            is_enabled = next_btn.is_enabled()
            
            if not (is_visible and is_enabled):
                return False
            
            if log_callback:
                log_callback(SUCCESS_MESSAGES["click_next"], "info")
            
            next_btn.click()
            
            # Vérifier le changement de page
            return self._verify_page_change(page, previous_first_title, previous_url, log_callback)
        
        except Exception as e:
            if log_callback:
                log_callback(f"{ERROR_MESSAGES['click_error']}: {str(e)}", "error")
            return False
    
    def _verify_page_change(self, page, previous_first_title: str, previous_url: str,
                           log_callback: Optional[Callable] = None) -> bool:
        """Vérifie que la page a changé après le clic"""
        # Méthode 1: Attendre le changement d'URL
        try:
            page.wait_for_function(
                f"window.location.href !== '{previous_url}'",
                timeout=TIMEOUT_CONFIG['navigation_wait']
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
                    const el = document.querySelector('{self.config["locator_title"]}');
                    const newTitle = el ? el.textContent.trim() : null;
                    return newTitle && newTitle !== '{escaped_title}';
                }}
                """,
                timeout=TIMEOUT_CONFIG['navigation_wait']
            )
            return True
        except:
            if log_callback:
                log_callback("⏳ Aucun changement détecté après le clic", "warning")
            return False