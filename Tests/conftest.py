#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações e Fixtures Compartilhadas - Sistema CT-e
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# CRÍTICO: Configurar variáveis de ambiente ANTES de qualquer importação
def configure_test_environment():
    """Configura ambiente de testes para usar sact_test"""
    # Forçar uso do banco de testes
    os.environ['DB_NAME'] = 'sact_test'
    os.environ['DB_USER'] = 'sergiomendes'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '5432'
    os.environ['DB_PASSWORD'] = ''
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['APPLICATION_NAME'] = 'CTE_Tests'
    os.environ['CORE_SCHEMA'] = 'core'
    os.environ['CTE_SCHEMA'] = 'cte'
    os.environ['IBGE_SCHEMA'] = 'ibge'

# Configurar ANTES de tudo
configure_test_environment()

# Path do projeto
PROJETO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJETO_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Retorna diretório raiz do projeto."""
    return PROJETO_ROOT


@pytest.fixture(scope="session")
def sample_xml_path():
    """Retorna caminho para XML de amostra."""
    paths = [
        Path("/Users/sergiomendes/Documents/CT-e/mes_1_2025/CT-e/Autorizados/CTe21250135263415000132570010000004821317310777.xml"),
        Path(__file__).parent / "sample_cte.xml",
    ]
    
    for path in paths:
        if path.exists():
            return path
    
    pytest.skip("Nenhum arquivo XML de teste encontrado")


@pytest.fixture(scope="session")
def sample_xml_dir():
    """Retorna diretório com XMLs de amostra."""
    dir_path = Path("/Users/sergiomendes/Documents/CT-e/mes_1_2025/CT-e/Autorizados")
    
    if dir_path.exists() and any(dir_path.glob("*.xml")):
        return dir_path
    
    pytest.skip("Diretório com XMLs não encontrado")


@pytest.fixture
def temp_dir():
    """Cria diretório temporário."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def db_config():
    """Configuração do banco de dados de testes."""
    try:
        # Forçar reimportação do módulo de configuração
        import sys
        if 'Config.database_config' in sys.modules:
            del sys.modules['Config.database_config']
        
        from Config import database_config
        
        # Forçar o uso do banco de testes
        database_config.DATABASE_CONFIG['database'] = 'sact_test'
        
        # Garantir que estamos usando o banco de testes
        assert database_config.DATABASE_CONFIG['database'] == 'sact_test', \
            f"ERRO: Testes devem usar 'sact_test', mas está configurado '{database_config.DATABASE_CONFIG['database']}'"
        
        print(f"\n✅ Usando banco de testes: {database_config.DATABASE_CONFIG['database']}")
        print(f"   Host: {database_config.DATABASE_CONFIG['host']}")
        print(f"   User: {database_config.DATABASE_CONFIG['user']}")
        
        return database_config.DATABASE_CONFIG
    except AssertionError as e:
        pytest.fail(str(e))
    except Exception as e:
        pytest.skip(f"Configuração de banco não disponível: {e}")


@pytest.fixture
def db_connection(db_config, populate_ibge):
    """Conexão com banco de dados."""
    import psycopg
    
    try:
        conn = psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['database'],
            user=db_config['user'],
            password=db_config.get('password', ''),
            options=db_config.get('options', '')
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Não foi possível conectar ao banco: {e}")


@pytest.fixture(scope="session")
def populate_ibge(db_config):
    """Popula dados IBGE básicos para testes."""
    import psycopg
    
    try:
        conn = psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['database'],
            user=db_config['user'],
            password=db_config.get('password', ''),
            options=db_config.get('options', '')
        )
        
        with conn.cursor() as cursor:
            # Popular UFs (principais para testes)
            cursor.execute("""
                INSERT INTO ibge.uf (id_uf, sigla, nome, regiao)
                VALUES 
                    (22, 'PI', 'Piauí', 'Nordeste'),
                    (35, 'SP', 'São Paulo', 'Sudeste'),
                    (33, 'RJ', 'Rio de Janeiro', 'Sudeste'),
                    (31, 'MG', 'Minas Gerais', 'Sudeste'),
                    (41, 'PR', 'Paraná', 'Sul')
                ON CONFLICT (id_uf) DO NOTHING
            """)
            
            # Popular alguns municípios principais
            cursor.execute("""
                INSERT INTO ibge.municipio (id_municipio, nome, id_uf, nome_normalizado)
                VALUES 
                    (2211001, 'Teresina', 22, 'TERESINA'),
                    (3550308, 'São Paulo', 35, 'SAO PAULO'),
                    (3304557, 'Rio de Janeiro', 33, 'RIO DE JANEIRO'),
                    (3106200, 'Belo Horizonte', 31, 'BELO HORIZONTE'),
                    (4106902, 'Curitiba', 41, 'CURITIBA')
                ON CONFLICT (id_municipio) DO NOTHING
            """)
            
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        # Se falhar, apenas pula (pode ser que já esteja populado)
        pass


@pytest.fixture(scope="session")
def results_dir():
    """Diretório para resultados."""
    results_path = Path(__file__).parent / "resultados"
    results_path.mkdir(exist_ok=True)
    return results_path


@pytest.fixture
def test_timestamp():
    """Timestamp para arquivos."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def pytest_configure(config):
    """Hook de configuração."""
    configure_test_environment()
    
    print("\n" + "="*80)
    print("🧪 SUITE DE TESTES CT-e")
    print("="*80)
    print(f"🗄️  Banco de Dados: sact_test")
    print(f"👤 Usuário: sergiomendes")
    print(f"🖥️  Host: localhost:5432")
    print(f"🔬 Ambiente: TESTING")
    print("="*80)


def pytest_collection_modifyitems(config, items):
    """Adiciona markers automaticamente."""
    for item in items:
        if "unitarios" in str(item.fspath):
            item.add_marker(pytest.mark.unitario)
        elif "funcionais" in str(item.fspath):
            item.add_marker(pytest.mark.funcional)
        elif "integracao" in str(item.fspath):
            item.add_marker(pytest.mark.integracao)
