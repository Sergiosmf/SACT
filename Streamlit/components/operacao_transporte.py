#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componente de Visualização: Operação de Transporte
Métricas e análises sobre volume e perfil das viagens
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import psycopg2
from Config.database_config import DATABASE_CONFIG


class OperacaoTransporteViewer:
    """Gerenciador de visualizações de Operação de Transporte"""
    
    def __init__(self):
        """Inicializa o visualizador"""
        self.conn = None
        
    def conectar(self) -> bool:
        """Estabelece conexão com o banco de dados"""
        try:
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco: {e}")
            return False
    
    def desconectar(self):
        """Fecha conexão com o banco"""
        if self.conn:
            self.conn.close()
    
    def executar_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Executa uma query e retorna um DataFrame
        
        Args:
            query: SQL query a executar
            
        Returns:
            DataFrame com os resultados ou None em caso de erro
        """
        try:
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            st.error(f"❌ Erro ao executar query: {e}")
            return None
    
    def mostrar_dashboard_principal(self):
        """Exibe o dashboard principal com KPIs"""
        st.header("📊 Dashboard de Operação de Transporte")
        st.markdown("---")
        
        # Carregar dados do dashboard
        df = self.executar_query("SELECT * FROM analytics.vw_dashboard_operacao")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        dados = df.iloc[0]
        
        # KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📋 Total de CT-es",
                f"{dados['total_ctes']:,}",
                help="Número total de Conhecimentos de Transporte emitidos"
            )
        
        with col2:
            st.metric(
                "🚛 Veículos",
                f"{dados['total_veiculos']:,}",
                help="Número de veículos diferentes utilizados"
            )
        
        with col3:
            st.metric(
                "📍 Origens",
                f"{dados['total_origens']:,}",
                help="Número de municípios de origem diferentes"
            )
        
        with col4:
            st.metric(
                "🎯 Destinos",
                f"{dados['total_destinos']:,}",
                help="Número de municípios de destino diferentes"
            )
        
        st.markdown("---")
        
        # Métricas financeiras
        col1, col2, col3 = st.columns(3)
        
        with col1:
            receita = float(dados['receita_total']) if dados['receita_total'] else 0
            st.metric(
                "💰 Receita Total",
                f"R$ {receita:,.2f}",
                help="Valor total de frete acumulado"
            )
        
        with col2:
            frete_medio = float(dados['frete_medio']) if dados['frete_medio'] else 0
            st.metric(
                "📊 Frete Médio",
                f"R$ {frete_medio:,.2f}",
                help="Valor médio de frete por viagem"
            )
        
        with col3:
            taxa_km = float(dados['taxa_media_km']) if dados['taxa_media_km'] else 0
            st.metric(
                "🛣️ Taxa Média/km",
                f"R$ {taxa_km:.2f}",
                help="Valor médio cobrado por quilômetro"
            )
        
        st.markdown("---")
        
        # Métricas de distância
        col1, col2, col3 = st.columns(3)
        
        with col1:
            km_medio = float(dados['km_medio']) if dados['km_medio'] else 0
            st.metric(
                "📏 Distância Média",
                f"{km_medio:,.0f} km",
                help="Quilometragem média por viagem"
            )
        
        with col2:
            km_total = float(dados['km_total']) if dados['km_total'] else 0
            st.metric(
                "🌍 Distância Total",
                f"{km_total:,.0f} km",
                help="Quilometragem total percorrida"
            )
        
        with col3:
            if dados['produto_mais_transportado']:
                st.metric(
                    "📦 Produto Top",
                    dados['produto_mais_transportado'][:20],
                    help="Produto predominante mais transportado"
                )
            else:
                st.metric("📦 Produto Top", "N/A")
        
        # Período dos dados
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📅 **Primeira Data:** {dados['primeira_data']}")
        
        with col2:
            st.info(f"📅 **Última Data:** {dados['ultima_data']}")
    
    def mostrar_ctes_por_mes(self):
        """Exibe análise temporal de CT-es por mês"""
        st.subheader("📅 Total de CT-es Emitidos por Mês")
        
        df = self.executar_query("""
            SELECT * FROM analytics.vw_ctes_por_mes 
            ORDER BY ano, mes
        """)
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Gráfico de barras
        fig = px.bar(
            df,
            x='ano_mes',
            y='total_ctes',
            title='Evolução Mensal de CT-es',
            labels={'ano_mes': 'Mês/Ano', 'total_ctes': 'Total de CT-es'},
            text='total_ctes',
            color='total_ctes',
            color_continuous_scale='Blues'
        )
        
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['receita_total'] = df_display['receita_total'].apply(lambda x: f"R$ {x:,.2f}")
            df_display['frete_medio'] = df_display['frete_medio'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def mostrar_top_origens_destinos(self):
        """Exibe top 10 origens e destinos"""
        st.subheader("📍 Municípios Mais Frequentes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔵 Top 10 Origens")
            df_origens = self.executar_query("SELECT * FROM analytics.vw_top_origens")
            
            if df_origens is not None and not df_origens.empty:
                # Gráfico
                fig = px.bar(
                    df_origens,
                    x='total_viagens',
                    y='origem_completa',
                    orientation='h',
                    title='Municípios de Origem',
                    labels={'total_viagens': 'Total de Viagens', 'origem_completa': 'Origem'},
                    text='total_viagens',
                    color='total_viagens',
                    color_continuous_scale='Blues'
                )
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela
                with st.expander("📊 Detalhes"):
                    st.dataframe(df_origens, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### 🟢 Top 10 Destinos")
            df_destinos = self.executar_query("SELECT * FROM analytics.vw_top_destinos")
            
            if df_destinos is not None and not df_destinos.empty:
                # Gráfico
                fig = px.bar(
                    df_destinos,
                    x='total_viagens',
                    y='destino_completo',
                    orientation='h',
                    title='Municípios de Destino',
                    labels={'total_viagens': 'Total de Viagens', 'destino_completo': 'Destino'},
                    text='total_viagens',
                    color='total_viagens',
                    color_continuous_scale='Greens'
                )
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela
                with st.expander("📊 Detalhes"):
                    st.dataframe(df_destinos, use_container_width=True, hide_index=True)
    
    def mostrar_analise_distancia(self):
        """Exibe análise de distâncias percorridas"""
        st.subheader("📏 Análise de Distâncias Percorridas")
        
        df = self.executar_query("SELECT * FROM analytics.vw_distancia_media")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        dados = df.iloc[0]
        
        # Estatísticas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Média", f"{float(dados['distancia_media_km']):,.0f} km")
        
        with col2:
            st.metric("📈 Mediana", f"{float(dados['mediana_km']):,.0f} km")
        
        with col3:
            st.metric("⬆️ Máxima", f"{float(dados['distancia_maxima_km']):,.0f} km")
        
        with col4:
            st.metric("📉 Desvio Padrão", f"{float(dados['desvio_padrao_km']):,.0f} km")
        
        st.markdown("---")
        
        # Distribuição por faixas
        st.markdown("#### 📊 Distribuição por Faixas de Distância")
        
        faixas = {
            'Até 100 km': int(dados['ate_100km']),
            '101-300 km': int(dados['de_101_a_300km']),
            '301-500 km': int(dados['de_301_a_500km']),
            '501-1000 km': int(dados['de_501_a_1000km']),
            'Acima de 1000 km': int(dados['acima_1000km'])
        }
        
        df_faixas = pd.DataFrame(list(faixas.items()), columns=['Faixa', 'Viagens'])
        
        # Gráfico de pizza
        fig = px.pie(
            df_faixas,
            values='Viagens',
            names='Faixa',
            title='Distribuição de Viagens por Faixa de Distância',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label+value')
        fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def mostrar_viagens_por_veiculo(self):
        """Exibe análise de viagens por veículo"""
        st.subheader("🚛 Viagens por Veículo")
        
        # Filtro de número de veículos
        num_veiculos = st.slider(
            "Número de veículos a exibir:",
            min_value=5,
            max_value=50,
            value=20,
            step=5
        )
        
        df = self.executar_query(f"""
            SELECT * FROM analytics.vw_viagens_por_veiculo 
            LIMIT {num_veiculos}
        """)
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Gráfico de barras
        fig = px.bar(
            df,
            x='placa',
            y='total_viagens',
            title=f'Top {num_veiculos} Veículos por Número de Viagens',
            labels={'placa': 'Placa', 'total_viagens': 'Total de Viagens'},
            text='total_viagens',
            color='total_viagens',
            color_continuous_scale='Viridis'
        )
        
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['receita_total'] = df_display['receita_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['frete_medio_por_viagem'] = df_display['frete_medio_por_viagem'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['km_medio_por_viagem'] = df_display['km_medio_por_viagem'].apply(lambda x: f"{float(x):,.0f} km")
            df_display['km_total_percorrido'] = df_display['km_total_percorrido'].apply(lambda x: f"{float(x):,.0f} km")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def mostrar_produtos_predominantes(self):
        """Exibe análise de produtos transportados"""
        st.subheader("📦 Produtos Predominantes Transportados")
        
        # Filtro
        num_produtos = st.slider(
            "Número de produtos a exibir:",
            min_value=5,
            max_value=20,
            value=10,
            step=5
        )
        
        df = self.executar_query(f"""
            SELECT * FROM analytics.vw_produtos_predominantes 
            LIMIT {num_produtos}
        """)
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Gráfico de barras horizontais
        fig = px.bar(
            df,
            x='total_ctes',
            y='produto',
            orientation='h',
            title=f'Top {num_produtos} Produtos Mais Transportados',
            labels={'total_ctes': 'Total de CT-es', 'produto': 'Produto'},
            text='total_ctes',
            color='receita_total',
            color_continuous_scale='Oranges'
        )
        
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['quantidade_total'] = df_display['quantidade_total'].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else "N/A")
            df_display['peso_total_kg'] = df_display['peso_total_kg'].apply(lambda x: f"{float(x):,.2f} kg" if pd.notna(x) else "N/A")
            df_display['peso_medio_kg'] = df_display['peso_medio_kg'].apply(lambda x: f"{float(x):,.2f} kg" if pd.notna(x) else "N/A")
            df_display['receita_total'] = df_display['receita_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['frete_medio'] = df_display['frete_medio'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['receita_por_kg'] = df_display['receita_por_kg'].apply(lambda x: f"R$ {float(x):.2f}/kg" if pd.notna(x) and float(x) > 0 else "N/A")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def mostrar_taxa_frete_km(self):
        """Exibe análise da taxa de frete por quilômetro"""
        st.subheader("💰 Taxa Média de Frete por Quilômetro")
        
        df = self.executar_query("SELECT * FROM analytics.vw_taxa_frete_km")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        dados = df.iloc[0]
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            taxa_media = float(dados['taxa_media_por_km']) if pd.notna(dados['taxa_media_por_km']) else 0
            st.metric("📊 Taxa Média", f"R$ {taxa_media:.2f}/km")
        
        with col2:
            taxa_mediana = float(dados['taxa_mediana_por_km']) if pd.notna(dados['taxa_mediana_por_km']) else 0
            st.metric("📈 Taxa Mediana", f"R$ {taxa_mediana:.2f}/km")
        
        with col3:
            taxa_min = float(dados['taxa_minima_por_km']) if pd.notna(dados['taxa_minima_por_km']) else 0
            st.metric("⬇️ Taxa Mínima", f"R$ {taxa_min:.2f}/km")
        
        with col4:
            taxa_max = float(dados['taxa_maxima_por_km']) if pd.notna(dados['taxa_maxima_por_km']) else 0
            st.metric("⬆️ Taxa Máxima", f"R$ {taxa_max:.2f}/km")
        
        st.markdown("---")
        
        # Taxa por faixa de distância
        st.markdown("#### 📊 Taxa por Faixa de Distância")
        
        faixas_taxa = {
            'Até 100 km': float(dados['taxa_ate_100km']) if pd.notna(dados['taxa_ate_100km']) else 0,
            '101-300 km': float(dados['taxa_101_300km']) if pd.notna(dados['taxa_101_300km']) else 0,
            '301-500 km': float(dados['taxa_301_500km']) if pd.notna(dados['taxa_301_500km']) else 0,
            '501-1000 km': float(dados['taxa_501_1000km']) if pd.notna(dados['taxa_501_1000km']) else 0,
            'Acima de 1000 km': float(dados['taxa_acima_1000km']) if pd.notna(dados['taxa_acima_1000km']) else 0
        }
        
        df_faixas = pd.DataFrame(list(faixas_taxa.items()), columns=['Faixa', 'Taxa (R$/km)'])
        
        # Gráfico de barras
        fig = px.bar(
            df_faixas,
            x='Faixa',
            y='Taxa (R$/km)',
            title='Taxa de Frete por Faixa de Distância',
            text='Taxa (R$/km)',
            color='Taxa (R$/km)',
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        💡 **Análise:** Normalmente, viagens mais longas tendem a ter uma taxa por km menor 
        devido à diluição dos custos fixos ao longo de uma distância maior.
        """)


def exibir_operacao_transporte():
    """Função principal para exibir todas as visualizações de operação de transporte"""
    viewer = OperacaoTransporteViewer()
    
    if not viewer.conectar():
        st.error("❌ Não foi possível conectar ao banco de dados")
        return
    
    try:
        # Dashboard principal
        viewer.mostrar_dashboard_principal()
        
        st.markdown("---")
        st.markdown("---")
        
        # CT-es por mês
        viewer.mostrar_ctes_por_mes()
        
        st.markdown("---")
        
        # Top origens e destinos
        viewer.mostrar_top_origens_destinos()
        
        st.markdown("---")
        
        # Análise de distâncias
        viewer.mostrar_analise_distancia()
        
        st.markdown("---")
        
        # Viagens por veículo
        viewer.mostrar_viagens_por_veiculo()
        
        st.markdown("---")
        
        # Produtos predominantes
        viewer.mostrar_produtos_predominantes()
        
        st.markdown("---")
        
        # Taxa de frete por km
        viewer.mostrar_taxa_frete_km()
        
    finally:
        viewer.desconectar()
