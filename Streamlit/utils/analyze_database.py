# -*- coding: utf-8 -*-
"""
Análise completa do banco de dados CT-e para sugestão de novas views
"""
import sys
import os
from pathlib import Path

# Configurar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from Config.database_config import DATABASE_CONFIG
import psycopg2
import pandas as pd

def analyze_database():
    """Analisa todo o banco de dados para sugerir novas views"""
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        
        print("🔍 ANÁLISE COMPLETA DO BANCO DE DADOS CT-e")
        print("=" * 60)
        
        # 1. Estrutura das tabelas
        print("\n📊 1. ESTRUTURA DAS TABELAS:")
        tables_query = """
        SELECT 
            t.table_schema as schema,
            t.table_name as tabela,
            COALESCE(s.n_live_tup, 0) as registros_ativos
        FROM information_schema.tables t
        LEFT JOIN pg_stat_user_tables s ON s.schemaname = t.table_schema AND s.relname = t.table_name
        WHERE t.table_schema IN ('cte', 'core', 'ibge') 
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_schema, t.table_name;
        """
        df_tables = pd.read_sql_query(tables_query, conn)
        print(df_tables.to_string(index=False))
        
        # 2. Análise detalhada dos documentos CT-e
        print("\n📋 2. ANÁLISE DOS DOCUMENTOS CT-e:")
        docs_query = """
        SELECT 
            COUNT(*) as total_documentos,
            COUNT(DISTINCT chave) as chaves_unicas,
            COUNT(DISTINCT numero) as numeros_unicos,
            COUNT(DISTINCT serie) as series_unicas,
            MIN(data_emissao) as primeira_emissao,
            MAX(data_emissao) as ultima_emissao,
            COUNT(DISTINCT DATE_TRUNC('month', data_emissao)) as meses_com_dados,
            COUNT(DISTINCT cfop) as cfops_diferentes,
            SUM(valor_frete) as valor_total_fretes,
            AVG(valor_frete) as valor_medio_frete,
            STDDEV(valor_frete) as desvio_padrao_frete
        FROM cte.documento 
        WHERE data_emissao IS NOT NULL;
        """
        df_docs = pd.read_sql_query(docs_query, conn)
        print(df_docs.to_string(index=False))
        
        # 3. Análise de CFOPs
        print("\n🏷️ 3. ANÁLISE DE CFOPs:")
        cfop_query = """
        SELECT 
            cfop,
            COUNT(*) as frequencia,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentual,
            SUM(valor_frete) as valor_total,
            AVG(valor_frete) as valor_medio
        FROM cte.documento 
        WHERE cfop IS NOT NULL
        GROUP BY cfop
        ORDER BY frequencia DESC
        LIMIT 15;
        """
        df_cfop = pd.read_sql_query(cfop_query, conn)
        print(df_cfop.to_string(index=False))
        
        # 4. Análise de carga
        print("\n📦 4. ANÁLISE DE CARGA:")
        carga_query = """
        SELECT 
            COUNT(*) as total_cargas,
            COUNT(valor) as cargas_com_valor,
            COUNT(peso) as cargas_com_peso,
            COUNT(quantidade) as cargas_com_quantidade,
            COUNT(produto_predominante) as cargas_com_produto,
            SUM(valor) as valor_total_cargas,
            AVG(valor) as valor_medio_carga,
            SUM(peso) as peso_total_kg,
            AVG(peso) as peso_medio_kg,
            SUM(quantidade) as quantidade_total,
            AVG(quantidade) as quantidade_media,
            COUNT(DISTINCT produto_predominante) as produtos_diferentes,
            COUNT(DISTINCT unidade_medida) as unidades_diferentes
        FROM cte.carga;
        """
        df_carga = pd.read_sql_query(carga_query, conn)
        print(df_carga.to_string(index=False))
        
        # 5. Top produtos com mais detalhes
        print("\n🎯 5. TOP PRODUTOS DETALHADO:")
        produtos_query = """
        SELECT 
            COALESCE(produto_predominante, 'Não informado') as produto,
            COUNT(*) as total_embarques,
            ROUND(SUM(valor), 2) as valor_total,
            ROUND(AVG(valor), 2) as valor_medio,
            ROUND(SUM(peso), 2) as peso_total_kg,
            ROUND(AVG(peso), 2) as peso_medio_kg,
            COUNT(DISTINCT d.id_municipio_origem) as cidades_origem,
            COUNT(DISTINCT d.id_municipio_destino) as cidades_destino
        FROM cte.carga c
        JOIN cte.documento d ON d.id_cte = c.id_cte
        GROUP BY produto_predominante
        ORDER BY total_embarques DESC
        LIMIT 15;
        """
        df_produtos = pd.read_sql_query(produtos_query, conn)
        print(df_produtos.to_string(index=False))
        
        # 6. Análise geográfica detalhada
        print("\n🌍 6. ANÁLISE GEOGRÁFICA:")
        geo_query = """
        WITH rotas AS (
            SELECT 
                uf_o.sigla as uf_origem,
                uf_d.sigla as uf_destino,
                COUNT(*) as viagens,
                SUM(d.valor_frete) as valor_fretes,
                SUM(c.valor) as valor_cargas,
                AVG(c.peso) as peso_medio
            FROM cte.documento d
            LEFT JOIN ibge.municipio m_o ON m_o.id_municipio = d.id_municipio_origem
            LEFT JOIN ibge.uf uf_o ON uf_o.id_uf = m_o.id_uf
            LEFT JOIN ibge.municipio m_d ON m_d.id_municipio = d.id_municipio_destino
            LEFT JOIN ibge.uf uf_d ON uf_d.id_uf = m_d.id_uf
            LEFT JOIN cte.carga c ON c.id_cte = d.id_cte
            WHERE uf_o.sigla IS NOT NULL AND uf_d.sigla IS NOT NULL
            GROUP BY uf_o.sigla, uf_d.sigla
        )
        SELECT 
            COUNT(*) as total_rotas_diferentes,
            SUM(viagens) as total_viagens,
            AVG(viagens) as viagens_por_rota,
            MAX(viagens) as max_viagens_rota,
            COUNT(CASE WHEN uf_origem = uf_destino THEN 1 END) as rotas_intraestado,
            COUNT(CASE WHEN uf_origem != uf_destino THEN 1 END) as rotas_interestado
        FROM rotas;
        """
        df_geo = pd.read_sql_query(geo_query, conn)
        print(df_geo.to_string(index=False))
        
        # 7. Análise de pessoas e partes
        print("\n👥 7. ANÁLISE DE PESSOAS E PARTES:")
        pessoas_query = """
        SELECT 
            COUNT(DISTINCT p.id_pessoa) as total_pessoas,
            COUNT(DISTINCT CASE WHEN dp.tipo = 'remetente' THEN p.id_pessoa END) as remetentes_unicos,
            COUNT(DISTINCT CASE WHEN dp.tipo = 'destinatario' THEN p.id_pessoa END) as destinatarios_unicos,
            COUNT(DISTINCT CASE WHEN dp.tipo = 'expedidor' THEN p.id_pessoa END) as expedidores_unicos,
            COUNT(DISTINCT CASE WHEN dp.tipo = 'recebedor' THEN p.id_pessoa END) as recebedores_unicos,
            COUNT(CASE WHEN p.cpf_cnpj IS NOT NULL THEN 1 END) as pessoas_com_documento
        FROM core.pessoa p
        LEFT JOIN cte.documento_parte dp ON dp.id_pessoa = p.id_pessoa;
        """
        df_pessoas = pd.read_sql_query(pessoas_query, conn)
        print(df_pessoas.to_string(index=False))
        
        # 8. Análise de veículos
        print("\n🚛 8. ANÁLISE DE VEÍCULOS:")
        veiculos_query = """
        SELECT 
            COUNT(DISTINCT v.id_veiculo) as total_veiculos,
            COUNT(DISTINCT v.placa) as placas_unicas,
            COUNT(DISTINCT uf.sigla) as ufs_licenciamento,
            COUNT(d.id_cte) as total_viagens,
            ROUND(COUNT(d.id_cte)::numeric / COUNT(DISTINCT v.id_veiculo), 2) as viagens_por_veiculo
        FROM core.veiculo v
        LEFT JOIN ibge.uf uf ON uf.id_uf = v.id_uf_licenciamento
        LEFT JOIN cte.documento d ON d.id_veiculo = v.id_veiculo;
        """
        df_veiculos = pd.read_sql_query(veiculos_query, conn)
        print(df_veiculos.to_string(index=False))
        
        # 9. Padrões temporais
        print("\n⏰ 9. PADRÕES TEMPORAIS:")
        temporal_query = """
        SELECT 
            EXTRACT(HOUR FROM data_emissao) as hora,
            COUNT(*) as documentos,
            ROUND(AVG(valor_frete), 2) as valor_medio_frete
        FROM cte.documento 
        WHERE data_emissao IS NOT NULL
        GROUP BY EXTRACT(HOUR FROM data_emissao)
        ORDER BY hora;
        """
        df_temporal = pd.read_sql_query(temporal_query, conn)
        print("Distribuição por hora do dia:")
        print(df_temporal.to_string(index=False))
        
        # 10. Análise de eficiência
        print("\n📈 10. ANÁLISE DE EFICIÊNCIA:")
        eficiencia_query = """
        SELECT 
            CASE 
                WHEN c.peso > 0 AND c.valor > 0 THEN ROUND(c.valor / c.peso, 2)
                ELSE NULL 
            END as valor_por_kg,
            COUNT(*) as frequencia
        FROM cte.carga c
        WHERE c.peso > 0 AND c.valor > 0
        GROUP BY 1
        ORDER BY 1
        LIMIT 10;
        """
        df_eficiencia = pd.read_sql_query(eficiencia_query, conn)
        print("Valor por kg (R$/kg) - Amostra:")
        print(df_eficiencia.to_string(index=False))
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ ANÁLISE COMPLETA FINALIZADA")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

if __name__ == "__main__":
    analyze_database()