# Sistema SACT - Manual de Instalação e Configuração

## Sumário

1. [Visão Geral](#visão-geral)
2. [Requisitos de Sistema](#requisitos-de-sistema)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Instalação Passo a Passo](#instalação-passo-a-passo)
5. [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
6. [Carga Inicial de Dados](#carga-inicial-de-dados)
7. [Processamento de CT-e](#processamento-de-ct-e)
8. [Interface Web](#interface-web)
9. [Verificação da Instalação](#verificação-da-instalação)
10. [Troubleshooting](#troubleshooting)
11. [Manutenção](#manutenção)

---

## Visão Geral

O Sistema SACT (Sistema de Análise de CT-e e Transporte) é uma solução completa para processamento, armazenamento e análise de Conhecimentos de Transporte Eletrônico (CT-e). O sistema extrai dados de arquivos XML, armazena em banco de dados PostgreSQL e oferece análises operacionais e financeiras através de interface web.

### Principais Funcionalidades

- Extração automática de dados de CT-e a partir de arquivos XML
- Cálculo automático de quilometragem entre municípios
- Integração com dados geográficos do IBGE (municípios e coordenadas)
- Análise de rentabilidade por veículo e rota
- Dashboards interativos para análise operacional
- Sistema de views analíticas pré-calculadas
- Rastreabilidade completa das operações

---

## Requisitos de Sistema

### Hardware Mínimo

- Processador: 2 cores, 2.0 GHz ou superior
- Memória RAM: 4 GB (recomendado 8 GB)
- Armazenamento: 10 GB livres
- Conexão com internet (para carga inicial de dados IBGE)

### Software Obrigatório

#### Sistema Operacional
- Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- macOS 10.14+
- Windows 10+ (com WSL2 recomendado)

#### PostgreSQL
- Versão: 12.0 ou superior
- Extensões necessárias:
  - `unaccent` (normalização de texto)
  - `pg_trgm` (busca por similaridade)

#### Python
- Versão: 3.8 ou superior
- pip (gerenciador de pacotes)
- venv (ambiente virtual)

---

## Arquitetura do Sistema

### Estrutura de Diretórios

```
SACT/
├── Config/
│   ├── database_config.py          # Configurações do banco de dados
│   └── __init__.py
├── Database/
│   ├── main.py                     # Camada de aplicação principal
│   ├── managers/                   # Gerenciadores (DB, arquivos, estatísticas)
│   ├── services/                   # Serviços de negócio
│   ├── repositories/               # Acesso a dados
│   ├── migrations/                 # Scripts SQL de migração
│   └── views/                      # Definições de views analíticas
├── cte_extractor/
│   ├── extractors.py               # Extratores de dados de CT-e
│   ├── strategies.py               # Estratégias de extração
│   ├── models.py                   # Modelos de dados
│   └── utils.py                    # Utilitários
├── Streamlit/
│   ├── app.py                      # Interface web principal
│   ├── components/                 # Componentes da interface
│   ├── utils/                      # Utilitários da interface
│   └── feedback/                   # Sistema de feedback
├── Tests/
│   ├── unitarios/                  # Testes unitários
│   ├── integracao/                 # Testes de integração
│   └── funcionais/                 # Testes funcionais
├── docs/                           # Documentação técnica
├── estrutura.sql                   # Schema completo do banco
├── ibge_loader.py                  # Carregador de dados IBGE
├── requirements.txt                # Dependências Python
└── README.md                       # Documentação principal
```

### Camadas da Aplicação

1. **Camada de Extração** (`cte_extractor/`)
   - Extração de dados de arquivos XML
   - Validação de estrutura
   - Transformação de dados

2. **Camada de Aplicação** (`Database/`)
   - Lógica de negócio
   - Orquestração de processos
   - Gerenciamento de transações

3. **Camada de Persistência** (PostgreSQL)
   - Armazenamento de dados
   - Views analíticas
   - Funções e procedures

4. **Camada de Visualização** (`Streamlit/`)
   - Interface web
   - Dashboards
   - Relatórios interativos

---

## Instalação Passo a Passo

### Passo 1: Preparação do Ambiente

#### 1.1 Criar Diretório de Instalação

```bash
mkdir -p /opt/sact
cd /opt/sact
```

#### 1.2 Clonar ou Copiar o Sistema

```bash
# Se usando git
git clone <repositorio> .

# Ou copiar arquivos manualmente
cp -r /caminho/origem/* .
```

#### 1.3 Criar Ambiente Virtual Python

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

#### 1.4 Instalar Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Conteúdo mínimo do requirements.txt:**
```
psycopg2-binary>=2.9.0
requests>=2.28.0
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.14.0
python-dotenv>=1.0.0
```

---

## Configuração do Banco de Dados

### Passo 2: Instalação do PostgreSQL

#### 2.1 Instalação (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2.2 Instalação (macOS)

```bash
brew install postgresql@14
brew services start postgresql@14
```

#### 2.3 Instalação (CentOS/RHEL)

```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Passo 3: Criar Banco de Dados

#### 3.1 Acessar PostgreSQL

```bash
sudo -u postgres psql
```

#### 3.2 Criar Usuário e Banco

```sql
-- Criar usuário
CREATE USER sact_user WITH PASSWORD 'senha_segura_aqui';

-- Criar banco de dados
CREATE DATABASE sact OWNER sact_user;

-- Conceder privilégios
GRANT ALL PRIVILEGES ON DATABASE sact TO sact_user;

-- Conectar ao banco
\c sact

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Sair
\q
```

### Passo 4: Criar Estrutura do Banco

#### 4.1 Executar Script de Estrutura

```bash
# Executar o schema completo
psql -U sact_user -d sact -f estrutura.sql
```

#### 4.2 Verificar Schemas Criados

```bash
psql -U sact_user -d sact -c "\dn"
```

**Schemas esperados:**
- `core` - Dados mestre (empresas, clientes, veículos)
- `cte` - Dados de CT-e (documentos, cargas)
- `ibge` - Dados geográficos (UF, municípios)
- `analytics` - Views analíticas

### Passo 5: Configurar Conexão

#### 5.1 Criar Arquivo de Configuração

Editar `Config/database_config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('PGPORT', '5432'),
    'dbname': os.getenv('PGDATABASE', 'sact'),
    'user': os.getenv('PGUSER', 'sact_user'),
    'password': os.getenv('PGPASSWORD', 'senha_segura_aqui')
}

def validate_config():
    """Valida se todas as configurações necessárias estão presentes."""
    required = ['host', 'port', 'dbname', 'user', 'password']
    missing = [k for k in required if not DATABASE_CONFIG.get(k)]
    if missing:
        raise ValueError(f"Configurações faltando: {', '.join(missing)}")
    return True
```

#### 5.2 Criar Arquivo .env (Opcional, mais seguro)

```bash
cat > .env << EOF
PGHOST=localhost
PGPORT=5432
PGDATABASE=sact
PGUSER=sact_user
PGPASSWORD=senha_segura_aqui
EOF

chmod 600 .env
```

#### 5.3 Testar Conexão

```bash
python3 << EOF
from Config.database_config import DATABASE_CONFIG, validate_config
import psycopg2

try:
    validate_config()
    conn = psycopg2.connect(**DATABASE_CONFIG)
    print("Conexão estabelecida com sucesso!")
    conn.close()
except Exception as e:
    print(f"Erro na conexão: {e}")
EOF
```

---

## Carga Inicial de Dados

### Passo 6: Carregar Dados do IBGE

O sistema necessita dos dados oficiais do IBGE (UFs e municípios) para funcionar corretamente.

#### 6.1 Executar Carregador IBGE

```bash
python3 ibge_loader.py
```

**Saída esperada:**
```
== IBGE Loader ==
Fetching UFs from IBGE ...
Fetched 27 UFs
Upserting UFs ...
Upserted UFs: 27
Fetching Municípios from IBGE ... (this can take a few seconds)
Fetched 5571 Municípios
Fetching coordenadas from GitHub dataset ...
Loaded coordinates for 5570 municipalities
Upserting Municípios with coordinates ...
Upserted Municípios: 5571
Done in X.Xs. Totals -> UF: 27, Município: 5571
```

#### 6.2 Verificar Carga de Dados

```bash
psql -U sact_user -d sact << EOF
SELECT 'UFs:', COUNT(*) FROM ibge.uf;
SELECT 'Municípios:', COUNT(*) FROM ibge.municipio;
SELECT 'Com coordenadas:', COUNT(*) FROM ibge.municipio WHERE latitude IS NOT NULL;
EOF
```

**Resultado esperado:**
- UFs: 27
- Municípios: 5571
- Com coordenadas: 5570

---

## Processamento de CT-e

### Passo 7: Preparar Arquivos XML

#### 7.1 Organizar Diretório de XMLs

```bash
mkdir -p /opt/sact/xml_ctes
# Copiar seus arquivos XML para este diretório
```

#### 7.2 Validar Estrutura dos XMLs

Os arquivos XML devem seguir o padrão da NF-e/CT-e da SEFAZ. Exemplo de estrutura:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cteProc versao="3.00">
  <CTe>
    <infCte>
      <ide>...</ide>
      <emit>...</emit>
      <rem>...</rem>
      <dest>...</dest>
      <vPrest>...</vPrest>
      <infCTeNorm>
        <infDoc>...</infDoc>
        <infModal>
          <rodo>
            <veic>
              <placa>ABC1234</placa>
            </veic>
          </rodo>
        </infModal>
      </infCTeNorm>
    </infCte>
  </CTe>
</cteProc>
```

### Passo 8: Processar CT-es

#### 8.1 Processamento via Python

```python
from Database.main import CTEMainApplication

# Inicializar aplicação
app = CTEMainApplication()

# Processar diretório de XMLs
diretorio_xml = "/opt/sact/xml_ctes"
custo_km = 3.50  # Custo por quilômetro

app.processar_diretorio(
    diretorio=diretorio_xml,
    custo_por_km=custo_km
)
```

#### 8.2 Processamento via Interface Web

```bash
cd /opt/sact/Streamlit
streamlit run app.py
```

Acesse `http://localhost:8501` e siga as instruções na interface.

### Passo 9: Criar Views Analíticas

Após processar os CT-es, criar views para análises:

```bash
python3 << EOF
from Database.main import CTEMainApplication

app = CTEMainApplication()
app.criar_views_analiticas()
EOF
```

**Views criadas:**
- `analytics.vw_cte_resumo` - Resumo completo de CT-es
- `analytics.vw_performance_frota` - Performance de veículos
- `analytics.vw_rotas_frequentes` - Rotas mais utilizadas
- `analytics.vw_rentabilidade_mensal` - Rentabilidade por período
- E outras (ver `Database/views/`)

---

## Interface Web

### Passo 10: Configurar Streamlit

#### 10.1 Criar Arquivo de Configuração Streamlit

```bash
mkdir -p ~/.streamlit

cat > ~/.streamlit/config.toml << EOF
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
serverAddress = "localhost"
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF
```

#### 10.2 Executar Interface

**Método 1: Script de inicialização**
```bash
cd /opt/sact/Streamlit
./run.sh
```

**Método 2: Comando direto**
```bash
cd /opt/sact/Streamlit
streamlit run app.py
```

**Método 3: Módulo Python**
```bash
cd /opt/sact/Streamlit
python3 -m streamlit run app.py
```

#### 10.3 Acessar Interface

Abra o navegador em: `http://localhost:8501`

### Passo 11: Configurar Acesso Remoto (Opcional)

Para acessar de outros computadores na rede:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Acesse via: `http://[IP_DO_SERVIDOR]:8501`

---

## Verificação da Instalação

### Checklist de Verificação

#### 1. Banco de Dados

```bash
# Verificar conexão
psql -U sact_user -d sact -c "SELECT version();"

# Verificar schemas
psql -U sact_user -d sact -c "\dn"

# Verificar tabelas principais
psql -U sact_user -d sact -c "
SELECT 
    schemaname, 
    tablename 
FROM pg_tables 
WHERE schemaname IN ('core', 'cte', 'ibge', 'analytics')
ORDER BY schemaname, tablename;
"
```

#### 2. Dados IBGE

```bash
psql -U sact_user -d sact << EOF
SELECT 'UFs carregadas:', COUNT(*) FROM ibge.uf;
SELECT 'Municípios carregados:', COUNT(*) FROM ibge.municipio;
SELECT 'Municípios com coordenadas:', COUNT(*) 
FROM ibge.municipio 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
EOF
```

#### 3. Dependências Python

```bash
python3 << EOF
import sys
print(f"Python: {sys.version}")

modules = [
    'psycopg2',
    'requests',
    'streamlit',
    'pandas',
    'plotly'
]

for mod in modules:
    try:
        __import__(mod)
        print(f"  {mod}: OK")
    except ImportError:
        print(f"  {mod}: FALTANDO")
EOF
```

#### 4. Estrutura de Diretórios

```bash
ls -la /opt/sact/ | grep -E "Config|Database|cte_extractor|Streamlit"
```

#### 5. Teste de Processamento

```bash
python3 << EOF
from Database.main import CTEMainApplication
from Config.database_config import validate_config

try:
    validate_config()
    print("Configuração: OK")
    
    app = CTEMainApplication()
    print("Aplicação: OK")
    
    print("\nSistema pronto para uso!")
except Exception as e:
    print(f"Erro: {e}")
EOF
```

---

## Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com PostgreSQL

**Sintoma:**
```
psycopg2.OperationalError: could not connect to server
```

**Solução:**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Reiniciar se necessário
sudo systemctl restart postgresql

# Verificar configurações de acesso
sudo cat /etc/postgresql/*/main/pg_hba.conf

# Adicionar se necessário:
# local   all   sact_user   md5
```

#### 2. Extensões Faltando

**Sintoma:**
```
ERROR: function unaccent(text) does not exist
```

**Solução:**
```bash
psql -U postgres -d sact << EOF
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF
```

#### 3. Dependências Python Faltando

**Sintoma:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solução:**
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Reinstalar dependências
pip install -r requirements.txt
```

#### 4. Erro ao Carregar IBGE

**Sintoma:**
```
requests.exceptions.ConnectionError
```

**Solução:**
- Verificar conexão com internet
- Tentar novamente (pode ser timeout temporário)
- Verificar firewall/proxy

#### 5. Streamlit Não Inicia

**Sintoma:**
```
OSError: [Errno 48] Address already in use
```

**Solução:**
```bash
# Verificar processos usando porta 8501
lsof -i :8501

# Matar processo se necessário
kill -9 [PID]

# Ou usar porta alternativa
streamlit run app.py --server.port 8502
```

### Logs e Debug

#### Habilitar Logs Detalhados

```python
# Adicionar no início do script
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/var/log/sact/app.log'
)
```

#### Verificar Logs PostgreSQL

```bash
# Ubuntu/Debian
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# CentOS/RHEL
sudo tail -f /var/lib/pgsql/data/log/postgresql-*.log
```

---

## Manutenção

### Backup do Banco de Dados

#### Backup Completo

```bash
# Backup
pg_dump -U sact_user -d sact -F c -f /backup/sact_$(date +%Y%m%d).backup

# Restore
pg_restore -U sact_user -d sact -c /backup/sact_YYYYMMDD.backup
```

#### Backup Apenas Dados

```bash
# Backup
pg_dump -U sact_user -d sact --data-only -f /backup/sact_data_$(date +%Y%m%d).sql

# Restore
psql -U sact_user -d sact -f /backup/sact_data_YYYYMMDD.sql
```

### Atualização do Sistema

#### 1. Atualizar Código

```bash
cd /opt/sact
git pull  # Se usando git
# ou copiar novos arquivos
```

#### 2. Atualizar Dependências

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

#### 3. Aplicar Migrações

```bash
cd /opt/sact/Database/migrations
for file in *.sql; do
    psql -U sact_user -d sact -f "$file"
done
```

#### 4. Recriar Views

```bash
python3 << EOF
from Database.main import CTEMainApplication
app = CTEMainApplication()
app.criar_views_analiticas()
EOF
```

### Monitoramento

#### Verificar Tamanho do Banco

```sql
SELECT 
    pg_size_pretty(pg_database_size('sact')) as tamanho_banco,
    pg_size_pretty(pg_total_relation_size('cte.documento')) as tamanho_cte;
```

#### Verificar Performance

```sql
-- Queries mais lentas
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### Limpeza de Dados Antigos

```sql
-- Exemplo: deletar CT-es com mais de 2 anos
DELETE FROM cte.documento 
WHERE data_emissao < NOW() - INTERVAL '2 years';

-- Vacuum após deleções grandes
VACUUM ANALYZE cte.documento;
```

---

## Automação

### Script de Inicialização Completa

Criar `install.sh`:

```bash
#!/bin/bash
set -e

echo "=== Instalação do Sistema SACT ==="

# 1. Criar ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Criar banco de dados
echo "Criando banco de dados..."
sudo -u postgres psql << EOF
CREATE USER sact_user WITH PASSWORD 'senha_segura';
CREATE DATABASE sact OWNER sact_user;
\c sact
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF

# 4. Criar estrutura
echo "Criando estrutura do banco..."
psql -U sact_user -d sact -f estrutura.sql

# 5. Carregar dados IBGE
echo "Carregando dados IBGE..."
python3 ibge_loader.py

# 6. Verificar instalação
echo "Verificando instalação..."
python3 << EOF
from Config.database_config import validate_config
from Database.main import CTEMainApplication
validate_config()
app = CTEMainApplication()
print("Instalação concluída com sucesso!")
EOF

echo "=== Sistema pronto para uso ==="
echo "Execute: cd Streamlit && streamlit run app.py"
```

### Executar Instalação

```bash
chmod +x install.sh
sudo ./install.sh
```

---

## Contato e Suporte

Para dúvidas, problemas ou sugestões:

- Documentação completa: `/opt/sact/docs/`
- Logs do sistema: `/var/log/sact/`
- Feedback via interface: Menu "Feedback" no Streamlit

---

**Versão:** 1.0.0  
**Data:** Novembro 2025  
**Última atualização:** 18/11/2025
