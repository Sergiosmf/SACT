# Configuração de Testes - Banco de Dados

## ✅ Configuração Concluída

Os testes agora estão configurados para usar o banco de dados **`sact_test`** automaticamente.

---

## 🗄️ Banco de Testes

### Informações do Banco
- **Nome:** `sact_test`
- **Usuário:** `sergiomendes`
- **Host:** `localhost`
- **Porta:** `5432`
- **Senha:** (vazia - autenticação local)

### Schemas Criados
```
✅ analytics
✅ core
✅ cte
✅ ibge
✅ public
✅ staging
```

### Tabelas no Schema CTE
```
✅ cte.carga
✅ cte.documento
✅ cte.documento_parte
```

---

## ⚙️ Como Funciona

### 1. Configuração Automática
O arquivo `Tests/conftest.py` configura automaticamente as variáveis de ambiente antes de executar os testes:

```python
def configure_test_environment():
    """Configura ambiente de testes para usar sact_test"""
    os.environ['DB_NAME'] = 'sact_test'
    os.environ['DB_USER'] = 'sergiomendes'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '5432'
    os.environ['DB_PASSWORD'] = ''
    os.environ['ENVIRONMENT'] = 'testing'
```

### 2. Prioridade de Configuração
O `Config/database_config.py` foi modificado para respeitar variáveis de ambiente já definidas:

```python
def load_env_file():
    """Carrega .env mas respeita variáveis já definidas"""
    # Só define se ainda não existir (permite override por testes)
    if key not in os.environ:
        os.environ[key] = value
```

### 3. Verificação de Segurança
Os testes verificam automaticamente se estão usando o banco correto:

```python
@pytest.fixture(scope="session")
def db_config():
    assert DATABASE_CONFIG['database'] == 'sact_test', \
        f"ERRO: Testes devem usar 'sact_test'"
```

---

## 🚀 Executando os Testes

### Comando Simples
```bash
cd Tests
python generate_report.py
```

### Saída Esperada
```
================================================================================
🧪 SUITE DE TESTES CT-e
================================================================================
🗄️  Banco de Dados: sact_test
👤 Usuário: sergiomendes
🖥️  Host: localhost:5432
🔬 Ambiente: TESTING
================================================================================
```

### Comandos Alternativos

```bash
# Todos os testes
pytest

# Apenas unitários
pytest unitarios/

# Apenas funcionais
pytest funcionais/

# Apenas integração
pytest integracao/

# Teste específico
pytest unitarios/test_unitarios.py::TestPersistenciaDados::test_conectar_banco -v
```

---

## 📊 Resultados Atuais

### Última Execução
- **Data:** 13/11/2025 10:08:08
- **Total de Testes:** 24
- **Aprovados:** 24 (100%)
- **Reprovados:** 0
- **Duração:** 0.4s

### Por Categoria
| Categoria | Testes | Status | Duração |
|-----------|--------|--------|---------|
| Unitários | 18 | ✅ 100% | 0.19s |
| Funcionais | 4 | ✅ 100% | 0.10s |
| Integração | 2 | ✅ 100% | 0.11s |

---

## 🔒 Segurança

### Isolamento de Dados
- ✅ Testes usam banco **separado** (`sact_test`)
- ✅ Dados de **produção** (`sact`) permanecem intocados
- ✅ Não há risco de **corromper dados reais**

### Verificações
- ✅ Asserção automática do banco correto
- ✅ Mensagem clara no início dos testes
- ✅ Falha imediata se banco errado

---

## 🗃️ Arquivos Relevantes

### Configuração
```
Config/
  ├── .env              # Configuração de produção (sact)
  ├── .env.test         # Configuração de testes (sact_test)
  └── database_config.py # Módulo de configuração

Tests/
  └── conftest.py       # Configuração de fixtures e ambiente
```

### Relatórios
```
Tests/resultados/
  ├── report_YYYYMMDD_HHMMSS.json
  ├── report_YYYYMMDD_HHMMSS.md
  ├── summary_YYYYMMDD_HHMMSS.md
  ├── table_YYYYMMDD_HHMMSS.tex
  ├── latest_report.json -> report_*.json
  └── latest_report.md -> report_*.md
```

---

## 🔄 Manutenção

### Resetar Banco de Testes
Se precisar limpar os dados de teste:

```bash
# Conectar ao banco
psql -U sergiomendes -d sact_test

# Limpar dados (preserva estrutura)
TRUNCATE cte.documento CASCADE;
TRUNCATE cte.carga CASCADE;
TRUNCATE cte.documento_parte CASCADE;
```

### Recriar Banco de Testes
Se precisar recriar completamente:

```bash
# Dropar banco
psql -U sergiomendes -d postgres -c "DROP DATABASE IF EXISTS sact_test;"

# Criar novo banco
psql -U sergiomendes -d postgres -c "CREATE DATABASE sact_test;"

# Restaurar estrutura
psql -U sergiomendes -d sact_test -f estrutura.sql
```

---

## ✅ Checklist de Verificação

Antes de executar testes:
- [x] Banco `sact_test` existe
- [x] Schemas criados (core, cte, ibge, analytics, staging)
- [x] Tabelas criadas no schema cte
- [x] Dados IBGE populados (UFs e municípios básicos)
- [x] Configuração de ambiente correta
- [x] Verificação de segurança ativa

---

## 📝 Notas Importantes

1. **Sempre use `sact_test` para testes**
   - NUNCA execute testes no banco `sact` (produção)

2. **Verificação automática**
   - Os testes falham imediatamente se detectarem banco errado

3. **Isolamento completo**
   - Testes não afetam dados de produção
   - Cada execução é independente

4. **Performance**
   - 24 testes em ~0.4 segundos
   - Banco local otimizado para testes rápidos

---

**Configuração validada em:** 13 de novembro de 2025  
**Status:** ✅ Totalmente funcional  
**Próxima revisão:** Conforme necessário
