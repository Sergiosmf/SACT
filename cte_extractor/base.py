# -*- coding: utf-8 -*-
"""
Módulo Base - Classes abstratas e protocols para CT-e Extractor
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Protocol
import xml.etree.ElementTree as ET


class CTEExtractorProtocol(Protocol):
    """Protocol para diferentes implementações de extrator."""
    
    def extrair_dados(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """Extrai dados do CT-e."""
        ...


class BaseExtractor(ABC):
    """
    Classe base abstrata para todos os extratores de CT-e.
    
    Implementa o template method pattern e define a interface comum.
    """
    
    def __init__(self, validate_data: bool = True, cache_enabled: bool = True):
        """
        Inicializa o extrator base.
        
        Args:
            validate_data: Se deve validar os dados extraídos
            cache_enabled: Se deve usar cache para performance
        """
        self._validate_data = validate_data
        self._cache_enabled = cache_enabled
        self._cache = {} if cache_enabled else None
        self._setup_extractor()
    
    @abstractmethod
    def _setup_extractor(self) -> None:
        """Configuração específica do extrator (template method)."""
        pass
    
    @abstractmethod
    def _carregar_xml(self, caminho_arquivo: str) -> None:
        """Carrega e valida o arquivo XML."""
        pass
    
    @abstractmethod
    def _extrair_dados_principais(self) -> Dict[str, Any]:
        """Extrai os dados principais do CT-e."""
        pass
    
    @abstractmethod
    def _validar_dados(self, dados: Dict[str, Any]) -> bool:
        """Valida os dados extraídos."""
        pass
    
    def extrair_dados(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """
        Template method para extração de dados.
        
        Define o fluxo geral de extração que será seguido por todas as implementações.
        """
        try:
            # 1. Carregar XML
            self._carregar_xml(caminho_arquivo)
            
            # 2. Extrair dados principais
            dados = self._extrair_dados_principais()
            
            # 3. Validar se necessário
            if self._validate_data and not self._validar_dados(dados):
                return None
            
            # 4. Pós-processamento (hook method)
            dados = self._pos_processar_dados(dados)
            
            return dados
            
        except Exception as e:
            self._handle_error(e, caminho_arquivo)
            return None
        finally:
            self._limpar_recursos()
    
    def _pos_processar_dados(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Hook method para pós-processamento (pode ser sobrescrito)."""
        return dados
    
    @abstractmethod
    def _handle_error(self, error: Exception, arquivo: str) -> None:
        """Trata erros durante a extração."""
        pass
    
    @abstractmethod
    def _limpar_recursos(self) -> None:
        """Limpa recursos da memória."""
        pass
    
    # Context manager support
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._limpar_recursos()


class ValidationStrategy(Protocol):
    """Strategy para diferentes tipos de validação."""
    
    def validate(self, data: Any) -> bool:
        """Valida os dados usando a estratégia específica."""
        ...


class ExtractionStrategy(Protocol):
    """Strategy para diferentes métodos de extração."""
    
    def extract_element(self, node: ET.Element, xpath: str) -> Any:
        """Extrai elemento usando a estratégia específica."""
        ...


class CacheStrategy(Protocol):
    """Strategy para diferentes tipos de cache."""
    
    def get(self, key: str) -> Any:
        """Recupera valor do cache."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Armazena valor no cache."""
        ...
    
    def clear(self) -> None:
        """Limpa o cache."""
        ...
