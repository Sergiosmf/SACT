#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Principal de Alimentação do Banco de Dados CT-e
Entry Point - Classe Main simplificada
"""

import os
import sys
import time
from pathlib import Path

# Adicionar diretórios ao path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Imports locais
try:
    from Config.database_config import DATABASE_CONFIG, validate_config
    from Database.managers.database_manager import CTEDatabaseManager
    from Database.managers.file_manager import FileManager
    from Database.managers.stats_manager import StatsManager
    from Database.services.etl_service import ETLService
    from Database.services.quilometragem_service import QuilometragemService
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)


class CTEMainApplication:
    """
    Aplicação principal do sistema CT-e
    Orquestra todos os componentes seguindo arquitetura limpa
    """
    
    def __init__(self):
        """Inicializa a aplicação com todos os managers necessários."""
        self.db_manager = None
        self.file_manager = FileManager()
        self.stats_manager = StatsManager()
        self.etl_service = None
        self.quilometragem_service = QuilometragemService()
        
    def inicializar_sistema(self) -> bool:
        """
        Inicializa e valida todos os componentes do sistema.
        
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        print("🗄️  SISTEMA DE ALIMENTAÇÃO DO BANCO DE DADOS CT-e")
        print("=" * 60)
        print("📝 Este sistema irá processar arquivos XML de CT-e e")
        print("   alimentar PERMANENTEMENTE o banco PostgreSQL")
        
        # 1. Validar configuração do banco
        print("\n📋 1. Validando configuração do banco...")
        config_validation = validate_config()
        
        if not config_validation['valid']:
            print("❌ Configuração inválida:")
            for erro in config_validation['errors']:
                print(f"   • {erro}")
            return False
        
        print("✅ Configuração válida")
        print(f"   🏛️  Banco: {DATABASE_CONFIG['database']}")
        print(f"   🏠 Host: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
        print(f"   👤 Usuário: {DATABASE_CONFIG['user']}")
        
        # 2. Inicializar managers
        try:
            self.db_manager = CTEDatabaseManager(DATABASE_CONFIG)
            self.etl_service = ETLService(self.db_manager, self.stats_manager)
            print("✅ Componentes inicializados com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            return False
    
    def selecionar_e_validar_arquivos(self) -> tuple[Path, int]:
        """
        Seleciona diretório e valida arquivos XML.
        
        Returns:
            tuple: (diretorio_path, total_arquivos)
        """
        print("\n📋 2. Selecionando diretório...")
        diretorio = self.file_manager.selecionar_diretorio()
        
        if not diretorio:
            print("❌ Nenhum diretório selecionado!")
            return None, 0
        
        # Descobrir arquivos XML
        xml_files = self.file_manager.descobrir_arquivos_xml(diretorio)
        total_arquivos = len(xml_files)
        
        print(f"\n✅ Diretório selecionado: {diretorio.name}")
        print(f"📊 Total de arquivos XML: {total_arquivos}")
        
        if total_arquivos == 0:
            print("❌ Nenhum arquivo XML encontrado no diretório!")
            return None, 0
            
        return diretorio, total_arquivos
    
    def configurar_parametros(self) -> float:
        """
        Configura parâmetros de processamento.
        
        Returns:
            float: Custo por quilômetro configurado
        """
        print("\n📋 3. Configurando cálculo de quilometragem...")
        return self.quilometragem_service.configurar_custo_por_km()
    
    def processar_arquivos(self, diretorio: Path, custo_por_km: float) -> bool:
        """
        Processa todos os arquivos XML do diretório.
        
        Args:
            diretorio: Path do diretório com arquivos XML
            custo_por_km: Valor por quilômetro para cálculos
            
        Returns:
            bool: True se processamento foi bem-sucedido
        """
        print("\n📋 4. Processando arquivos...")
        
        # Descobrir arquivos
        xml_files = self.file_manager.descobrir_arquivos_xml(diretorio)
        
        if not xml_files:
            print("❌ Nenhum arquivo XML encontrado!")
            return False
        
        # Processar com ETL Service
        inicio_tempo = time.time()
        sucesso = self.etl_service.processar_lote_arquivos(xml_files, custo_por_km)
        tempo_total = time.time() - inicio_tempo
        
        # Gerar relatório final
        self.stats_manager.imprimir_relatorio_final(tempo_total)
        
        return sucesso
    
    def executar(self) -> bool:
        """
        Executa o fluxo completo da aplicação.
        
        Returns:
            bool: True se execução foi bem-sucedida
        """
        try:
            # 1. Inicializar sistema
            if not self.inicializar_sistema():
                return False
            
            # 2. Selecionar e validar arquivos
            diretorio, total_arquivos = self.selecionar_e_validar_arquivos()
            if not diretorio or total_arquivos == 0:
                return False
            
            # 3. Configurar parâmetros
            custo_por_km = self.configurar_parametros()
            
            # 4. Processar arquivos
            sucesso_processamento = self.processar_arquivos(diretorio, custo_por_km)
            
            # 5. Resultado final
            if sucesso_processamento:
                print("\n🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
                print("✅ Banco de dados alimentado com os dados dos CT-e")
                return True
            else:
                print("\n❌ PROCESSO FALHOU!")
                print("🔧 Verifique os erros e tente novamente")
                return False
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Processo interrompido pelo usuário")
            print("🛑 Operação cancelada")
            return False
            
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            print("🔧 Verifique a configuração e tente novamente")
            return False


def main():
    """Entry point da aplicação."""
    app = CTEMainApplication()
    success = app.executar()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()