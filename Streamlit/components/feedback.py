#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componente de Feedback do Usuário
Sistema para coletar sugestões, bugs e melhorias
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import os


class FeedbackManager:
    """Gerenciador do sistema de feedback"""
    
    def __init__(self):
        """Inicializa o gerenciador de feedback"""
        self.feedback_dir = Path(__file__).parent.parent / "feedback"
        self.feedback_dir.mkdir(exist_ok=True)
    
    def save_feedback(self, texto: str, categoria: str, nome: str = "Anônimo") -> bool:
        """
        Salva o feedback em um arquivo .txt
        
        Args:
            texto: Texto do feedback
            categoria: Categoria do feedback
            nome: Nome do usuário (ou "Anônimo")
            
        Returns:
            True se salvou com sucesso
        """
        try:
            # Criar nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feedback_{timestamp}.txt"
            filepath = self.feedback_dir / filename
            
            # Criar conteúdo do arquivo
            conteudo = f"""
================================================================================
FEEDBACK DO USUÁRIO - Sistema CT-e
================================================================================

📅 Data/Hora: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
👤 Usuário: {nome}
🏷️  Categoria: {categoria}

--------------------------------------------------------------------------------
📝 FEEDBACK:
--------------------------------------------------------------------------------

{texto}

================================================================================
Arquivo: {filename}
================================================================================
"""
            
            # Salvar arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao salvar feedback: {e}")
            return False
    
    def get_feedback_count(self) -> int:
        """Retorna o número total de feedbacks salvos"""
        try:
            return len(list(self.feedback_dir.glob("feedback_*.txt")))
        except:
            return 0
    
    def contar_feedbacks(self) -> int:
        """Alias para get_feedback_count (compatibilidade)"""
        return self.get_feedback_count()
    
    def get_recent_feedbacks(self, limit: int = 10) -> list:
        """
        Retorna os feedbacks mais recentes
        
        Args:
            limit: Número máximo de feedbacks a retornar
            
        Returns:
            Lista de dicionários com informações dos feedbacks
        """
        try:
            arquivos = sorted(
                self.feedback_dir.glob("feedback_*.txt"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            feedbacks = []
            for arquivo in arquivos:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    feedbacks.append({
                        'arquivo': arquivo.name,
                        'conteudo': conteudo,
                        'data': datetime.fromtimestamp(arquivo.stat().st_mtime)
                    })
            
            return feedbacks
        except:
            return []
    
    def get_latest_feedbacks(self, limit: int = 10) -> list:
        """
        Retorna os feedbacks mais recentes (alias para compatibilidade)
        
        Args:
            limit: Número máximo de feedbacks a retornar
            
        Returns:
            Lista de dicionários com informações dos feedbacks
        """
        try:
            arquivos = sorted(
                self.feedback_dir.glob("feedback_*.txt"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            feedbacks = []
            for arquivo in arquivos:
                stat = arquivo.stat()
                feedbacks.append({
                    'filename': arquivo.name,
                    'data': datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                    'tamanho': f"{stat.st_size} bytes"
                })
            
            return feedbacks
        except:
            return []
    
    def obter_categorias_stats(self) -> dict:
        """Retorna estatísticas por categoria"""
        stats = {
            "🐛 Bug / Erro": 0,
            "✨ Nova Funcionalidade": 0,
            "🔧 Melhoria": 0,
            "📚 Documentação": 0,
            "💡 Sugestão": 0,
            "❓ Dúvida": 0,
            "👍 Elogio": 0,
            "📊 Outro": 0
        }
        
        try:
            for arquivo in self.feedback_dir.glob("feedback_*.txt"):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    for categoria in stats.keys():
                        if f"🏷️  Categoria: {categoria}" in conteudo:
                            stats[categoria] += 1
                            break
        except:
            pass
        
        return stats


def create_feedback_form() -> FeedbackManager:
    """
    Cria e exibe o formulário de feedback
    
    Returns:
        Instância do FeedbackManager
    """
    st.header("💬 Feedback do Usuário")
    st.markdown("""
    Sua opinião é muito importante! Use este espaço para:
    - 🐛 Reportar bugs ou erros
    - ✨ Sugerir novas funcionalidades
    - 🔧 Propor melhorias
    - 💡 Compartilhar ideias
    """)
    
    st.divider()
    
    manager = FeedbackManager()
    
    # Formulário
    with st.form("feedback_form", clear_on_submit=True):
        st.subheader("📝 Seu Feedback")
        
        # Nome (opcional)
        col1, col2 = st.columns([3, 1])
        with col1:
            nome = st.text_input(
                "Nome (opcional):",
                placeholder="Digite seu nome ou deixe em branco para ser anônimo",
                help="Deixe vazio se preferir feedback anônimo"
            )
        
        with col2:
            anonimo = st.checkbox("Anônimo", value=False)
        
        # Categoria
        categoria = st.selectbox(
            "Categoria do Feedback:",
            [
                "🐛 Bug / Erro",
                "✨ Nova Funcionalidade",
                "🔧 Melhoria",
                "📚 Documentação",
                "💡 Sugestão",
                "❓ Dúvida",
                "👍 Elogio",
                "📊 Outro"
            ],
            help="Selecione a categoria que melhor descreve seu feedback"
        )
        
        # Texto do feedback
        texto = st.text_area(
            "Descreva seu feedback:",
            placeholder="Seja o mais detalhado possível. Se for um bug, descreva os passos para reproduzi-lo.",
            height=200,
            help="Mínimo de 10 caracteres"
        )
        
        # Botão de envio
        submitted = st.form_submit_button("📨 Enviar Feedback", use_container_width=True, type="primary")
        
        if submitted:
            # Validações
            if not texto or len(texto.strip()) < 10:
                st.error("❌ Por favor, escreva um feedback com pelo menos 10 caracteres.")
            else:
                # Definir nome (anônimo ou não)
                nome_final = "Anônimo" if anonimo or not nome.strip() else nome.strip()
                
                # Salvar feedback
                if manager.save_feedback(texto=texto.strip(), categoria=categoria, nome=nome_final):
                    st.success("🎉 Feedback enviado com sucesso! Obrigado pela contribuição!")
                    st.balloons()
                else:
                    st.error("❌ Erro ao salvar feedback. Tente novamente.")
    
    return manager


def display_feedback_stats(manager: FeedbackManager):
    """
    Exibe estatísticas dos feedbacks recebidos
    
    Args:
        manager: Instância do FeedbackManager
    """
    st.divider()
    st.subheader("📊 Estatísticas de Feedbacks")
    
    total = manager.contar_feedbacks()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "📬 Total de Feedbacks Recebidos",
            total,
            help="Número total de feedbacks salvos"
        )
    
    with col2:
        st.info("💾 Feedbacks salvos em: `Streamlit/feedback/`")
    
    # Estatísticas por categoria
    if total > 0:
        st.markdown("#### 📈 Por Categoria:")
        stats = manager.obter_categorias_stats()
        
        # Exibir em colunas
        cols = st.columns(4)
        for idx, (categoria, count) in enumerate(stats.items()):
            with cols[idx % 4]:
                if count > 0:
                    st.metric(categoria, count)
