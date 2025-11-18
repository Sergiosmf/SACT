# -*- coding: utf-8 -*-
"""
CT-e Extractor - Sistema Orientado a Objetos para Extração de Dados de CT-e

Este módulo fornece uma implementação robusta e extensível para extração de dados
de documentos CT-e (Conhecimento de Transporte eletrônico), aplicando os 4 fundamentos
da Programação Orientada a Objetos:

1. ENCAPSULAMENTO: Dados e comportamentos encapsulados em classes específicas
2. HERANÇA: Hierarquia clara com classe base abstrata e especializações
3. POLIMORFISMO: Strategy pattern para diferentes validações e extrações
4. ABSTRAÇÃO: Interfaces bem definidas e Facade para simplicidade de uso

Principais Componentes:
- Base: Classes abstratas e protocols
- Models: Dataclasses para representação dos dados
- Extractors: Implementações concretas dos extratores
- Strategies: Padrões Strategy para validação, cache e extração
- Factory: Criação de extratores baseada em configuração
- Facade: Interface simplificada para uso
- Utils: Utilitários, logging e configuração
- Exceptions: Hierarquia de exceções específicas

Exemplo de Uso Básico:
    >>> from cte_extractor import CTEFacade
    >>> facade = CTEFacade()
    >>> dados = facade.extrair('meu_cte.xml')
    >>> print(f"CT-e: {dados['CT-e_numero']}")

Exemplo de Uso Avançado:
    >>> from cte_extractor import CTEExtractorFactory, ExtractorBuilder
    >>> 
    >>> # Usando Factory
    >>> extrator = CTEExtractorFactory.create_extractor('v3', validate_data=True)
    >>> with extrator:
    ...     dados = extrator.extrair_dados('cte.xml')
    >>> 
    >>> # Usando Builder
    >>> extrator = (ExtractorBuilder()
    ...              .version('v3')
    ...              .validation(True)
    ...              .cache(True, 'lru', 200)
    ...              .build())

Versão: 2.0.0 (Refatorada com POO)
Autor: Sistema CT-e Extractor
Licença: MIT
"""

# Importações principais para API pública
from .facade import (
    CTEFacade,
    cte_extractor_facade,
    extrair_cte_simples,
    validar_cte
)

from .factory import (
    CTEExtractorFactory,
    ExtractorBuilder
)

from .extractors import (
    CTEExtractorV3,
    CTEExtractorAprimorado  # Alias para compatibilidade
)

from .models import (
    CTe,
    Pessoa,
    Endereco,
    Documentos,
    Localidade,
    Veiculo,
    Carga
)

from .exceptions import (
    CTEExtractionError,
    CTEValidationError,
    CTEParsingError,
    CTESchemaError,
    CTEConfigurationError
)

from .base import (
    BaseExtractor,
    CTEExtractorProtocol,
    ValidationStrategy,
    ExtractionStrategy,
    CacheStrategy
)

from .strategies import (
    StrategyFactory,
    StrictValidator,
    LenientValidator,
    MemoryCache,
    LRUCache
)

from .utils import (
    logger,
    config_manager,
    PerformanceMonitor,
    DataConverter
)

# Metadados do módulo
__version__ = "2.0.0"
__title__ = "CT-e Extractor POO"
__description__ = "Sistema orientado a objetos para extração de dados de CT-e"
__author__ = "CT-e Extractor Team"
__license__ = "MIT"

# API pública - o que será exportado com "from cte_extractor import *"
__all__ = [
    # Facade (Interface Principal)
    'CTEFacade',
    'cte_extractor_facade',
    'extrair_cte_simples',
    'validar_cte',
    
    # Factory e Builder
    'CTEExtractorFactory',
    'ExtractorBuilder',
    
    # Extratores
    'CTEExtractorV3',
    'CTEExtractorAprimorado',
    
    # Modelos de Dados
    'CTe',
    'Pessoa',
    'Endereco', 
    'Documentos',
    'Localidade',
    'Veiculo',
    'Carga',
    
    # Base e Protocols
    'BaseExtractor',
    'CTEExtractorProtocol',
    
    # Exceções
    'CTEExtractionError',
    'CTEValidationError',
    'CTEParsingError',
    'CTESchemaError',
    'CTEConfigurationError',
    
    # Strategies
    'StrategyFactory',
    'ValidationStrategy',
    'ExtractionStrategy',
    'CacheStrategy',
    
    # Utilitários
    'logger',
    'config_manager',
    'PerformanceMonitor'
]

