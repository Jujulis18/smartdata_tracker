"""
Gestionnaire des sélecteurs CSS et extraction des données
"""

from typing import Dict, List, Any, Optional


class LocatorManager:
    """Gestionnaire des sélecteurs CSS pour l'extraction de données"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def extract_articles(self, page) -> List[Dict[str, Any]]:
        """
        Extrait les articles de la page courante
        
        Args:
            page: Instance de page Playwright
            
        Returns:
            Liste des articles extraits
        """
        articles = []
        
        try:
            # Récupérer tous les éléments
            title_elements = page.query_selector_all(self.config['locator_title'])
            description_elements = page.query_selector_all(self.config['locator_description'])
            date_elements = page.query_selector_all(self.config['locator_date'])
            
            # Extraire les textes
            descriptions = self._extract_text_from_elements(description_elements)
            dates = self._extract_text_from_elements(date_elements)
            
            # Traiter chaque article
            for i, title_el in enumerate(title_elements):
                article = self._extract_single_article(
                    title_el, descriptions, dates, i
                )
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction des articles: {str(e)}")
        
        return articles
    
    def _extract_text_from_elements(self, elements) -> List[str]:
        """Extrait le texte d'une liste d'éléments"""
        texts = []
        for element in elements:
            text_content = element.text_content()
            texts.append(text_content.strip() if text_content else '')
        return texts
    
    def _extract_single_article(self, title_el, descriptions: List[str], 
                              dates: List[str], index: int) -> Optional[Dict[str, Any]]:
        """
        Extrait un article unique
        
        Args:
            title_el: Élément titre
            descriptions: Liste des descriptions
            dates: Liste des dates
            index: Index de l'article
            
        Returns:
            Dictionnaire représentant l'article ou None si invalide
        """
        try:
            title = title_el.text_content()
            href = title_el.get_attribute('href')
            
            if not title or not title.strip():
                return None
            
            # Construire l'URL complète si nécessaire
            link = self._build_full_url(href)
            
            # Récupérer description et date si disponibles
            description = descriptions[index] if index < len(descriptions) else ''
            date = dates[index] if index < len(dates) else ''
            
            return {
                'title': title.strip(),
                'description': description,
                'url': link,
                'date': date,
                'category': self.config['category']
            }
        
        except Exception as e:
            # Log l'erreur mais continue le traitement
            return None
    
    def _build_full_url(self, href: Optional[str]) -> str:
        """
        Construit une URL complète à partir d'un href
        
        Args:
            href: Attribut href de l'élément
            
        Returns:
            URL complète
        """
        if not href:
            return ''
        
        # Si l'URL est déjà complète
        if href.startswith('http'):
            return href
        
        # Si c'est un chemin relatif
        base_url = self.config['url'].rstrip('/')
        if href.startswith('/'):
            # Chemin absolu
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{href}"
        else:
            # Chemin relatif
            return f"{base_url}/{href.lstrip('/')}"
    
    def validate_locators(self, page) -> Dict[str, bool]:
        """
        Valide que tous les sélecteurs sont présents sur la page
        
        Args:
            page: Instance de page Playwright
            
        Returns:
            Dictionnaire indiquant quels sélecteurs sont valides
        """
        validation_results = {}
        
        locators_to_check = [
            ('title', self.config['locator_title']),
            ('description', self.config['locator_description']),
            ('date', self.config['locator_date']),
            ('next_page', self.config['locator_next_page'])
        ]
        
        for name, selector in locators_to_check:
            try:
                elements = page.query_selector_all(selector)
                validation_results[name] = len(elements) > 0
            except Exception:
                validation_results[name] = False
        
        return validation_results
    
    def get_locator_info(self) -> Dict[str, str]:
        """
        Retourne les informations sur les sélecteurs utilisés
        
        Returns:
            Dictionnaire des sélecteurs
        """
        return {
            'Titre': self.config['locator_title'],
            'Description': self.config['locator_description'],
            'Date': self.config['locator_date'],
            'Lien': self.config.get('locator_link', 'N/A'),
            'Pagination': self.config['locator_next_page']
        }