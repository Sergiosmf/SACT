# 🗄️ Database - Sistema de Banco de Dados

Esta pasta contém todos os componentes relacionados ao banco de dados PostgreSQL do SACT.

## 📁 **ARQUIVOS PRINCIPAIS**

| Arquivo | Descrição |
|---------|-----------|
| **main.py** | 🚀 **ENTRY POINT PRINCIPAL** - Sistema modular ETL |
| **managers/** | 🔧 Gerenciadores (DB, arquivos, estatísticas) |
| **services/** | 💼 Serviços de negócio (ETL, cálculos) |
| **views/** | 📊 Gerenciamento das views analíticas |
| **repositories/** | 🗄️ Camada de acesso a dados (futuro) |
| **schema_cte_ibge_postgres.sql** | Estrutura completa do banco PostgreSQL |
| **ibge_loader.py** | Carregador de dados geográficos IBGE |
| **desc.tabelas.txt** | Documentação das tabelas |

## 🚀 **COMO USAR**

### **1. 🔧 Setup Inicial do Banco**
```bash
# Criar o schema (apenas uma vez)
psql -U sergiomendes -h localhost -d sact -f schema_cte_ibge_postgres.sql

# Carregar dados IBGE (apenas uma vez)
python ibge_loader.py
```

### **2. 🔄 Processar CT-e (Uso Regular)**
```bash
```bash
# Executar sistema ETL modular
python main.py

# OU executar versão legado (se necessário)
python ../Legacy/alimentar_banco_cte.py
```
```

## 🗄️ **ESTRUTURA DO BANCO**

### **Schemas:**
- **core**: Entidades principais (pessoa, endereço, veículo)
- **cte**: Dados específicos de CT-e (documento, carga)
- **ibge**: Dados geográficos (município, UF)
- **public**: Views analíticas

### **Principais Tabelas:**
- `core.pessoa` - Pessoas físicas e jurídicas
- `core.endereco` - Endereços normalizados
- `core.veiculo` - Frota de veículos
- `cte.documento` - CT-e processadas
- `cte.carga` - Cargas transportadas
- `ibge.municipio` - Municípios brasileiros
- `ibge.uf` - Estados e regiões

## 📊 **VIEWS ANALÍTICAS**

O sistema cria automaticamente 7 views para análise:
- vw_dashboard_executivo
- vw_cte_resumo
- vw_analise_rotas
- vw_ranking_produtos
- vw_analise_temporal
- vw_eficiencia_logistica
- vw_rendimento_caminhoes_mensal

## 🔧 **CONFIGURAÇÃO**

As configurações de conexão estão em:
- `../Config/database_config.py`
- `../Config/.env`

## 📈 **STATUS ATUAL**

- ✅ **1.659+ CT-e** processadas
- ✅ **99.2% de sucesso** na carga
- ✅ **Integridade referencial** mantida
- ✅ **7 views analíticas** funcionais

---
**💡 Execute `python main.py` para processar novos lotes de CT-e com sistema modular**