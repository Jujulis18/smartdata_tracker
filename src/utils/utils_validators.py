"""
Validateurs pour les données de scraping
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime


class DataValidator:
    """Validateur pour les données d'articles scrapés"""
    
    def __init__(self):
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        self.required_fields = ['title']
        self.optional_fields = ['description', 'url', 'date', 'category']
    
    def validate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valide une liste d'articles et retourne les articles valides
        
        Args:
            articles: Liste des articles à valider
            
        Returns:
            Liste des articles valides
        """
        valid_articles = []
        
        for i, article in enumerate(articles):
            try:
                validated_article = self.validate_single_article(article)
                if validated_article:
                    valid_articles.append(validated_article)
            except Exception as e:
                # Log l'erreur mais continue le traitement
                print(f"Erreur lors de la validation de l'article {i}: {str(e)}")
                continue
        
        return valid_articles
    
    def validate_single_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Valide un article unique
        
        Args:
            article: Dictionnaire représentant l'article
            
        Returns:
            Article validé ou None si invalide
        """
        if not isinstance(article, dict):
            return None
        
        # Vérifier les champs requis
        if not self._has_required_fields(article):
            return None
        
        # Nettoyer et valider chaque champ
        validated_article = {}
        
        # Valider le titre
        title = self._validate_title(article.get('title', ''))
        if not title:
            return None
        validated_article['title'] = title
        
        # Valider les champs optionnels
        validated_article['description'] = self._validate_description(
            article.get('description', ''))
        validated_article['url'] = self._validate_url(article.get('url', ''))
        validated_article['date'] = self._validate_date(article.get('date', ''))
        validated_article['category'] = self._validate_category(
            article.get('category', ''))
        
        return validated_article
    
    def _has_required_fields(self, article: Dict[str, Any]) -> bool:
        """Vérifie que l'article a tous les champs requis"""
        for field in self.required_fields:
            if field not in article or not article[field]:
                return False
        return True
    
    def _validate_title(self, title: Any) -> Optional[str]:
        """
        Valide et nettoie le titre
        
        Args:
            title: Titre à valider
            
        Returns:
            Titre validé ou None si invalide
        """
        if not isinstance(title, str):
            title = str(title) if title is not None else ''
        
        # Nettoyer le titre
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)  # Remplacer les espaces multiples
        title = re.sub(r'[\r\n\t]+', ' ', title)  # Remplacer les retours à la ligne
        
        # Vérifier la longueur
        if not title or len(title) < 3:
            return None
        
        if len(title) > 500:
            title = title[:497] + "..."
        
        return title
    
    def _validate_description(self, description: Any) -> str:
        """
        Valide et nettoie la description
        
        Args:
            description: Description à valider
            
        Returns:
            Description validée
        """
        if not isinstance(description, str):
            description = str(description) if description is not None else ''
        
        # Nettoyer la description
        description = description.strip()
        description = re.sub(r'\s+', ' ', description)  # Espaces multiples
        description = re.sub(r'[\r\n\t]+', ' ', description)  # Retours à la ligne
        
        # Limiter la longueur
        if len(description) > 2000:
            description = description[:1997] + "..."
        
        return description
    
    def _validate_url(self, url: Any) -> str:
        """
        Valide et nettoie l'URL
        
        Args:
            url: URL à valider
            
        Returns:
            URL validée
        """
        if not isinstance(url, str):
            url = str(url) if url is not None else ''
        
        url = url.strip()
        
        if not url:
            return ''
        
        # Vérifier le format de l'URL
        if self.url_pattern.match(url):
            return url
        
        # Tentative de correction d'URL relative
        if url.startswith('/') or not url.startswith('http'):
            # Ne pas essayer de corriger, retourner vide
            return ''
        
        return url
    
    def _validate_date(self, date: Any) -> str:
        """
        Valide et nettoie la date
        
        Args:
            date: Date à valider
            
        Returns:
            Date validée
        """
        if not isinstance(date, str):
            date = str(date) if date is not None else ''
        
        date = date.strip()
        
        if not date:
            return ''
        
        # Tentative de parsing de différents formats de date
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%B %d, %Y',
            '%d %B %Y'
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date, date_format)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Si aucun format ne correspond, retourner la date originale nettoyée
        return re.sub(r'[^\w\s\-/:,]', '', date)[:50]
    
    def _validate_category(self, category: Any) -> str:
        """
        Valide et nettoie la catégorie
        
        Args:
            category: Catégorie à valider
            
        Returns:
            Catégorie validée
        """
        if not isinstance(category, str):
            category = str(category) if category is not None else ''
        
        category = category.strip().lower()
        
        # Limiter la longueur
        if len(category) > 50:
            category = category[:50]
        
        return category
    
    def validate_scraping_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valide la configuration de scraping
        
        Args:
            config: Configuration à valider
            
        Returns:
            Tuple (est_valide, liste_erreurs)
        """
        errors = []
        
        # Vérifier les champs requis
        required_config_fields = [
            'url', 'locator_title', 'locator_description', 
            'locator_date', 'locator_next_page', 'category'
        ]
        
        for field in required_config_fields:
            if field not in config or not config[field]:
                errors.append(f"Champ requis manquant: {field}")
        
        # Valider l'URL
        if 'url' in config:
            if not self._validate_url(config['url']):
                errors.append("URL invalide")
        
        # Valider les sélecteurs CSS
        css_selectors = [
            'locator_title', 'locator_description', 
            'locator_date', 'locator_next_page'
        ]
        
        for selector_field in css_selectors:
            if selector_field in config:
                if not self._validate_css_selector(config[selector_field]):
                    errors.append(f"Sélecteur CSS invalide: {selector_field}")
        
        return len(errors) == 0, errors
    
    def _validate_css_selector(self, selector: str) -> bool:
        """
        Valide un sélecteur CSS basique
        
        Args:
            selector: Sélecteur CSS à valider
            
        Returns:
            True si le sélecteur semble valide
        """
        if not isinstance(selector, str) or not selector.strip():
            return False
        
        # Vérifications basiques
        selector = selector.strip()
        
        # Ne doit pas être vide
        if not selector:
            return False
        
        # Ne doit pas contenir de caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", ';', 'javascript:']
        for char in dangerous_chars:
            if char in selector.lower():
                return False
        
        return True
    
    def get_validation_stats(self, original_articles: List[Dict[str, Any]], 
                           validated_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère des statistiques de validation
        
        Args:
            original_articles: Articles originaux
            validated_articles: Articles après validation
            
        Returns:
            Dictionnaire de statistiques
        """
        original_count = len(original_articles)
        validated_count = len(validated_articles)
        rejected_count = original_count - validated_count
        
        stats = {
            "original_count": original_count,
            "validated_count": validated_count,
            "rejected_count": rejected_count,
            "validation_rate": (validated_count / original_count * 100) if original_count > 0 else 0,
            "fields_stats": {}
        }
        
        # Statistiques par champ
        if validated_articles:
            for field in ['title', 'description', 'url', 'date', 'category']:
                non_empty_count = sum(1 for article in validated_articles 
                                    if article.get(field, '').strip())
                stats["fields_stats"][field] = {
                    "filled_count": non_empty_count,
                    "fill_rate": (non_empty_count / validated_count * 100) if validated_count > 0 else 0
                }
        
        return stats