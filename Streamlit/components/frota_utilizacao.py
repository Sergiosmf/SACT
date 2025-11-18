#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componente de Visualização: Frota e Utilização
Monitora uso e desempenho da frota de veículos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Adicionar path do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

from Config.database_config import DATABASE_CONFIG
import psycopg2


class FrotaUtilizacaoViewer:
    """Visualizador de dados de Frota e Utilização"""
    
    def __init__(self):
        self.conn = None
    
    def connect(self):
        """Conecta ao banco de dados"""
        try:
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            return True
        except Exception as e:
            st.error(f"Erro ao conectar ao banco: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.conn:
            self.conn.close()
    
    def query_data(self, query):
        """Executa query e retorna DataFrame"""
        try:
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return pd.DataFrame()
    
    def mostrar_dashboard_principal(self):
        """Dashboard principal com KPIs de frota"""
        st.header("📊 Dashboard de Frota")
        
        df = self.query_data("SELECT * FROM analytics.vw_dashboard_frota")
        
        if not df.empty:
            row = df.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🚛 Total de Veículos", f"{int(row['total_veiculos']):,}")
            with col2:
                st.metric("📦 Total de Viagens", f"{int(row['total_viagens']):,}")
            with col3:
                st.metric("🛣️ KM Total da Frota", f"{int(row['km_total_frota']):,} km")
            with col4:
                st.metric("💰 Faturamento Total", f"R$ {row['faturamento_total']:,.2f}")
    
    def mostrar_rodagem_total(self):
        """Gráfico de rodagem total por veículo"""
        st.subheader("🛣️ Rodagem Total por Veículo")
        
        df = self.query_data("""
            SELECT placa, tipo, km_total, total_viagens, km_medio_viagem
            FROM analytics.vw_rodagem_total
            ORDER BY km_total DESC
            LIMIT 20
        """)
        
        if not df.empty:
            fig = px.bar(
                df,
                x='placa',
                y='km_total',
                title='Top 20 Veículos por Quilometragem Total',
                labels={'placa': 'Placa', 'km_total': 'KM Total'},
                hover_data=['tipo', 'total_viagens', 'km_medio_viagem']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
    
    def mostrar_distribuicao_viagens(self):
        """Distribuição de viagens ao longo do tempo"""
        st.subheader("📊 Distribuição de Viagens por Mês")
        
        # Seletor de veículo
        placas_df = self.query_data("SELECT DISTINCT placa FROM analytics.vw_distribuicao_viagens ORDER BY placa")
        placas = ['Todos'] + placas_df['placa'].tolist()
        
        placa_selecionada = st.selectbox("Selecione um veículo:", placas)
        
        if placa_selecionada == 'Todos':
            query = """
                SELECT mes_ano, SUM(total_viagens) AS total_viagens, SUM(km_mes) AS km_mes
                FROM analytics.vw_distribuicao_viagens
                GROUP BY mes_ano
                ORDER BY mes_ano
            """
        else:
            query = f"""
                SELECT mes_ano, total_viagens, km_mes
                FROM analytics.vw_distribuicao_viagens
                WHERE placa = '{placa_selecionada}'
                ORDER BY mes_ano
            """
        
        df = self.query_data(query)
        
        if not df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(x=df['mes_ano'], y=df['total_viagens'], name="Viagens"),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(x=df['mes_ano'], y=df['km_mes'], name="KM", mode='lines+markers'),
                secondary_y=True
            )
            
            fig.update_layout(title=f"Evolução Mensal - {placa_selecionada}")
            fig.update_xaxes(title_text="Mês")
            fig.update_yaxes(title_text="Viagens", secondary_y=False)
            fig.update_yaxes(title_text="Quilômetros", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
    
    def mostrar_idade_frota(self):
        """Idade média da frota por tipo"""
        st.subheader("📅 Idade da Frota")
        
        df = self.query_data("SELECT * FROM analytics.vw_idade_frota ORDER BY total_veiculos DESC")
        
        if not df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df,
                    x='tipo',
                    y='total_veiculos',
                    title='Quantidade de Veículos por Tipo',
                    labels={'tipo': 'Tipo', 'total_veiculos': 'Total'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    df,
                    x='tipo',
                    y='idade_media_anos',
                    title='Idade Média por Tipo (Anos)',
                    labels={'tipo': 'Tipo', 'idade_media_anos': 'Idade Média'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
    
    def mostrar_tempo_parada(self):
        """Tempo médio de parada entre viagens"""
        st.subheader("⏱️ Tempo de Parada Entre Viagens")
        
        df = self.query_data("""
            SELECT * FROM analytics.vw_tempo_parada
            ORDER BY dias_parada_media
            LIMIT 30
        """)
        
        if not df.empty:
            fig = px.bar(
                df,
                x='placa',
                y='dias_parada_media',
                title='Tempo Médio de Parada (Dias)',
                labels={'placa': 'Placa', 'dias_parada_media': 'Dias Parado'},
                hover_data=['tipo', 'total_intervalos'],
                color='dias_parada_media',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
    
    def mostrar_uso_extremo(self):
        """Veículos com maior e menor uso"""
        st.subheader("🔝 Veículos de Uso Extremo")
        
        df = self.query_data("SELECT * FROM analytics.vw_veiculos_uso_extremo")
        
        if not df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🔥 Maior Uso (Top 10)**")
                df_maior = df[df['rank_maior'] <= 10].sort_values('km_total', ascending=False)
                st.dataframe(df_maior[['placa', 'tipo', 'km_total', 'total_viagens']], use_container_width=True)
            
            with col2:
                st.write("**❄️ Menor Uso (Bottom 10)**")
                df_menor = df[df['rank_menor'] <= 10].sort_values('km_total')
                st.dataframe(df_menor[['placa', 'tipo', 'km_total', 'total_viagens']], use_container_width=True)
    
    def mostrar_performance_frota(self):
        """Performance geral da frota"""
        st.subheader("💼 Performance da Frota")
        
        df = self.query_data("""
            SELECT * FROM analytics.vw_performance_frota
            ORDER BY faturamento_total DESC
            LIMIT 20
        """)
        
        if not df.empty:
            fig = px.scatter(
                df,
                x='km_total',
                y='faturamento_total',
                size='total_viagens',
                color='receita_por_km',
                hover_data=['placa', 'tipo'],
                title='Performance: Quilometragem vs Faturamento',
                labels={
                    'km_total': 'KM Total',
                    'faturamento_total': 'Faturamento (R$)',
                    'receita_por_km': 'R$/KM'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)


def exibir_frota_utilizacao():
    """Função principal para exibir o módulo de Frota e Utilização"""
    st.title("🚚 Frota e Utilização")
    st.markdown("**Monitoramento de uso e desempenho da frota de veículos**")
    st.divider()
    
    viewer = FrotaUtilizacaoViewer()
    
    if not viewer.connect():
        st.error("❌ Não foi possível conectar ao banco de dados")
        return
    
    try:
        # Menu de visualizações
        opcoes = [
            "📊 Dashboard Geral",
            "🛣️ Rodagem Total",
            "📈 Distribuição de Viagens",
            "📅 Idade da Frota",
            "⏱️ Tempo de Parada",
            "🔝 Uso Extremo",
            "💼 Performance"
        ]
        
        escolha = st.selectbox("Selecione uma visualização:", opcoes)
        
        st.divider()
        
        if escolha == "📊 Dashboard Geral":
            viewer.mostrar_dashboard_principal()
        elif escolha == "🛣️ Rodagem Total":
            viewer.mostrar_rodagem_total()
        elif escolha == "📈 Distribuição de Viagens":
            viewer.mostrar_distribuicao_viagens()
        elif escolha == "📅 Idade da Frota":
            viewer.mostrar_idade_frota()
        elif escolha == "⏱️ Tempo de Parada":
            viewer.mostrar_tempo_parada()
        elif escolha == "🔝 Uso Extremo":
            viewer.mostrar_uso_extremo()
        elif escolha == "💼 Performance":
            viewer.mostrar_performance_frota()
    
    finally:
        viewer.disconnect()


if __name__ == "__main__":
    exibir_frota_utilizacao()
