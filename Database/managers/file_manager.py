# -*- coding: utf-8 -*-
"""
File Manager - Gerenciamento de arquivos e interface de usuário
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional


class FileManager:
    """
    Manager para operações de arquivo e interface de usuário.
    Implementa Single Responsibility Principle.
    """
    
    def __init__(self):
        """Inicializa o manager de arquivos."""
        pass
    
    def selecionar_diretorio(self) -> Optional[Path]:
        """
        Abre interface para seleção de diretório.
        
        Returns:
            Path do diretório selecionado ou None
        """
        print("\n" + "=" * 60)
        print("SELEÇÃO DE DIRETÓRIO")
        print("=" * 60)
        print("📁 Abrindo seletor de diretório...")
        
        try:
            # Configurar interface tkinter
            root = tk.Tk()
            root.withdraw()  # Esconder janela principal
            root.attributes('-topmost', True)  # Trazer para frente
            
            # Abrir dialog de seleção
            caminho = filedialog.askdirectory(
                title="Selecione o diretório com arquivos XML de CT-e",
                mustexist=True
            )
            
            root.destroy()  # Limpar recursos
            
            if caminho:
                path_obj = Path(caminho)
                print(f"✅ Diretório selecionado: {path_obj.name}")
                print(f"📂 Caminho completo: {path_obj}")
                return path_obj
            else:
                print("❌ Nenhum diretório selecionado.")
                return None
                
        except Exception as e:
            print(f"❌ Erro na seleção de diretório: {e}")
            return None
    
    def descobrir_arquivos_xml(self, diretorio: Path) -> List[Path]:
        """
        Descobre todos os arquivos XML no diretório.
        
        Args:
            diretorio: Path do diretório para buscar
            
        Returns:
            Lista de arquivos XML encontrados
        """
        if not diretorio.exists():
            print(f"❌ Diretório não existe: {diretorio}")
            return []
        
        if not diretorio.is_dir():
            print(f"❌ Caminho não é um diretório: {diretorio}")
            return []
        
        # Buscar arquivos XML
        xml_files = list(diretorio.glob("*.xml"))
        xml_files.extend(diretorio.glob("*.XML"))  # Case insensitive
        
        # Remover duplicatas e ordenar
        xml_files = sorted(set(xml_files))
        
        print(f"📊 Arquivos XML encontrados: {len(xml_files)}")
        
        if xml_files:
            print(f"📄 Primeiro arquivo: {xml_files[0].name}")
            print(f"📄 Último arquivo: {xml_files[-1].name}")
        
        return xml_files
    
    def validar_arquivo_xml(self, arquivo: Path) -> bool:
        """
        Valida se arquivo XML está acessível.
        
        Args:
            arquivo: Path do arquivo XML
            
        Returns:
            True se arquivo é válido
        """
        try:
            if not arquivo.exists():
                print(f"❌ Arquivo não existe: {arquivo.name}")
                return False
            
            if not arquivo.is_file():
                print(f"❌ Não é um arquivo: {arquivo.name}")
                return False
            
            if arquivo.stat().st_size == 0:
                print(f"❌ Arquivo vazio: {arquivo.name}")
                return False
            
            # Tentar ler primeiros bytes para verificar acesso
            with open(arquivo, 'rb') as f:
                header = f.read(100)
                if not header:
                    print(f"❌ Erro ao ler arquivo: {arquivo.name}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação do arquivo {arquivo.name}: {e}")
            return False
    
    def listar_arquivos_detalhado(self, arquivos: List[Path]) -> None:
        """
        Lista arquivos com informações detalhadas.
        
        Args:
            arquivos: Lista de arquivos para listar
        """
        if not arquivos:
            print("📄 Nenhum arquivo para listar")
            return
        
        print(f"\n📋 LISTA DETALHADA DE ARQUIVOS ({len(arquivos)} arquivos):")
        print("-" * 80)
        
        total_size = 0
        
        for i, arquivo in enumerate(arquivos, 1):
            try:
                size = arquivo.stat().st_size
                size_mb = size / (1024 * 1024)
                total_size += size
                
                print(f"{i:3d}. {arquivo.name} ({size_mb:.2f} MB)")
                
                # Mostrar apenas primeiros 20 arquivos para não poluir console
                if i >= 20 and len(arquivos) > 20:
                    restantes = len(arquivos) - 20
                    print(f"     ... e mais {restantes} arquivos")
                    break
                    
            except Exception as e:
                print(f"{i:3d}. {arquivo.name} (ERRO: {e})")
        
        total_mb = total_size / (1024 * 1024)
        print("-" * 80)
        print(f"📊 Total: {len(arquivos)} arquivos, {total_mb:.2f} MB")
    
    def confirmar_processamento(self, total_arquivos: int) -> bool:
        """
        Solicita confirmação do usuário para processamento.
        
        Args:
            total_arquivos: Número total de arquivos
            
        Returns:
            True se usuário confirmou
        """
        try:
            root = tk.Tk()
            root.withdraw()
            
            mensagem = (
                f"Processar {total_arquivos} arquivos XML?\n\n"
                f"Esta operação irá:\n"
                f"• Extrair dados dos CT-e\n"
                f"• Inserir no banco PostgreSQL\n"
                f"• Criar/atualizar views analíticas\n\n"
                f"Continuar?"
            )
            
            resposta = messagebox.askyesno(
                "Confirmar Processamento",
                mensagem,
                icon='question'
            )
            
            root.destroy()
            return resposta
            
        except Exception as e:
            print(f"❌ Erro na confirmação: {e}")
            # Se der erro, assumir confirmação via console
            resposta = input(f"\n🤔 Processar {total_arquivos} arquivos? (s/n): ")
            return resposta.lower().startswith('s')
    
    def criar_backup_lista_arquivos(self, arquivos: List[Path], 
                                   diretorio_output: Path) -> Optional[Path]:
        """
        Cria arquivo de backup com lista de arquivos processados.
        
        Args:
            arquivos: Lista de arquivos processados
            diretorio_output: Diretório para salvar backup
            
        Returns:
            Path do arquivo de backup criado
        """
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = diretorio_output / f"arquivos_processados_{timestamp}.txt"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"# Lista de arquivos processados\n")
                f.write(f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"# Total: {len(arquivos)} arquivos\n\n")
                
                for i, arquivo in enumerate(arquivos, 1):
                    f.write(f"{i:4d}. {arquivo.name}\n")
            
            print(f"📄 Backup criado: {backup_file.name}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return None