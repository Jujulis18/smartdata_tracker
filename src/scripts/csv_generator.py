"""
Générateur de fichiers CSV pour les données scrapées
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.utils_validators import DataValidator


class CSVGenerator:
    """Générateur de fichiers CSV pour les articles scrapés"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def generate_csv_data(self, articles: List[Dict[str, Any]], 
                         validate: bool = True) -> str:
        """
        Génère les données CSV à partir de la liste d'articles
        
        Args:
            articles: Liste des articles à convertir
            validate: Si True, valide les données avant conversion
            
        Returns:
            Chaîne de caractères représentant le CSV
        """
        if not articles:
            return self._generate_empty_csv()
        
        if validate:
            articles = self.validator.validate_articles(articles)
        
        # Créer le DataFrame
        df = self._create_dataframe(articles)
        
        # Nettoyer et formater les données
        df = self._clean_dataframe(df)
        
        # Convertir en CSV
        return df.to_csv(index=False, encoding='utf-8')
    
    def _create_dataframe(self, articles: List[Dict[str, Any]]) -> pd.DataFrame:
        """Crée un DataFrame pandas à partir des articles"""
        # Définir l'ordre des colonnes
        columns_order = ['title', 'description', 'url', 'date', 'category']
        
        # Créer le DataFrame avec l'ordre des colonnes spécifié
        df = pd.DataFrame(articles)
        
        # Réorganiser les colonnes si elles existent
        existing_columns = [col for col in columns_order if col in df.columns]
        if existing_columns:
            df = df[existing_columns]
        
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie et formate le DataFrame"""
        # Nettoyer les chaînes de caractères
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            # Remplacer les valeurs vides par des chaînes vides
            df[col] = df[col].replace('nan', '')
            df[col] = df[col].replace('None', '')
        
        # Nettoyer les descriptions (supprimer les retours à la ligne excessifs)
        if 'description' in df.columns:
            df['description'] = df['description'].str.replace('\n+', ' ', regex=True)
            df['description'] = df['description'].str.replace('\r+', ' ', regex=True)
            df['description'] = df['description'].str.strip()
        
        # Nettoyer les titres
        if 'title' in df.columns:
            df['title'] = df['title'].str.replace('\n', ' ', regex=False)
            df['title'] = df['title'].str.replace('\r', ' ', regex=False)
            df['title'] = df['title'].str.strip()
        
        return df
    
    def _generate_empty_csv(self) -> str:
        """Génère un CSV vide avec les en-têtes"""
        columns = ['title', 'description', 'url', 'date', 'category']
        empty_df = pd.DataFrame(columns=columns)
        return empty_df.to_csv(index=False, encoding='utf-8')
    
    def generate_filename(self, prefix: str = "articles_scraped") -> str:
        """
        Génère un nom de fichier avec timestamp
        
        Args:
            prefix: Préfixe du nom de fichier
            
        Returns:
            Nom de fichier avec timestamp
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.csv"
    
    def get_csv_preview(self, articles: List[Dict[str, Any]], 
                       max_length: int = 1000) -> str:
        """
        Génère un aperçu du CSV limité en taille
        
        Args:
            articles: Liste des articles
            max_length: Longueur maximale de l'aperçu
            
        Returns:
            Aperçu tronqué du CSV
        """
        csv_data = self.generate_csv_data(articles)
        
        if len(csv_data) <= max_length:
            return csv_data
        
        return csv_data[:max_length] + "..."
    
    def get_statistics(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère des statistiques sur les données
        
        Args:
            articles: Liste des articles
            
        Returns:
            Dictionnaire de statistiques
        """
        if not articles:
            return {
                "total_articles": 0,
                "articles_with_description": 0,
                "articles_with_date": 0,
                "articles_with_url": 0,
                "categories": []
            }
        
        df = pd.DataFrame(articles)
        
        stats = {
            "total_articles": len(articles),
            "articles_with_description": df['description'].notna().sum() if 'description' in df.columns else 0,
            "articles_with_date": df['date'].notna().sum() if 'date' in df.columns else 0,
            "articles_with_url": df['url'].notna().sum() if 'url' in df.columns else 0,
            "categories": df['category'].unique().tolist() if 'category' in df.columns else []
        }
        
        return stats
    
    def export_to_excel(self, articles: List[Dict[str, Any]], 
                       filename: Optional[str] = None) -> bytes:
        """
        Exporte les articles vers un fichier Excel
        
        Args:
            articles: Liste des articles
            filename: Nom du fichier (optionnel)
            
        Returns:
            Données Excel en bytes
        """
        if not articles:
            articles = []
        
        df = self