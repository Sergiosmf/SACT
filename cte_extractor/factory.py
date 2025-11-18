# -*- coding: utf-8 -*-
"""
Módulo Factory - Criação de extratores baseado em configurações
"""
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET

from .base import BaseExtractor
from .extractors import CTEExtractorV3
from .exceptions import CTEConfigurationError
from .utils import logger, config_manager


class CTEExtractorFactory:
    """
    Factory para criação de extratores de CT-e.
    
    Aplica o padrão Factory Method para criar extratores específicos
    baseados na versão do schema ou configuração fornecida.
    """
    
    # Mapeamento de versões para classes de extratores
    EXTRACTOR_MAPPING = {
        '3.0': CTEExtractorV3,
        '3.00': CTEExtractorV3,
        'v3': CTEExtractorV3,
        'auto': CTEExtractorV3,  # Padrão
        'default': CTEExtractorV3
    }
    
    @classmethod
    def create_extractor(
        cls,
        schema_version: str = 'auto',
        validate_data: bool = None,
        cache_enabled: bool = None,
        config: Dict[str, Any] = None
    ) -> BaseExtractor:
        """
        Cria extrator baseado na versão do schema.
        
        Args:
            schema_version: Versão do schema ('3.0', 'auto', etc.)
            validate_data: Se deve validar dados (None = usar config)
            cache_enabled: Se deve usar cache (None = usar config)
            config: Configuração customizada
            
        Returns:
            Instância do extrator apropriado
            
        Raises:
            CTEConfigurationError: Quando versão não é suportada
        """
        # Usar configuração global se não fornecida
        if validate_data is None:
            validate_data = config_manager.get('validation', 'strict_mode')
        if cache_enabled is None:
            cache_enabled = config_manager.get('cache', 'enabled')
        
        # Determinar classe do extrator
        extractor_class = cls._get_extractor_class(schema_version)
        
        # Criar e configurar extrator
        try:
            extractor = extractor_class(
                validate_data=validate_data,
                cache_enabled=cache_enabled
            )
            
            # Aplicar configuração customizada se fornecida
            if config:
                cls._apply_custom_config(extractor, config)
            
            logger.logger.info(f"Extrator criado: {extractor_class.__name__} (versão: {schema_version})")
            return extractor
            
        except Exception as e:
            raise CTEConfigurationError(
                f"Erro ao criar extrator para versão {schema_version}: {e}"
            ) from e
    
    @classmethod
    def create_from_xml(
        cls,
        xml_path: str,
        **kwargs
    ) -> BaseExtractor:
        """
        Cria extrator baseado na detecção automática do XML.
        
        Args:
            xml_path: Caminho para o arquivo XML
            **kwargs: Argumentos adicionais para o extrator
            
        Returns:
            Extrator apropriado para o XML
        """
        try:
            # Detectar versão do XML
            version = cls._detect_version_from_xml(xml_path)
            
            # Criar extrator baseado na versão detectada
            return cls.create_extractor(
                schema_version=version,
                **kwargs
            )
            
        except Exception as e:
            logger.log_error("factory_xml_detection_error", str(e), xml_path)
            # Fallback para versão padrão
            return cls.create_extractor('default', **kwargs)
    
    @classmethod
    def _get_extractor_class(cls, schema_version: str) -> type:
        """Determina classe do extrator baseada na versão."""
        version_key = schema_version.lower()
        
        if version_key in cls.EXTRACTOR_MAPPING:
            return cls.EXTRACTOR_MAPPING[version_key]
        
        # Tentar match parcial para versões como "3.1", "3.2"
        if version_key.startswith('3'):
            return cls.EXTRACTOR_MAPPING['v3']
        
        raise CTEConfigurationError(
            f"Versão de schema não suportada: {schema_version}. "
            f"Versões suportadas: {list(cls.EXTRACTOR_MAPPING.keys())}"
        )
    
    @classmethod
    def _detect_version_from_xml(cls, xml_path: str) -> str:
        """Detecta versão do schema a partir do XML."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Tentar extrair versão de diferentes locais
            version_sources = [
                root.get('versao'),
                root.get('version'),
                root.findtext('.//{http://www.portalfiscal.inf.br/cte}versao'),
                root.findtext('.//versao')
            ]
            
            for version in version_sources:
                if version:
                    version = version.strip()
                    if version.startswith('3'):
                        return 'v3'
                    # Adicionar outras versões conforme necessário
            
            # Versão padrão se não detectar
            return 'default'
            
        except Exception:
            return 'default'
    
    @classmethod
    def _apply_custom_config(cls, extractor: BaseExtractor, config: Dict[str, Any]) -> None:
        """Aplica configuração customizada ao extrator."""
        # Implementar aplicação de configurações específicas
        # Por enquanto, apenas log da configuração aplicada
        logger.logger.info(f"Configuração customizada aplicada: {list(config.keys())}")
    
    @classmethod
    def get_supported_versions(cls) -> list:
        """Retorna lista de versões suportadas."""
        return list(cls.EXTRACTOR_MAPPING.keys())
    
    @classmethod
    def register_extractor(cls, version: str, extractor_class: type) -> None:
        """
        Registra novo extrator para uma versão específica.
        
        Permite extensibilidade para novas versões de CT-e.
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise CTEConfigurationError(
                f"Classe {extractor_class.__name__} deve herdar de BaseExtractor"
            )
        
        cls.EXTRACTOR_MAPPING[version] = extractor_class
        logger.logger.info(f"Extrator registrado: {version} -> {extractor_class.__name__}")


