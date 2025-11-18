#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal para execução do CT-e Extractor via python -m cte_extractor

Este arquivo permite executar o módulo diretamente com:
    python -m cte_extractor
"""

import sys
import os

def main():
    """Função principal para demonstração do módulo."""
    print("🚚 CT-e EXTRACTOR - Execução via módulo")
    print("="*50)
    
    try:
        # Importar componentes do próprio módulo
        from . import (
            __version__, __title__, __description__,
            get_version_info, show_example, help
        )
        
        print(f"✅ {__title__} v{__version__}")
        print(f"📋 {__description__}")
        
        # Mostrar informações
        print("\n" + "="*50)
        help()
        
        # Testar importações básicas
        print("\n" + "="*50)
        print("TESTANDO COMPONENTES:")
        print("="*50)
        
        from .facade import CTEFacade
        print("✅ CTEFacade disponível")
        
        from .factory import CTEExtractorFactory, ExtractorBuilder
        print("✅ Factory e Builder disponíveis")
        
        from .models import CTe, Pessoa, Endereco
        print("✅ Modelos de dados disponíveis")
        
        print("\n🎉 Módulo funcionando corretamente!")
        
        print("\n" + "="*50)
        print("PRÓXIMOS PASSOS:")
        print("="*50)
        print("1. Para usar o módulo, importe em seu código Python:")
        print("   from cte_extractor import CTEFacade")
        print("   facade = CTEFacade()")
        print("\n2. Para ver exemplos detalhados:")
        print("   python main.py")
        print("\n3. Para desenvolvimento:")
        print("   Execute os testes em tests/")
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todos os arquivos do módulo estão presentes")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
