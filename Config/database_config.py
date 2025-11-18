# -*- coding: utf-8 -*-
"""
Configuração de conexão com PostgreSQL
Lê variáveis de ambiente do arquivo .env
"""
import os
from pathlib import Path
from typing import Dict, Any

# Carregar variáveis de ambiente do arquivo .env
def load_env_file():
    """Carrega variáveis de ambiente do arquivo .env"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Carrega o arquivo .env na importação
load_env_file()

# Configuração principal do banco de dados
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', os.getenv('ENVIRONMENT') == 'testing' and 'sact_test' or 'sact'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'application_name': os.getenv('APPLICATION_NAME', 'CTE_Database_Manager'),
    'connect_timeout': int(os.getenv('CONNECTION_TIMEOUT', '10')),
    'options': f"-c search_path={os.getenv('CORE_SCHEMA', 'core')},{os.getenv('CTE_SCHEMA', 'cte')},{os.getenv('IBGE_SCHEMA', 'ibge')},public"
}

# Configuração do pool de conexões
POOL_CONFIG = {
    'min_connections': int(os.getenv('MIN_CONNECTIONS_POOL', '2')),
    'max_connections': int(os.getenv('MAX_CONNECTIONS_POOL', '10')),
    'timeout': int(os.getenv('CONNECTION_TIMEOUT', '10'))
}

# Schemas específicos
SCHEMAS = {
    'ibge': os.getenv('IBGE_SCHEMA', 'ibge'),
    'core': os.getenv('CORE_SCHEMA', 'core'),
    'cte': os.getenv('CTE_SCHEMA', 'cte')
}

# Configurações de cache
CACHE_CONFIG = {
    'ttl_seconds': int(os.getenv('CACHE_TTL_SECONDS', '3600')),
    'max_size': 1000
}

# Configurações de processamento
PROCESSING_CONFIG = {
    'batch_size': int(os.getenv('BATCH_SIZE', '50')),
    'max_workers': int(os.getenv('MAX_WORKERS', '4')),
    'network_timeout': int(os.getenv('NETWORK_TIMEOUT', '30'))
}

# Configurações de log
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file_path': os.getenv('LOG_FILE_PATH', 'logs/cte_database.log'),
    'format': os.getenv('LOG_FORMAT', 'json'),
    'max_size_mb': int(os.getenv('LOG_MAX_SIZE_MB', '50')),
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
}

# Configurações gerais
APP_CONFIG = {
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'verbose_logging': os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true',
    'temp_dir': os.getenv('TEMP_DIR', 'temp'),
    'results_dir': os.getenv('RESULTS_DIR', 'resultados_teste_completo')
}

def get_connection_string() -> str:
    """Retorna string de conexão PostgreSQL"""
    if DATABASE_CONFIG['password']:
        return (
            f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        )
    else:
        return (
            f"postgresql://{DATABASE_CONFIG['user']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        )

def validate_config() -> Dict[str, Any]:
    """Valida configurações e retorna status"""
    errors = []
    warnings = []
    
    # Validações críticas
    # Senha pode ser vazia para configurações locais sem autenticação
    
    if not DATABASE_CONFIG['database']:
        errors.append("DB_NAME não configurado")
    
    if not DATABASE_CONFIG['user']:
        errors.append("DB_USER não configurado")
    
    # Validações de warning
    if DATABASE_CONFIG['password'] == 'sua_senha_postgresql_aqui':
        warnings.append("Senha padrão detectada - configure sua senha real")
    
    if not DATABASE_CONFIG['password']:
        warnings.append("PostgreSQL configurado sem senha (modo local)")
    
    if APP_CONFIG['environment'] == 'development' and DATABASE_CONFIG['database'] == 'sact':
        warnings.append("Usando banco de desenvolvimento")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'config_summary': {
            'host': DATABASE_CONFIG['host'],
            'port': DATABASE_CONFIG['port'],
            'database': DATABASE_CONFIG['database'],
            'user': DATABASE_CONFIG['user'],
            'password_set': bool(DATABASE_CONFIG['password']),
            'environment': APP_CONFIG['environment']
        }
    }

if __name__ == "__main__":
    """Teste de configuração"""
    print("🔧 Testando configuração do banco de dados...")
    
    validation = validate_config()
    
    print(f"\n📊 Status da configuração:")
    print(f"   Válida: {'✅' if validation['valid'] else '❌'}")
    print(f"   Host: {validation['config_summary']['host']}")
    print(f"   Porta: {validation['config_summary']['port']}")
    print(f"   Banco: {validation['config_summary']['database']}")
    print(f"   Usuário: {validation['config_summary']['user']}")
    print(f"   Senha configurada: {'✅' if validation['config_summary']['password_set'] else '❌'}")
    print(f"   Ambiente: {validation['config_summary']['environment']}")
    
    if validation['errors']:
        print(f"\n❌ Erros encontrados:")
        for error in validation['errors']:
            print(f"   • {error}")
    
    if validation['warnings']:
        print(f"\n⚠️  Avisos:")
        for warning in validation['warnings']:
            print(f"   • {warning}")
    
    if validation['valid']:
        conn_str = get_connection_string()
        if DATABASE_CONFIG['password']:
            masked_conn = conn_str.replace(DATABASE_CONFIG['password'], '***')
        else:
            masked_conn = conn_str
        print(f"\n🔗 String de conexão: {masked_conn}")
    else:
        print(f"\n❌ Corrija os erros antes de usar o sistema")