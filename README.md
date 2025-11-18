# Sistema SACT - Sistema de Análise de CT-e e Transporte

## Sobre o Sistema

O SACT é uma solução completa para processamento, armazenamento e análise de Conhecimentos de Transporte Eletrônico (CT-e). O sistema automatiza a extração de dados de arquivos XML da SEFAZ, realiza cálculos de quilometragem, custos operacionais e oferece análises detalhadas através de dashboards interativos.

## Características Principais

- **Processamento Automático de CT-e**: Extração de dados de arquivos XML padrão SEFAZ
- **Cálculo de Quilometragem**: Integração com dados IBGE para cálculo preciso de distâncias
- **Análise de Rentabilidade**: Métricas de custo por quilômetro, rendimento por veículo
- **Gestão de Frota**: Controle de veículos, rotas e operações
- **Dashboards Interativos**: Visualizações gráficas e relatórios em tempo real
- **Rastreabilidade Completa**: Histórico detalhado de todas as operações
- **Views Analíticas**: Consultas otimizadas pré-calculadas para análises rápidas

## Tecnologias Utilizadas

### Backend
- **Python 3.8+**: Linguagem principal
- **PostgreSQL 12+**: Banco de dados relacional
- **psycopg2**: Conector Python-PostgreSQL

### Frontend
- **Streamlit**: Framework para interface web
- **Plotly**: Biblioteca de visualização de dados
- **Pandas**: Manipulação e análise de dados

### Integrações
- **API IBGE**: Dados oficiais de municípios e UFs
- **GitHub Dataset**: Coordenadas geográficas dos municípios

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Web (Streamlit)                │
│  - Dashboards Interativos                                   │
│  - Formulários de Entrada                                   │
│  - Visualizações Gráficas                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Camada de Aplicação (Python)                   │
│  - CTEMainApplication (Orquestrador)                        │
│  - Managers (Database, File, Stats)                         │
│  - Services (Business Logic)                                │
│  - Repositories (Data Access)                               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│           Camada de Extração (cte_extractor)                │
│  - XML Parser                                               │
│  - Data Validators                                          │
│  - Data Transformers                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Banco de Dados (PostgreSQL)                    │
│  Schemas:                                                   │
│  - core: Dados mestre (empresas, clientes, veículos)       │
│  - cte: Documentos fiscais (CT-e, cargas)                  │
│  - ibge: Dados geográficos (UF, municípios)                │
│  - analytics: Views analíticas pré-calculadas              │
└─────────────────────────────────────────────────────────────┘
```

## Estrutura do Projeto

```
SACT/
├── Config/                      # Configurações do sistema
│   ├── database_config.py       # Configurações de banco
│   └── __init__.py
│
├── Database/                    # Camada de aplicação
│   ├── main.py                  # Aplicação principal
│   ├── managers/                # Gerenciadores
│   │   ├── database_manager.py # Gerenciador de banco
│   │   ├── file_manager.py     # Gerenciador de arquivos
│   │   └── stats_manager.py    # Gerenciador de estatísticas
│   ├── services/                # Lógica de negócio
│   ├── repositories/            # Acesso a dados
│   ├── migrations/              # Scripts de migração
│   └── views/                   # Definições de views
│
├── cte_extractor/               # Extrator de CT-e
│   ├── extractors.py            # Extratores XML
│   ├── strategies.py            # Estratégias de extração
│   ├── models.py                # Modelos de dados
│   ├── utils.py                 # Utilitários
│   └── __init__.py
│
├── Streamlit/                   # Interface web
│   ├── app.py                   # Aplicação principal
│   ├── components/              # Componentes UI
│   │   ├── operacao_transporte.py
│   │   ├── rentabilidade_custos.py
│   │   └── feedback.py
│   ├── utils/                   # Utilitários UI
│   └── feedback/                # Feedbacks dos usuários
│
├── Tests/                       # Testes automatizados
│   ├── unitarios/               # Testes unitários
│   ├── integracao/              # Testes de integração
│   └── funcionais/              # Testes funcionais
│
├── docs/                        # Documentação técnica
│   ├── CODING_GUIDELINES.md
│   ├── CTE_EXTRACTOR_DOCUMENTATION.md
│   └── ...
│
├── estrutura.sql                # Schema completo do banco
├── ibge_loader.py               # Carregador dados IBGE
├── requirements.txt             # Dependências Python
├── INSTALACAO.md                # Guia de instalação detalhado
└── README.md                    # Este arquivo
```

## Instalação

Para instruções detalhadas de instalação e configuração, consulte:

**[INSTALACAO.md](INSTALACAO.md)** - Guia completo passo a passo

### Resumo de Instalação

1. **Pré-requisitos**: PostgreSQL 12+, Python 3.8+
2. **Criar banco de dados e estrutura**: `psql -f estrutura.sql`
3. **Instalar dependências Python**: `pip install -r requirements.txt`
4. **Carregar dados IBGE**: `python3 ibge_loader.py`
5. **Configurar conexão**: Editar `Config/database_config.py`
6. **Processar CT-e**: Via interface ou linha de comando
7. **Executar interface**: `streamlit run Streamlit/app.py`

## Uso Rápido

### Processar CT-e via Interface Web

```bash
cd Streamlit
streamlit run app.py
```

Acesse `http://localhost:8501` e siga as instruções na interface.

