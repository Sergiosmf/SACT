# -*- coding: utf-8 -*-
"""
Módulo de Utilitários - Logger estruturado e funções auxiliares
"""
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict


class StructuredLogger:
    """Logger estruturado para melhor rastreabilidade e debugging."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura o logger com formato estruturado."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_extraction_start(self, file_path: str):
        """Log do início da extração."""
        self.logger.info(json.dumps({
            "event": "extraction_start",
            "file": file_path,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
    
    def log_extraction_success(self, file_path: str, fields_extracted: int):
        """Log de sucesso na extração."""
        self.logger.info(json.dumps({
            "event": "extraction_success", 
            "file": file_path,
            "fields_extracted": fields_extracted,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
    
    def log_extraction_warning(self, file_path: str, warning: str):
        """Log de aviso durante extração."""
        self.logger.warning(json.dumps({
            "event": "extraction_warning",
            "file": file_path,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
    
    def log_error(self, event: str, error: str, file_path: str = None, **extra_data):
        """Log de erro com dados extras."""
        error_data = {
            "event": event,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        if file_path:
            error_data["file"] = file_path
        
        error_data.update(extra_data)
        
        self.logger.error(json.dumps(error_data, ensure_ascii=False))
    
    def log_validation_error(self, field: str, value: str, error_type: str):
        """Log específico para erros de validação."""
        self.log_error(
            "validation_error",
            f"Erro de validação no campo {field}",
            field=field,
            value=value,
            error_type=error_type
        )
    
    def log_performance(self, operation: str, duration_seconds: float, **metrics):
        """Log de métricas de performance."""
        perf_data = {
            "event": "performance_metric",
            "operation": operation,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat()
        }
        perf_data.update(metrics)
        
        self.logger.info(json.dumps(perf_data, ensure_ascii=False))


# Instância global do logger
logger = StructuredLogger(__name__)


class DataConverter:
    """Utilitários para conversão de dados."""
    
    @staticmethod
    def to_decimal(value: Any) -> Decimal:
        """Converte valor para Decimal com tratamento de erro."""
        if value is None:
            return None
        
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value).strip())
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def clean_string(value: str) -> str:
        """Limpa e normaliza string."""
        if not value:
            return None
        
        cleaned = value.strip()
        return cleaned if cleaned else None
    
    @staticmethod
    def format_currency(value: Decimal) -> str:
        """Formata valor como moeda brasileira."""
        if not value:
            return "R$ 0,00"
        
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def normalize_document(document: str) -> str:
        """Normaliza documento (remove caracteres especiais)."""
        if not document:
            return None
        
        import re
        return re.sub(r'[^0-9]', '', document)


class XMLHelper:
    """Utilitários para manipulação de XML."""
    
    @staticmethod
    def safe_findtext(element, xpath: str, namespaces: dict = None, default: str = None) -> str:
        """Busca texto de forma segura com valor padrão."""
        if element is None:
            return default
        
        try:
            text = element.findtext(xpath, namespaces=namespaces)
            return text.strip() if text else default
        except Exception:
            return default
    
    @staticmethod
    def get_element_text(element, tag: str, namespaces: dict = None) -> str:
        """Extrai texto de um elemento específico."""
        if element is None:
            return None
        
        try:
            full_tag = f"{list(namespaces.keys())[0]}:{tag}" if namespaces else tag
            text = element.findtext(full_tag, namespaces=namespaces)
            return text.strip() if text else None
        except Exception:
            return None


class PerformanceMonitor:
    """Monitor de performance para operações."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.metrics = {}
    
    def __enter__(self):
        """Inicia monitoramento."""
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza monitoramento e registra métricas."""
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Log performance
            logger.log_performance(
                self.operation_name,
                duration,
                **self.metrics
            )
    
    def add_metric(self, key: str, value: Any):
        """Adiciona métrica personalizada."""
        self.metrics[key] = value


class ConfigManager:
    """Gerenciador de configurações."""
    
    DEFAULT_CONFIG = {
        'validation': {
            'strict_mode': True,
            'validate_documents': True,
            'validate_dates': True
        },
        'cache': {
            'enabled': True,
            'type': 'memory',
            'max_size': 100
        },
        'extraction': {
            'strategy': 'standard',
            'multiple_sources': True,
            'regex_fallback': True
        },
        'logging': {
            'level': 'INFO',
            'structured': True,
            'performance_logs': True
        }
    }
    
    def __init__(self, config_dict: dict = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_dict:
            self._merge_config(config_dict)
    
    def _merge_config(self, config_dict: dict):
        """Merge configuração customizada com padrão."""
        for section, values in config_dict.items():
            if section in self.config:
                self.config[section].update(values)
            else:
                self.config[section] = values
    
    def get(self, section: str, key: str = None):
        """Recupera configuração."""
        section_config = self.config.get(section, {})
        if key:
            return section_config.get(key)
        return section_config
    
    def set(self, section: str, key: str, value: Any):
        """Define configuração."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value


# Instância global do gerenciador de configuração
config_manager = ConfigManager()