# Configuração de logging padrão
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Banner informativo (apenas em modo debug)
def _print_banner():
    """Imprime banner informativo do sistema."""
    import sys
    if '--debug' in sys.argv or 'debug' in str(sys.argv).lower():
        print(f"""
╭─────────────────────────────────────────────────────────────╮
│                   🚚 CT-e EXTRACTOR v{__version__}                   │
│                Sistema Orientado a Objetos                 │
│                                                             │
│  ✅ Encapsulamento    ✅ Herança                            │
│  ✅ Polimorfismo      ✅ Abstração                          │
│                                                             │
│  Componentes Principais:                                    │
│  • CTEFacade - Interface simplificada                      │
│  • CTEExtractorFactory - Criação de extratores             │
│  • ExtractorBuilder - Configuração fluente                 │
│  • StrategyFactory - Padrões de comportamento              │
│                                                             │
│  📖 Documentação completa disponível                       │
╰─────────────────────────────────────────────────────────────╯
        """)

# Executar banner se em modo debug
_print_banner()

def get_version_info():
    """Retorna informações detalhadas da versão."""
    return {
        'version': __version__,
        'title': __title__,
        'description': __description__,
        'components': {
            'extractors': ['CTEExtractorV3'],
            'strategies': ['StrictValidator', 'LenientValidator', 'MemoryCache', 'LRUCache'],
            'models': ['CTe', 'Pessoa', 'Endereco', 'Documentos', 'Localidade', 'Veiculo', 'Carga'],
            'patterns': ['Factory', 'Builder', 'Strategy', 'Facade', 'Template Method']
        },
        'features': [
            'Extração robusta de dados CT-e',
            'Validação automática de documentos',
            'Cache inteligente para performance',
            'Logging estruturado',
            'Suporte a múltiplas versões de schema',
            'Interface simplificada via Facade',
            'Configuração flexível via Builder',
            'Extensibilidade via Strategy Pattern'
        ]
    }

def show_example():
    """Mostra exemplo de uso básico."""
    example_code = '''
# Exemplo de uso básico do CT-e Extractor v2.0.0

from cte_extractor import CTEFacade

# 1. Uso mais simples possível
facade = CTEFacade()
dados = facade.extrair('meu_cte.xml')
print(f"CT-e número: {dados['CT-e_numero']}")

# 2. Extração de múltiplos arquivos
resultados = facade.extrair_multiplos(['cte1.xml', 'cte2.xml'])

# 3. Validação de arquivo
if facade.validar_arquivo('cte.xml')['eh_cte']:
    print("✅ Arquivo CT-e válido!")

# 4. Configuração avançada com Builder
from cte_extractor import ExtractorBuilder

extrator = (ExtractorBuilder()
           .version('v3')
           .validation(True)
           .cache(True, 'lru', 200)
           .build())

# 5. Context manager
from cte_extractor import cte_extractor_facade

with cte_extractor_facade() as facade:
    dados = facade.extrair('cte.xml')
    print(f"Dados extraídos: {len(dados)} campos")
'''
    return example_code

# Função de ajuda rápida
def help():
    """Mostra ajuda rápida sobre o sistema."""
    print(f"""
🚚 CT-e EXTRACTOR v{__version__} - AJUDA RÁPIDA

COMPONENTES PRINCIPAIS:
├── CTEFacade          → Interface principal simplificada
├── CTEExtractorFactory → Criação de extratores por versão
├── ExtractorBuilder   → Configuração fluente de extratores
└── StrategyFactory    → Criação de estratégias de validação/cache

USO BÁSICO:
  from cte_extractor import CTEFacade
  facade = CTEFacade()
  dados = facade.extrair('cte.xml')

USO AVANÇADO:
  from cte_extractor import ExtractorBuilder
  extrator = ExtractorBuilder().version('v3').build()

FUNÇÕES DE CONVENIÊNCIA:
  extrair_cte_simples('cte.xml')  → Extração rápida
  validar_cte('cte.xml')          → Validação rápida

Para mais exemplos: show_example()
Para informações da versão: get_version_info()
    """)