class ExtractorBuilder:
    """
    Builder para configuração avançada de extratores.
    
    Permite construção fluente de extratores com configurações complexas.
    """
    
    def __init__(self):
        self._version = 'auto'
        self._validate_data = True
        self._cache_enabled = True
        self._custom_config = {}
        self._strategies = {}
    
    def version(self, version: str) -> 'ExtractorBuilder':
        """Define versão do schema."""
        self._version = version
        return self
    
    def validation(self, enabled: bool) -> 'ExtractorBuilder':
        """Define se deve validar dados."""
        self._validate_data = enabled
        return self
    
    def cache(self, enabled: bool, cache_type: str = 'memory', max_size: int = 100) -> 'ExtractorBuilder':
        """Configura cache."""
        self._cache_enabled = enabled
        self._custom_config['cache'] = {
            'type': cache_type,
            'max_size': max_size
        }
        return self
    
    def strategy(self, strategy_type: str, **kwargs) -> 'ExtractorBuilder':
        """Define estratégias específicas."""
        self._strategies[strategy_type] = kwargs
        return self
    
    def config(self, **custom_config) -> 'ExtractorBuilder':
        """Adiciona configuração customizada."""
        self._custom_config.update(custom_config)
        return self
    
    def build(self) -> BaseExtractor:
        """Constrói o extrator com as configurações definidas."""
        # Merge estratégias na configuração
        if self._strategies:
            self._custom_config['strategies'] = self._strategies
        
        return CTEExtractorFactory.create_extractor(
            schema_version=self._version,
            validate_data=self._validate_data,
            cache_enabled=self._cache_enabled,
            config=self._custom_config
        )


# Exemplos de uso e testes da factory
if __name__ == "__main__":
    # Exemplo 1: Criação simples
    extrator1 = CTEExtractorFactory.create_extractor('v3')
    
    # Exemplo 2: Criação com configuração
    extrator2 = CTEExtractorFactory.create_extractor(
        schema_version='3.0',
        validate_data=True,
        cache_enabled=True
    )
    
    # Exemplo 3: Usando Builder
    extrator3 = (ExtractorBuilder()
                 .version('v3')
                 .validation(True)
                 .cache(True, 'lru', 200)
                 .strategy('extraction', multisource=True)
                 .build())
    
    # Exemplo 4: Detecção automática
    # extrator4 = CTEExtractorFactory.create_from_xml('/caminho/para/cte.xml')
    
    print("✅ Factory testada com sucesso!")
    print(f"Versões suportadas: {CTEExtractorFactory.get_supported_versions()}")