### Processar CT-e via Python

```python
from Database.main import CTEMainApplication

# Inicializar sistema
app = CTEMainApplication()

# Processar diretório com XMLs
app.processar_diretorio(
    diretorio="/caminho/para/xmls",
    custo_por_km=3.50
)

# Criar views analíticas
app.criar_views_analiticas()
```

### Consultas Analíticas

```sql
-- Resumo completo de CT-e
SELECT * FROM analytics.vw_cte_resumo LIMIT 10;

-- Performance da frota
SELECT * FROM analytics.vw_performance_frota;

-- Rotas mais frequentes
SELECT * FROM analytics.vw_rotas_frequentes;

-- Rentabilidade mensal
SELECT * FROM analytics.vw_rentabilidade_mensal;
```

## Funcionalidades

### 1. Processamento de CT-e
- Leitura automática de arquivos XML
- Extração de dados fiscais e operacionais
- Validação de estrutura e dados
- Armazenamento normalizado no banco

### 2. Cálculo de Quilometragem
- Integração com base de municípios IBGE
- Cálculo automático de distâncias
- Suporte a coordenadas geográficas
- Fallback para municípios sem coordenadas

### 3. Análise Operacional
- Controle de frota por veículo
- Análise de rotas e destinos
- Frequência de operações
- Tempo médio de viagem

### 4. Análise Financeira
- Custo por quilômetro
- Rendimento por veículo
- Faturamento por rota
- Margem de lucro por operação

### 5. Dashboards
- KPIs principais (faturamento, viagens, km)
- Gráficos temporais de evolução
- Mapas de origem e destino
- Ranking de veículos e rotas

### 6. Sistema de Feedback
- Coleta de sugestões dos usuários
- Categorização de feedbacks
- Armazenamento estruturado
- Estatísticas de uso

## Comandos Úteis

### Banco de Dados

```bash
# Backup completo
pg_dump -U sact_user -d sact -F c -f backup_sact.backup

# Restore
pg_restore -U sact_user -d sact -c backup_sact.backup

# Conectar ao banco
psql -U sact_user -d sact

# Verificar tamanho
psql -U sact_user -d sact -c "SELECT pg_size_pretty(pg_database_size('sact'));"
```

### Python

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar testes
cd Tests
python run_all_tests.py
```

### Streamlit

```bash
# Executar interface
streamlit run Streamlit/app.py

# Executar em porta específica
streamlit run Streamlit/app.py --server.port 8502

# Executar permitindo acesso externo
streamlit run Streamlit/app.py --server.address 0.0.0.0
```

## Requisitos de Sistema

### Hardware Mínimo
- CPU: 2 cores, 2.0 GHz
- RAM: 4 GB (8 GB recomendado)
- Disco: 10 GB livres
- Conexão com internet (para carga inicial)

### Software Obrigatório
- Python 3.8+
- PostgreSQL 12+
- pip (gerenciador de pacotes Python)
- Sistema Operacional: Linux, macOS ou Windows 10+

## Dependências Python

```
psycopg2-binary>=2.9.0    # Conector PostgreSQL
requests>=2.28.0          # Cliente HTTP
streamlit>=1.28.0         # Framework web
pandas>=1.5.0             # Análise de dados
plotly>=5.14.0            # Visualização
python-dotenv>=1.0.0      # Variáveis de ambiente
```

## Extensões PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;  -- Normalização de texto
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- Busca por similaridade
```

## Schemas do Banco de Dados

### core - Dados Mestre
- `empresa`: Informações da empresa
- `pessoa`: Cadastro de pessoas (clientes, fornecedores)
- `veiculo`: Frota de veículos
- `motorista`: Cadastro de motoristas

### cte - Documentos Fiscais
- `documento`: CT-e processados
- `carga`: Cargas transportadas
- `documento_parte`: Relacionamento documento-pessoa

### ibge - Dados Geográficos
- `uf`: Unidades federativas (27 estados)
- `municipio`: Municípios brasileiros (5.571)
  - Inclui coordenadas geográficas

