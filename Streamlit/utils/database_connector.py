# -*- coding: utf-8 -*-
"""
Conector para banco de dados PostgreSQL
Facilita consultas e análises para views do Streamlit
"""
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
import streamlit as st
from typing import Dict, Any, List, Optional
import logging
from contextlib import contextmanager

# Importar configuração
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from Config.database_config import DATABASE_CONFIG, SCHEMAS

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """Classe para conectar ao PostgreSQL e executar consultas para views"""
    
    def __init__(self):
        self.config = DATABASE_CONFIG.copy()
        self.schemas = SCHEMAS
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
        except Exception as e:
            logger.error(f"Erro na conexão: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Executa uma query e retorna DataFrame"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            st.error(f"Erro na consulta: {e}")
            return pd.DataFrame()
    
    def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """Executa query que retorna um valor único"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Erro ao executar query escalar: {e}")
            return None
    
    def get_table_info(self) -> Dict[str, Any]:
        """Obtém informações sobre as tabelas principais"""
        info = {}
        
        # Contagem de registros por tabela principal
        tables = [
            ('Documentos CT-e', 'cte.documento'),
            ('Dados de Carga', 'cte.carga'),
            ('Pessoas', 'core.pessoa'),
            ('Municípios IBGE', 'ibge.municipio'),
            ('UF IBGE', 'ibge.uf'),
            ('Veículos', 'core.veiculo')
        ]
        
        for name, table in tables:
            count = self.execute_scalar(f"SELECT COUNT(*) FROM {table}")
            info[name] = count or 0
        
        return info
    
    def get_date_range(self) -> Dict[str, Any]:
        """Obtém range de datas dos documentos"""
        query = """
        SELECT 
            MIN(data_emissao) as primeira_data,
            MAX(data_emissao) as ultima_data,
            COUNT(*) as total_docs
        FROM cte.documento 
        WHERE data_emissao IS NOT NULL
        """
        df = self.execute_query(query)
        if not df.empty:
            return df.iloc[0].to_dict()
        return {}
    
    # Queries específicas para views gerais
    
    def get_resumo_geral(self) -> Dict[str, Any]:
        """Resumo geral dos dados - KPIs principais"""
        query = """
        SELECT 
            COUNT(*) as total_documentos,
            COUNT(DISTINCT d.id_municipio_origem) as total_cidades_origem,
            COUNT(DISTINCT d.id_municipio_destino) as total_cidades_destino,
            SUM(d.valor_frete) as valor_total_fretes,
            AVG(d.valor_frete) as valor_medio_frete,
            SUM(c.valor) as valor_total_cargas,
            AVG(c.valor) as valor_medio_carga,
            SUM(c.peso) as peso_total,
            COUNT(DISTINCT v.id_veiculo) as total_veiculos
        FROM cte.documento d
        LEFT JOIN cte.carga c ON c.id_cte = d.id_cte
        LEFT JOIN core.veiculo v ON v.id_veiculo = d.id_veiculo
        """
        df = self.execute_query(query)
        if not df.empty:
            return df.iloc[0].to_dict()
        return {}
    
    def get_distribuicao_temporal(self) -> pd.DataFrame:
        """Distribuição temporal dos documentos"""
        query = """
        SELECT 
            DATE_TRUNC('month', data_emissao) as mes,
            COUNT(*) as total_documentos,
            SUM(valor_frete) as valor_total_fretes,
            AVG(valor_frete) as valor_medio_frete,
            SUM(c.valor) as valor_total_cargas
        FROM cte.documento d
        LEFT JOIN cte.carga c ON c.id_cte = d.id_cte
        WHERE data_emissao IS NOT NULL
        GROUP BY DATE_TRUNC('month', data_emissao)
        ORDER BY mes
        """
        return self.execute_query(query)
    
    def get_distribuicao_valores(self) -> pd.DataFrame:
        """Distribuição de valores de frete e carga"""
        query = """
        SELECT 
            CASE 
                WHEN valor_frete < 100 THEN '< R$ 100'
                WHEN valor_frete < 500 THEN 'R$ 100-500'
                WHEN valor_frete < 1000 THEN 'R$ 500-1000'
                WHEN valor_frete < 5000 THEN 'R$ 1000-5000'
                ELSE '> R$ 5000'
            END as faixa_frete,
            COUNT(*) as quantidade,
            ROUND(AVG(valor_frete), 2) as valor_medio_frete,
            ROUND(SUM(valor_frete), 2) as valor_total_frete
        FROM cte.documento 
        WHERE valor_frete IS NOT NULL AND valor_frete > 0
        GROUP BY 1
        ORDER BY valor_medio_frete
        """
        return self.execute_query(query)
    
    def get_top_rotas(self, limit: int = 10) -> pd.DataFrame:
        """Top rotas mais utilizadas"""
        query = f"""
        SELECT 
            uf_o.sigla as uf_origem,
            uf_d.sigla as uf_destino,
            CONCAT(uf_o.sigla, ' → ', uf_d.sigla) as rota,
            COUNT(*) as total_viagens,
            ROUND(SUM(d.valor_frete), 2) as valor_total_fretes,
            ROUND(AVG(d.valor_frete), 2) as valor_medio_frete,
            ROUND(SUM(c.valor), 2) as valor_total_cargas
        FROM cte.documento d
        LEFT JOIN ibge.municipio m_o ON m_o.id_municipio = d.id_municipio_origem
        LEFT JOIN ibge.uf uf_o ON uf_o.id_uf = m_o.id_uf
        LEFT JOIN ibge.municipio m_d ON m_d.id_municipio = d.id_municipio_destino
        LEFT JOIN ibge.uf uf_d ON uf_d.id_uf = m_d.id_uf
        LEFT JOIN cte.carga c ON c.id_cte = d.id_cte
        WHERE uf_o.sigla IS NOT NULL AND uf_d.sigla IS NOT NULL
        GROUP BY uf_o.sigla, uf_d.sigla, rota
        ORDER BY total_viagens DESC
        LIMIT {limit}
        """
        return self.execute_query(query)
    
    def get_distribuicao_uf(self) -> pd.DataFrame:
        """Distribuição por UF (origem e destino)"""
        query = """
        WITH origem AS (
            SELECT 
                uf.sigla as uf,
                uf.nome as nome_uf,
                COUNT(*) as total_origem,
                SUM(d.valor_frete) as valor_origem
            FROM cte.documento d
            JOIN ibge.municipio m ON m.id_municipio = d.id_municipio_origem
            JOIN ibge.uf uf ON uf.id_uf = m.id_uf
            GROUP BY uf.sigla, uf.nome
        ),
        destino AS (
            SELECT 
                uf.sigla as uf,
                COUNT(*) as total_destino,
                SUM(d.valor_frete) as valor_destino
            FROM cte.documento d
            JOIN ibge.municipio m ON m.id_municipio = d.id_municipio_destino
            JOIN ibge.uf uf ON uf.id_uf = m.id_uf
            GROUP BY uf.sigla
        )
        SELECT 
            o.uf,
            o.nome_uf,
            COALESCE(o.total_origem, 0) as total_origem,
            COALESCE(d.total_destino, 0) as total_destino,
            COALESCE(o.total_origem, 0) + COALESCE(d.total_destino, 0) as total_movimentacao,
            ROUND(COALESCE(o.valor_origem, 0), 2) as valor_origem,
            ROUND(COALESCE(d.valor_destino, 0), 2) as valor_destino
        FROM origem o
        FULL OUTER JOIN destino d ON d.uf = o.uf
        ORDER BY total_movimentacao DESC
        """
        return self.execute_query(query)
    
    def get_top_produtos(self, limit: int = 10) -> pd.DataFrame:
        """Top produtos mais transportados"""
        query = f"""
        SELECT 
            COALESCE(produto_predominante, 'Não informado') as produto,
            COUNT(*) as total_embarques,
            ROUND(SUM(valor), 2) as valor_total,
            ROUND(AVG(valor), 2) as valor_medio,
            ROUND(SUM(peso), 2) as peso_total,
            ROUND(AVG(peso), 2) as peso_medio,
            ROUND(SUM(quantidade), 2) as quantidade_total
        FROM cte.carga c
        JOIN cte.documento d ON d.id_cte = c.id_cte
        GROUP BY produto_predominante
        ORDER BY total_embarques DESC
        LIMIT {limit}
        """
        return self.execute_query(query)
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Teste de conexão falhou: {e}")
            return False

# Instância global
db = DatabaseConnector()