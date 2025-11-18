# -*- coding: utf-8 -*-
"""
Módulo de Estratégias - Implementações concretas dos padrões Strategy
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
import xml.etree.ElementTree as ET

from .base import ValidationStrategy, ExtractionStrategy, CacheStrategy
from .exceptions import CTEValidationError, CTECacheError


# ========== VALIDATION STRATEGIES ==========

class StrictValidator(ValidationStrategy):
    """Validador rigoroso que aplica todas as regras de validação."""
    
    def validate(self, data: Any) -> bool:
        """Aplica validação rigorosa."""
        if isinstance(data, dict):
            return self._validate_dict(data)
        return self._validate_single_value(data)
    
    def _validate_dict(self, data: Dict[str, Any]) -> bool:
        """Valida dicionário de dados."""
        required_fields = ['CT-e_chave', 'CT-e_numero']
        return all(field in data and data[field] for field in required_fields)
    
    def _validate_single_value(self, value: Any) -> bool:
        """Valida valor único."""
        return value is not None and str(value).strip() != ""


class LenientValidator(ValidationStrategy):
    """Validador permissivo que aceita dados com algumas falhas."""
    
    def validate(self, data: Any) -> bool:
        """Aplica validação permissiva."""
        return data is not None


class CPFValidator(ValidationStrategy):
    """Validador específico para CPF."""
    
    def validate(self, cpf: str) -> bool:
        """Valida formato de CPF."""
        if not cpf:
            return False
        cpf = re.sub(r'[^0-9]', '', cpf)
        return len(cpf) == 11 and not cpf == cpf[0] * 11


class CNPJValidator(ValidationStrategy):
    """Validador específico para CNPJ."""
    
    def validate(self, cnpj: str) -> bool:
        """Valida formato de CNPJ."""
        if not cnpj:
            return False
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        return len(cnpj) == 14 and not cnpj == cnpj[0] * 14


class PlacaValidator(ValidationStrategy):
    """Validador específico para placas de veículos."""
    
    def validate(self, placa: str) -> bool:
        """Valida formato de placa."""
        if not placa:
            return False
        # Padrão antigo: ABC-1234 ou Mercosul: ABC1D23 ou ABC-1D23
        patterns = [
            r'^[A-Z]{3}-[0-9]{4}$',  # Antigo
            r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$',  # Mercosul sem hífen
            r'^[A-Z]{3}-[0-9][A-Z][0-9]{2}$'  # Mercosul com hífen
        ]
        return any(re.match(pattern, placa) for pattern in patterns)


class DateValidator(ValidationStrategy):
    """Validador específico para datas."""
    
    def validate(self, date_str: str) -> bool:
        """Valida formato de data."""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False


# ========== EXTRACTION STRATEGIES ==========

class StandardExtractionStrategy(ExtractionStrategy):
    """Estratégia padrão de extração."""
    
    def __init__(self, namespaces: Dict[str, str]):
        self.namespaces = namespaces
    
    def extract_element(self, node: ET.Element, xpath: str) -> Any:
        """Extrai elemento usando XPath padrão."""
        if node is None:
            return None
        
        text = node.findtext(xpath, namespaces=self.namespaces)
        return text.strip() if text else None


class MultiSourceExtractionStrategy(ExtractionStrategy):
    """Estratégia que tenta múltiplas fontes para extrair dados."""
    
    def __init__(self, namespaces: Dict[str, str]):
        self.namespaces = namespaces
    
    def extract_element(self, node: ET.Element, xpath_list: list) -> Any:
        """Extrai elemento tentando múltiplos XPaths."""
        if node is None:
            return None
        
        for xpath in xpath_list:
            text = node.findtext(xpath, namespaces=self.namespaces)
            if text and text.strip():
                return text.strip()
        
        return None


class RegexExtractionStrategy(ExtractionStrategy):
    """Estratégia que usa regex para extrair dados de texto."""
    
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)
    
    def extract_element(self, text: str, group: int = 0) -> Any:
        """Extrai usando regex."""
        if not text:
            return None
        
        match = self.pattern.search(text)
        return match.group(group) if match else None


# ========== CACHE STRATEGIES ==========

class MemoryCache(CacheStrategy):
    """Cache simples em memória."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Any:
        """Recupera valor do cache."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Armazena valor no cache."""
        self._cache[key] = value
    
    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()


class LRUCache(CacheStrategy):
    """Cache com política LRU (Least Recently Used)."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = {}
        self._access_order = []
    
    def get(self, key: str) -> Any:
        """Recupera valor e atualiza ordem de acesso."""
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Armazena valor respeitando limite de tamanho."""
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            # Remove o menos recentemente usado
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = value
        self._access_order.append(key)
    
    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()
        self._access_order.clear()


class NoCache(CacheStrategy):
    """Cache desabilitado."""
    
    def get(self, key: str) -> Any:
        return None
    
    def set(self, key: str, value: Any) -> None:
        pass
    
    def clear(self) -> None:
        pass


# ========== FACTORY PARA STRATEGIES ==========

class StrategyFactory:
    """Factory para criar estratégias."""
    
    @staticmethod
    def create_validator(validator_type: str) -> ValidationStrategy:
        """Cria validador baseado no tipo."""
        validators = {
            'strict': StrictValidator(),
            'lenient': LenientValidator(),
            'cpf': CPFValidator(),
            'cnpj': CNPJValidator(),
            'placa': PlacaValidator(),
            'date': DateValidator()
        }
        
        validator = validators.get(validator_type.lower())
        if not validator:
            raise ValueError(f"Tipo de validador desconhecido: {validator_type}")
        
        return validator
    
    @staticmethod
    def create_cache(cache_type: str, **kwargs) -> CacheStrategy:
        """Cria cache baseado no tipo."""
        if cache_type.lower() == 'memory':
            return MemoryCache()
        elif cache_type.lower() == 'lru':
            max_size = kwargs.get('max_size', 100)
            return LRUCache(max_size)
        elif cache_type.lower() == 'none':
            return NoCache()
        else:
            raise ValueError(f"Tipo de cache desconhecido: {cache_type}")
    
    @staticmethod
    def create_extraction_strategy(strategy_type: str, **kwargs) -> ExtractionStrategy:
        """Cria estratégia de extração baseada no tipo."""
        if strategy_type.lower() == 'standard':
            namespaces = kwargs.get('namespaces', {})
            return StandardExtractionStrategy(namespaces)
        elif strategy_type.lower() == 'multisource':
            namespaces = kwargs.get('namespaces', {})
            return MultiSourceExtractionStrategy(namespaces)
        elif strategy_type.lower() == 'regex':
            pattern = kwargs.get('pattern', r'.*')
            return RegexExtractionStrategy(pattern)
        else:
            raise ValueError(f"Tipo de estratégia desconhecido: {strategy_type}")
