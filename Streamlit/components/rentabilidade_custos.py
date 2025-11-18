#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Componente de Visualização: Rentabilidade e Custos
Métricas e análises sobre desempenho financeiro da operação
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import psycopg2
from Config.database_config import DATABASE_CONFIG


class RentabilidadeCustosViewer:
    """Gerenciador de visualizações de Rentabilidade e Custos"""
    
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
        """Exibe o dashboard financeiro principal com KPIs"""
        st.header("💰 Dashboard de Rentabilidade e Custos")
        st.markdown("---")
        
        # Carregar dados do dashboard
        df = self.executar_query("SELECT * FROM analytics.vw_dashboard_financeiro")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        dados = df.iloc[0]
        
        # KPIs principais - Linha 1
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            receita = float(dados['receita_total']) if dados['receita_total'] else 0
            st.metric(
                "💰 Receita Total",
                f"R$ {receita:,.2f}",
                help="Valor total de frete acumulado"
            )
        
        with col2:
            ticket = float(dados['ticket_medio']) if dados['ticket_medio'] else 0
            st.metric(
                "🎫 Ticket Médio",
                f"R$ {ticket:,.2f}",
                help="Valor médio por viagem"
            )
        
        with col3:
            custo = float(dados['custo_estimado_total']) if dados['custo_estimado_total'] else 0
            st.metric(
                "💸 Custo Estimado",
                f"R$ {custo:,.2f}",
                help="Custo operacional estimado total (R$ 2.50/km)"
            )
        
        with col4:
            margem = float(dados['margem_bruta_total']) if dados['margem_bruta_total'] else 0
            st.metric(
                "📊 Margem Bruta",
                f"R$ {margem:,.2f}",
                help="Receita - Custo Operacional"
            )
        
        st.markdown("---")
        
        # KPIs secundários - Linha 2
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            margem_pct = float(dados['margem_percentual']) if dados['margem_percentual'] else 0
            delta_color = "normal" if margem_pct >= 25 else "inverse"
            st.metric(
                "📈 Margem %",
                f"{margem_pct:.1f}%",
                help="Percentual de margem sobre receita"
            )
        
        with col2:
            receita_mensal = float(dados['receita_media_mensal']) if dados['receita_media_mensal'] else 0
            st.metric(
                "📅 Receita Média/Mês",
                f"R$ {receita_mensal:,.2f}",
                help="Média de receita mensal"
            )
        
        with col3:
            clientes_rem = int(dados['total_clientes_remetentes']) if dados['total_clientes_remetentes'] else 0
            st.metric(
                "👥 Clientes Remetentes",
                f"{clientes_rem:,}",
                help="Total de clientes remetentes"
            )
        
        with col4:
            clientes_dest = int(dados['total_clientes_destinatarios']) if dados['total_clientes_destinatarios'] else 0
            st.metric(
                "🎯 Clientes Destinatários",
                f"{clientes_dest:,}",
                help="Total de clientes destinatários"
            )
        
        # Melhor mês
        if dados['melhor_mes']:
            st.success(f"🏆 **Melhor Mês:** {dados['melhor_mes']}")
    
    def mostrar_receita_mensal(self):
        """Exibe análise de receita mensal"""
        st.subheader("📅 Receita Total de Frete por Mês")
        
        df = self.executar_query("""
            SELECT * FROM analytics.vw_receita_mensal 
            ORDER BY ano, mes
        """)
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Calcular crescimento percentual
        df['crescimento_pct'] = ((df['receita_total'] - df['receita_mes_anterior']) / 
                                  df['receita_mes_anterior'] * 100).fillna(0)
        
        # Gráfico de linha + barras
        fig = go.Figure()
        
        # Barras de receita
        fig.add_trace(go.Bar(
            x=df['ano_mes'],
            y=df['receita_total'],
            name='Receita',
            marker_color='lightblue',
            text=df['receita_total'].apply(lambda x: f'R$ {x:,.0f}'),
            textposition='outside'
        ))
        
        # Linha de crescimento
        fig.add_trace(go.Scatter(
            x=df['ano_mes'],
            y=df['crescimento_pct'],
            name='Crescimento %',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Evolução Mensal de Receita e Crescimento',
            xaxis_title='Mês/Ano',
            yaxis_title='Receita (R$)',
            yaxis2=dict(
                title='Crescimento (%)',
                overlaying='y',
                side='right'
            ),
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['receita_total'] = df_display['receita_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['receita_media'] = df_display['receita_media'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['receita_por_km'] = df_display['receita_por_km'].apply(lambda x: f"R$ {float(x):.2f}/km")
            df_display['crescimento_pct'] = df_display['crescimento_pct'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_display[['mes_nome', 'total_ctes', 'receita_total', 'receita_media', 
                                     'receita_por_km', 'crescimento_pct']], 
                        use_container_width=True, hide_index=True)
    
    def mostrar_ticket_medio(self):
        """Exibe análise de ticket médio"""
        st.subheader("🎫 Ticket Médio por Viagem")
        
        df = self.executar_query("SELECT * FROM analytics.vw_ticket_medio")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        dados = df.iloc[0]
        
        # Estatísticas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ticket_medio = float(dados['ticket_medio']) if pd.notna(dados['ticket_medio']) else 0
            st.metric("📊 Ticket Médio", f"R$ {ticket_medio:,.2f}")
        
        with col2:
            ticket_mediano = float(dados['ticket_mediano']) if pd.notna(dados['ticket_mediano']) else 0
            st.metric("📈 Ticket Mediano", f"R$ {ticket_mediano:,.2f}")
        
        with col3:
            ticket_min = float(dados['ticket_minimo']) if pd.notna(dados['ticket_minimo']) else 0
            st.metric("⬇️ Mínimo", f"R$ {ticket_min:,.2f}")
        
        with col4:
            ticket_max = float(dados['ticket_maximo']) if pd.notna(dados['ticket_maximo']) else 0
            st.metric("⬆️ Máximo", f"R$ {ticket_max:,.2f}")
        
        st.markdown("---")
        
        # Distribuição por faixas de valor
        st.markdown("#### 📊 Distribuição por Faixas de Valor")
        
        faixas_valor = {
            'Até R$ 100': int(dados['ate_100']),
            'R$ 101 - 500': int(dados['de_101_a_500']),
            'R$ 501 - 1.000': int(dados['de_501_a_1000']),
            'R$ 1.001 - 3.000': int(dados['de_1001_a_3000']),
            'Acima de R$ 3.000': int(dados['acima_3000'])
        }
        
        df_faixas = pd.DataFrame(list(faixas_valor.items()), columns=['Faixa', 'Viagens'])
        
        # Gráfico de pizza
        fig = px.pie(
            df_faixas,
            values='Viagens',
            names='Faixa',
            title='Distribuição de Viagens por Faixa de Valor',
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label+value')
        fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Ticket médio por faixa de distância
        st.markdown("#### 🛣️ Ticket Médio por Faixa de Distância")
        
        faixas_ticket = {
            'Até 100 km': float(dados['ticket_medio_ate_100km']) if pd.notna(dados['ticket_medio_ate_100km']) else 0,
            '101-300 km': float(dados['ticket_medio_101_300km']) if pd.notna(dados['ticket_medio_101_300km']) else 0,
            '301-500 km': float(dados['ticket_medio_301_500km']) if pd.notna(dados['ticket_medio_301_500km']) else 0,
            '501-1000 km': float(dados['ticket_medio_501_1000km']) if pd.notna(dados['ticket_medio_501_1000km']) else 0,
            'Acima de 1000 km': float(dados['ticket_medio_acima_1000km']) if pd.notna(dados['ticket_medio_acima_1000km']) else 0
        }
        
        df_ticket = pd.DataFrame(list(faixas_ticket.items()), columns=['Faixa', 'Ticket Médio'])
        
        fig = px.bar(
            df_ticket,
            x='Faixa',
            y='Ticket Médio',
            title='Ticket Médio por Distância',
            text='Ticket Médio',
            color='Ticket Médio',
            color_continuous_scale='Blues'
        )
        fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def mostrar_margem_veiculo(self):
        """Exibe análise de margem por veículo"""
        st.subheader("🚛 Margem Estimada por Veículo")
        
        st.info("""
        💡 **Importante:** Os custos são estimados em **R$ 2,50 por km** percorrido.
        Esta é uma estimativa padrão que pode variar conforme o tipo de veículo e operação.
        """)
        
        # Filtro de número de veículos
        num_veiculos = st.slider(
            "Número de veículos a exibir:",
            min_value=10,
            max_value=50,
            value=20,
            step=10
        )
        
        df = self.executar_query(f"""
            SELECT * FROM analytics.vw_margem_veiculo 
            LIMIT {num_veiculos}
        """)
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Gráfico de barras - Margem percentual
        fig = px.bar(
            df,
            x='placa',
            y='margem_percentual',
            title=f'Top {num_veiculos} Veículos por Margem Percentual',
            labels={'placa': 'Placa', 'margem_percentual': 'Margem (%)'},
            text='margem_percentual',
            color='margem_percentual',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=25
        )
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['receita_total'] = df_display['receita_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['custo_estimado'] = df_display['custo_estimado'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['margem_bruta'] = df_display['margem_bruta'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['margem_percentual'] = df_display['margem_percentual'].apply(lambda x: f"{float(x):.1f}%")
            df_display['receita_por_km'] = df_display['receita_por_km'].apply(lambda x: f"R$ {float(x):.2f}/km")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def mostrar_faturamento_clientes(self):
        """Exibe análise de faturamento por cliente"""
        st.subheader("👥 Faturamento por Cliente")
        
        # Tabs para remetente e destinatário
        tab1, tab2 = st.tabs(["📤 Remetentes", "📥 Destinatários"])
        
        with tab1:
            self._mostrar_faturamento_tipo("remetente")
        
        with tab2:
            self._mostrar_faturamento_tipo("destinatario")
    
    def _mostrar_faturamento_tipo(self, tipo: str):
        """Exibe faturamento por tipo de cliente (remetente ou destinatário)"""
        
        # Filtro de número de clientes
        num_clientes = st.slider(
            f"Número de {tipo}s a exibir:",
            min_value=10,
            max_value=50,
            value=20,
            step=10,
            key=f"slider_{tipo}"
        )
        
        view_name = f"analytics.vw_faturamento_{tipo}"
        df = self.executar_query(f"""
            SELECT * FROM {view_name} 
            LIMIT {num_clientes}
        """)
        
        if df is None or df.empty:
            st.warning(f"⚠️ Sem dados de {tipo}s disponíveis")
            return
        
        # Truncar nomes longos para visualização
        df['cliente_display'] = df['cliente'].apply(lambda x: x[:30] + '...' if len(str(x)) > 30 else x)
        
        # Gráfico de barras horizontais
        fig = px.bar(
            df.head(num_clientes),
            x='faturamento_total',
            y='cliente_display',
            orientation='h',
            title=f'Top {num_clientes} {tipo.title()}s por Faturamento',
            labels={'faturamento_total': 'Faturamento (R$)', 'cliente_display': 'Cliente'},
            text='faturamento_total',
            color='faturamento_total',
            color_continuous_scale='Viridis'
        )
        
        fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📊 Ver Dados Detalhados"):
            df_display = df.copy()
            df_display['faturamento_total'] = df_display['faturamento_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['ticket_medio'] = df_display['ticket_medio'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['km_total'] = df_display['km_total'].apply(lambda x: f"{float(x):,.0f} km" if pd.notna(x) else "N/A")
            st.dataframe(df_display[['cliente', 'documento', 'total_ctes', 'faturamento_total', 
                                     'ticket_medio', 'km_total', 'classificacao']], 
                        use_container_width=True, hide_index=True)
    
    def mostrar_ranking_clientes(self):
        """Exibe ranking dos principais clientes"""
        st.subheader("🏆 Ranking dos Principais Clientes")
        
        df = self.executar_query("SELECT * FROM analytics.vw_ranking_clientes")
        
        if df is None or df.empty:
            st.warning("⚠️ Sem dados disponíveis")
            return
        
        # Top 3 em destaque
        st.markdown("#### 🥇 Top 3 Clientes")
        
        cols = st.columns(3)
        for idx, (col, (_, row)) in enumerate(zip(cols, df.head(3).iterrows())):
            with col:
                medal = ["🥇", "🥈", "🥉"][idx]
                faturamento = float(row['faturamento_total'])
                participacao = float(row['participacao_percentual'])
                
                st.markdown(f"### {medal} #{row['ranking']}")
                st.markdown(f"**{row['cliente'][:30]}**")
                st.metric("Faturamento", f"R$ {faturamento:,.2f}")
                st.metric("Participação", f"{participacao:.2f}%")
                st.metric("CT-es", f"{int(row['total_ctes']):,}")
                st.info(f"🏷️ {row['classificacao']}")
        
        st.markdown("---")
        
        # Gráfico de participação
        st.markdown("#### 📊 Participação no Faturamento Total")
        
        fig = px.treemap(
            df.head(20),
            path=[px.Constant("Clientes"), 'cliente'],
            values='faturamento_total',
            color='participacao_percentual',
            color_continuous_scale='Oranges',
            title='Top 20 Clientes - Participação no Faturamento'
        )
        
        fig.update_layout(height=600)
        fig.update_traces(textinfo='label+value+percent parent')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela completa
        with st.expander("📊 Ver Ranking Completo"):
            df_display = df.copy()
            df_display['faturamento_total'] = df_display['faturamento_total'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['ticket_medio'] = df_display['ticket_medio'].apply(lambda x: f"R$ {float(x):,.2f}")
            df_display['participacao_percentual'] = df_display['participacao_percentual'].apply(lambda x: f"{float(x):.2f}%")
            df_display['km_total'] = df_display['km_total'].apply(lambda x: f"{float(x):,.0f} km" if pd.notna(x) else "N/A")
            st.dataframe(df_display[['ranking', 'cliente', 'total_ctes', 'faturamento_total', 
                                     'ticket_medio', 'participacao_percentual', 'classificacao']], 
                        use_container_width=True, hide_index=True)


def exibir_rentabilidade_custos():
    """Função principal para exibir todas as visualizações de rentabilidade e custos"""
    viewer = RentabilidadeCustosViewer()
    
    if not viewer.conectar():
        st.error("❌ Não foi possível conectar ao banco de dados")
        return
    
    try:
        # Dashboard principal
        viewer.mostrar_dashboard_principal()
        
        st.markdown("---")
        st.markdown("---")
        
        # Receita mensal
        viewer.mostrar_receita_mensal()
        
        st.markdown("---")
        
        # Ticket médio
        viewer.mostrar_ticket_medio()
        
        st.markdown("---")
        
        # Margem por veículo
        viewer.mostrar_margem_veiculo()
        
        st.markdown("---")
        
        # Faturamento por cliente
        viewer.mostrar_faturamento_clientes()
        
        st.markdown("---")
        
        # Ranking de clientes
        viewer.mostrar_ranking_clientes()
        
    finally:
        viewer.desconectar()
