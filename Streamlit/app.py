#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import sys
import os
from pathlib import Path
import time
import io
from contextlib import redirect_stdout, redirect_stderr

# Configurar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Importar camada de aplicação
try:
    from Database.main import CTEMainApplication
    from Config.database_config import validate_config, DATABASE_CONFIG
except ImportError as e:
    st.error(f"Erro de importação: {e}")
    st.stop()


class StreamlitCTEInterface:
    def __init__(self):
        self.app = CTEMainApplication()
        
    def setup_page(self):
        st.set_page_config(
            page_title="Sistema CT-e",
            page_icon="🚛",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.title("🚛 Sistema de Processamento CT-e")
        st.markdown("**Alimentação Automática do Banco de Dados PostgreSQL**")
        st.divider()
        
    def run(self):
        self.setup_page()
        
        menu_opcoes = [
            "🔧 Processamento CT-e",
            "📊 Operação de Transporte",
            "💰 Rentabilidade e Custos",
            "🚚 Frota e Utilização",
            "💬 Feedback"
        ]
        
        menu_selecionado = st.selectbox(
            "📋 Selecione uma funcionalidade:",
            menu_opcoes,
            index=0
        )
        
        st.divider()
        
        if menu_selecionado == "🔧 Processamento CT-e":
            self.pagina_processamento()
        elif menu_selecionado == "📊 Operação de Transporte":
            self.pagina_operacao_transporte()
        elif menu_selecionado == "💰 Rentabilidade e Custos":
            self.pagina_rentabilidade_custos()
        elif menu_selecionado == "🚚 Frota e Utilização":
            self.pagina_frota_utilizacao()
        else:
            self.pagina_feedback()
    
    def mostrar_status_configuracao(self):
        """Mostra o status da configuração do sistema"""
        st.subheader("📋 1. Status da Configuração")
        
        with st.container():
            config_validation = validate_config()
            
            if config_validation['valid']:
                st.success("✅ Configuração válida")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"🏛️ **Banco:** {DATABASE_CONFIG['database']}")
                with col2:
                    st.info(f"🏠 **Host:** {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
                with col3:
                    st.info(f"👤 **Usuário:** {DATABASE_CONFIG['user']}")
                
                return True
            else:
                st.error("❌ Configuração inválida")
                for erro in config_validation['errors']:
                    st.error(f"• {erro}")
                return False
    
    def selecionar_diretorio(self):
        """Interface para seleção de diretório"""
        st.subheader("📋 2. Seleção de Diretório")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            diretorio_path = st.text_input(
                "Caminho do diretório com arquivos XML:",
                placeholder="/caminho/para/arquivos/xml",
                help="Digite o caminho completo para o diretório contendo os arquivos CT-e XML",
                key="diretorio_input"
            )
        
        with col2:
            st.write("")
            if st.button("💡 Dica", help="Como encontrar o caminho"):
                st.info("""
                **Como encontrar o caminho do diretório:**
                
                **No macOS:**
                1. Abra o Finder
                2. Navegue até a pasta desejada
                3. Clique com botão direito → "Copiar caminho"
                4. Cole aqui no campo acima
                
                **Exemplo:** `/Users/seu_usuario/Documents/CT-e/mes_10_2025`
                """)
        
        st.write("**Alternativa:** Para teste, você pode fazer upload de alguns arquivos XML:")
        uploaded_files = st.file_uploader(
            "Selecione arquivos XML de CT-e",
            accept_multiple_files=True,
            type=['xml'],
            help="Selecione um ou mais arquivos XML para teste"
        )
        
        if diretorio_path:
            diretorio = Path(diretorio_path)
            
            if diretorio.exists() and diretorio.is_dir():
                xml_files = self.app.file_manager.descobrir_arquivos_xml(diretorio)
                total_arquivos = len(xml_files)
                
                if total_arquivos > 0:
                    st.success(f"✅ Diretório válido: {diretorio.name}")
                    st.info(f"📊 Total de arquivos XML encontrados: {total_arquivos}")
                    
                    if total_arquivos > 0:
                        st.write("**Exemplos de arquivos encontrados:**")
                        for arquivo in xml_files[:5]:
                            st.write(f"• {arquivo.name}")
                        
                        if total_arquivos > 5:
                            st.write(f"... e mais {total_arquivos - 5} arquivos")
                    
                    return diretorio, total_arquivos
                else:
                    st.warning("⚠️ Nenhum arquivo XML encontrado no diretório")
                    return None, 0
            else:
                if diretorio_path:
                    st.error("❌ Diretório não existe ou não é válido")
                return None, 0
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} arquivo(s) selecionado(s) para teste")
            st.info("📝 **Nota:** Esta é uma funcionalidade de teste. Para processamento completo, use um diretório.")
            
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            
            for uploaded_file in uploaded_files:
                file_path = temp_dir / uploaded_file.name
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            
            return temp_dir, len(uploaded_files)
        
        return None, 0
    
    def configurar_parametros(self):
        """Interface para configuração de parâmetros"""
        st.subheader("📋 3. Configuração de Parâmetros")
        
        custo_por_km = st.number_input(
            "Custo por Quilômetro (R$):",
            min_value=0.01,
            value=2.50,
            step=0.01,
            format="%.2f",
            help="Valor em reais por quilômetro para cálculos de rendimento"
        )
        
        st.info(f"💰 Custo configurado: R$ {custo_por_km:.2f} por km")
        
        return custo_por_km
    
    def processar_arquivos_interface(self, diretorio: Path, custo_por_km: float):
        """Interface para processamento de arquivos"""
        st.subheader("📋 4. Processamento de Arquivos")
        
        if st.button("🚀 Iniciar Processamento", type="primary", use_container_width=True):
            return self.executar_processamento(diretorio, custo_por_km)
        
        return False
    
    def executar_processamento(self, diretorio: Path, custo_por_km: float):
        """Executa o processamento dos arquivos com feedback em tempo real"""
        
        status_container = st.container()
        progress_container = st.container()
        log_container = st.container()
        
        with status_container:
            st.info("🔄 Iniciando processamento...")
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        with log_container:
            log_placeholder = st.empty()
        
        try:
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                inicializado = self.app.inicializar_sistema()
            
            logs = output_buffer.getvalue()
            log_placeholder.text_area("📝 Logs do Sistema:", value=logs, height=200)
            
            if not inicializado:
                status_container.error("❌ Falha na inicialização do sistema")
                return False
            
            progress_bar.progress(20)
            status_text.text("✅ Sistema inicializado - Processando arquivos...")
            
            output_buffer = io.StringIO()
            inicio_tempo = time.time()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                sucesso = self.app.processar_arquivos(diretorio, custo_por_km)
            
            logs_processamento = output_buffer.getvalue()
            log_placeholder.text_area("📝 Logs do Sistema:", value=logs + "\n" + logs_processamento, height=300)
            
            tempo_total = time.time() - inicio_tempo
            
            progress_bar.progress(100)
            
            if sucesso:
                status_container.success("🎉 Processamento concluído com sucesso!")
                status_text.text(f"✅ Concluído em {tempo_total:.1f} segundos")
                
                st.subheader("📊 Resumo Final")
                st.metric("⏱️ Tempo Total", f"{tempo_total:.1f}s")
                
                return True
            else:
                status_container.error("❌ Falha no processamento")
                status_text.text("❌ Processo falhou - verifique os logs")
                return False
                
        except Exception as e:
            status_container.error(f"❌ Erro inesperado: {e}")
            return False
    
    def pagina_processamento(self):
        """Página de processamento CT-e (funcionalidade original)"""
        config_valida = self.mostrar_status_configuracao()
        
        if not config_valida:
            st.stop()
        
        st.divider()
        
        diretorio, total_arquivos = self.selecionar_diretorio()
        
        if diretorio and total_arquivos > 0:
            st.divider()
            
            custo_por_km = self.configurar_parametros()
            
            st.divider()
            
            self.processar_arquivos_interface(diretorio, custo_por_km)
    
    def pagina_operacao_transporte(self):
        try:
            sys.path.append(os.path.join(current_dir, 'components'))
            from components.operacao_transporte import exibir_operacao_transporte
            exibir_operacao_transporte()
        except Exception as e:
            st.error(f"Erro: {e}")
    
    def pagina_rentabilidade_custos(self):
        try:
            sys.path.append(os.path.join(current_dir, 'components'))
            from components.rentabilidade_custos import exibir_rentabilidade_custos
            exibir_rentabilidade_custos()
        except Exception as e:
            st.error(f"Erro: {e}")
    
    def pagina_frota_utilizacao(self):
        try:
            sys.path.append(os.path.join(current_dir, 'components'))
            from components.frota_utilizacao import exibir_frota_utilizacao
            exibir_frota_utilizacao()
        except Exception as e:
            st.error(f"Erro: {e}")
    
    def pagina_feedback(self):
        try:
            sys.path.append(os.path.join(current_dir, 'components'))
            from components.feedback import create_feedback_form, display_feedback_stats
            manager = create_feedback_form()
            display_feedback_stats(manager)
        except Exception as e:
            st.error(f"Erro: {e}")


def main():
    interface = StreamlitCTEInterface()
    interface.run()


if __name__ == "__main__":
    main()