### analytics - Views Analíticas
- `vw_cte_resumo`: Resumo completo de CT-e
- `vw_performance_frota`: Performance de veículos
- `vw_rotas_frequentes`: Análise de rotas
- `vw_rentabilidade_mensal`: Métricas financeiras
- Mais de 20 views especializadas

## Segurança

### Banco de Dados
- Use senhas fortes para usuários
- Restrinja acesso à rede (pg_hba.conf)
- Habilite SSL para conexões remotas
- Faça backups regulares

### Aplicação
- Use variáveis de ambiente para credenciais
- Não commite senhas no código
- Mantenha dependências atualizadas
- Valide inputs de usuários

### Arquivo .env (Recomendado)
```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=sact
PGUSER=sact_user
PGPASSWORD=sua_senha_segura_aqui
```

## Performance

### Otimizações Implementadas
- Índices em campos chave (chave CT-e, placas, datas)
- Views materializadas para consultas complexas
- Batch inserts para processamento em lote
- Conexão pool para reutilização de conexões
- Cache de consultas frequentes

### Recomendações
- Execute VACUUM periodicamente
- Monitore queries lentas (pg_stat_statements)
- Ajuste parâmetros PostgreSQL conforme volume
- Use particionamento para tabelas grandes

## Troubleshooting

### Problemas Comuns

**Erro de conexão PostgreSQL**
```bash
# Verificar se está rodando
sudo systemctl status postgresql

# Reiniciar
sudo systemctl restart postgresql
```

**Módulos Python faltando**
```bash
# Reinstalar dependências
pip install -r requirements.txt
```

**Porta do Streamlit ocupada**
```bash
# Usar porta alternativa
streamlit run app.py --server.port 8502
```

Para mais detalhes, consulte a seção Troubleshooting em [INSTALACAO.md](INSTALACAO.md).

## Testes

### Executar Todos os Testes
```bash
cd Tests
python run_all_tests.py
```

### Testes por Categoria
```bash
# Testes unitários
pytest Tests/unitarios/

# Testes de integração
pytest Tests/integracao/

# Testes funcionais
pytest Tests/funcionais/
```

## Documentação

### Documentos Disponíveis
- `INSTALACAO.md` - Guia completo de instalação
- `docs/CODING_GUIDELINES.md` - Padrões de código
- `docs/CTE_EXTRACTOR_DOCUMENTATION.md` - Documentação do extrator
- `docs/DOCUMENTACAO_TECNICA_COMPLETA.md` - Documentação técnica
- `docs/GUIA_VIEWS_ANALITICAS.md` - Guia das views analíticas

## Manutenção

### Backup Regular
```bash
# Script de backup diário
#!/bin/bash
BACKUP_DIR="/backup/sact"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U sact_user -d sact -F c -f "$BACKUP_DIR/sact_$DATE.backup"
find "$BACKUP_DIR" -name "*.backup" -mtime +30 -delete
```

### Monitoramento
```sql
-- Tamanho do banco
SELECT pg_size_pretty(pg_database_size('sact'));

-- Tabelas maiores
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname IN ('core', 'cte', 'ibge')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Consultas lentas
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Roadmap

### Próximas Funcionalidades
- [ ] Exportação de relatórios em PDF/Excel
- [ ] API REST para integração externa
- [ ] Notificações por email/webhook
- [ ] Análise preditiva com machine learning
- [ ] Integração com sistemas ERP
- [ ] App mobile para consultas
- [ ] Autenticação multi-usuário
- [ ] Auditoria completa de operações

## Contribuindo

### Para Desenvolvedores
1. Fork o projeto
2. Crie uma branch para sua feature
3. Siga os padrões de código em `docs/CODING_GUIDELINES.md`
4. Adicione testes para novas funcionalidades
5. Submeta um Pull Request

### Padrões de Código
- PEP 8 para Python
- Docstrings em todas as funções
- Type hints quando aplicável
- Cobertura de testes > 80%

## Licença

Este projeto é proprietário e confidencial.

## Suporte

Para dúvidas, problemas ou sugestões:
- Use o sistema de Feedback integrado na interface
- Consulte a documentação em `docs/`
- Verifique os logs em `/var/log/sact/`

## Changelog

### Versão 1.0.0 (Novembro 2025)
- Lançamento inicial do sistema
- Processamento automático de CT-e
- Integração com dados IBGE
- Cálculo de quilometragem com coordenadas
- Interface web Streamlit
- Dashboards analíticos
- Sistema de feedback
- Views analíticas otimizadas

---

**Desenvolvido por**: Sérgio Mendes  
**Data**: Novembro 2025  
**Versão**: 1.0.0  
**Última atualização**: 18/11/2025
