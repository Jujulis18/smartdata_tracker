"""
Système de logging pour le scraping web
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Niveaux de log disponibles"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class ScrapingLogger:
    """Logger spécialisé pour le scraping web"""
    
    def __init__(self, name: str = "WebScraper"):
        self.name = name
        self.logs: List[Dict[str, Any]] = []
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure le logger Python standard"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter les doublons de handlers
        if not self.logger.handlers:
            # Handler pour console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Format des messages
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, 
            context: Optional[Dict[str, Any]] = None):
        """
        Ajoute un log avec niveau et contexte
        
        Args:
            message: Message à logger
            level: Niveau du log
            context: Contexte additionnel (optionnel)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": level.value,
            "context": context or {}
        }
        
        self.logs.append(log_entry)
        
        # Logger aussi dans le système Python
        if level == LogLevel.DEBUG:
            self.logger.debug(message)
        elif level == LogLevel.INFO:
            self.logger.info(message)
        elif level == LogLevel.WARNING:
            self.logger.warning(message)
        elif level == LogLevel.ERROR:
            self.logger.error(message)
        elif level == LogLevel.SUCCESS:
            self.logger.info(f"✅ {message}")
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log de niveau DEBUG"""
        self.log(message, LogLevel.DEBUG, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log de niveau INFO"""
        self.log(message, LogLevel.INFO, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log de niveau WARNING"""
        self.log(message, LogLevel.WARNING, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log de niveau ERROR"""
        self.log(message, LogLevel.ERROR, context)
    
    def success(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log de niveau SUCCESS"""
        self.log(message, LogLevel.SUCCESS, context)
    
    def get_logs(self, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """
        Récupère les logs, optionnellement filtrés par niveau
        
        Args:
            level: Niveau de log à filtrer (optionnel)
            
        Returns:
            Liste des logs
        """
        if level is None:
            return self.logs.copy()
        
        return [log for log in self.logs if log["level"] == level.value]
    
    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les N derniers logs
        
        Args:
            count: Nombre de logs à récupérer
            
        Returns:
            Liste des derniers logs
        """
        return self.logs[-count:] if len(self.logs) >= count else self.logs.copy()
    
    def clear_logs(self):
        """Efface tous les logs"""
        self.logs.clear()
    
    def get_log_summary(self) -> Dict[str, int]:
        """
        Génère un résumé des logs par niveau
        
        Returns:
            Dictionnaire avec le nombre de logs par niveau
        """
        summary = {level.value: 0 for level in LogLevel}
        
        for log in self.logs:
            level = log["level"]
            if level in summary:
                summary[level] += 1
        
        return summary
    
    def export_logs_to_text(self) -> str:
        """
        Exporte tous les logs vers un format texte
        
        Returns:
            Chaîne de caractères contenant tous les logs
        """
        if not self.logs:
            return "Aucun log disponible."
        
        lines = []
        lines.append("=== LOGS DE SCRAPING ===")
        lines.append(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Nombre total de logs: {len(self.logs)}")
        lines.append("")
        
        # Résumé par niveau
        summary = self.get_log_summary()
        lines.append("Résumé par niveau:")
        for level, count in summary.items():
            if count > 0:
                lines.append(f"  {level.upper()}: {count}")
        lines.append("")
        
        # Logs détaillés
        lines.append("=== LOGS DÉTAILLÉS ===")
        for log in self.logs:
            timestamp = log["timestamp"]
            level = log["level"].upper()
            message = log["message"]
            
            line = f"[{timestamp}] {level}: {message}"
            
            # Ajouter le contexte si présent
            if log.get("context"):
                context_str = ", ".join([f"{k}={v}" for k, v in log["context"].items()])
                line += f" | Context: {context_str}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def log_scraping_start(self, url: str, max_pages: int, delay: int):
        """Log le début du scraping avec les paramètres"""
        context = {
            "url": url,
            "max_pages": max_pages,
            "delay": delay
        }
        self.info("🚀 Début du scraping", context)
    
    def log_page_start(self, page_number: int, url: str):
        """Log le début du scraping d'une page"""
        context = {
            "page": page_number,
            "url": url
        }
        self.info(f"📄 Scraping de la page {page_number}", context)
    
    def log_page_complete(self, page_number: int, articles_count: int):
        """Log la fin du scraping d'une page"""
        context = {
            "page": page_number,
            "articles_found": articles_count
        }
        self.success(f"Page {page_number} terminée - {articles_count} articles trouvés", context)
    
    def log_scraping_complete(self, total_pages: int, total_articles: int, duration: float):
        """Log la fin du scraping avec les statistiques"""
        context = {
            "total_pages": total_pages,
            "total_articles": total_articles,
            "duration_seconds": duration
        }
        self.success(f"Scraping terminé: {total_articles} articles sur {total_pages} pages en {duration:.2f}s", context)
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log une erreur avec son contexte"""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **context
        }
        self.error(f"Erreur: {str(error)}", error_context)