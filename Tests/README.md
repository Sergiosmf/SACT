# 🧪 Suite de Testes - Sistema CT-e

Suite completa de testes para o sistema de processamento de CT-e (Conhecimento de Transporte Eletrônico).

## 📋 Estrutura dos Testes

A suite está organizada em **três categorias principais**, conforme solicitado:

### (I) **Testes Unitários** 📦
Verificação das **funções críticas** de leitura, validação e persistência de dados.

**Localização:** `unitarios/test_unitarios.py`

**Cobertura:**
- ✅ **Leitura de XML**: Parsing, extração de chave CT-e, número, emitente
- ✅ **Validação de Dados**: CNPJ, CPF, chave CT-e, campos obrigatórios
- ✅ **CTE Extractor**: Funcionamento do módulo `cte_extractor`
- ✅ **Persistência**: Operações CRUD no banco de dados

### (II) **Testes Funcionais** 🔄
Execução de **fluxos completos** de importação e processamento de lotes de XML.

**Localização:** `funcionais/test_funcionais.py`

**Cobertura:**
- ✅ **Processamento de Lote**: 1 arquivo, 5 arquivos, geração de relatórios
- ✅ **Fluxo Completo**: Descoberta → Extração → Validação → Relatório
- ✅ **Pipeline com Persistência**: Extração → Transformação → Persistência → Verificação

### (III) **Testes de Integração** 🔗
Avaliação da **interoperabilidade entre as quatro camadas** do sistema.

**Localização:** `integracao/test_integracao.py`

**Cobertura:**
- ✅ **4 Camadas Completas**:
  1. **Upload/Descoberta**: Localização de arquivos XML
  2. **Extração**: Uso do `cte_extractor.CTEFacade`
  3. **Parsing/Transformação**: Processamento dos dados
  4. **Persistência**: Gravação no banco PostgreSQL
- ✅ **Verificação de Integridade**: Validação de dados entre camadas
- ✅ **Processamento em Lote**: Múltiplos arquivos através das 4 camadas

## 🚀 Como Executar

### Pré-requisitos

1. **Instalar dependências:**
```bash
cd Tests
pip install -r requirements-test.txt
```

2. **Configurar banco de dados** (para testes de integração):
   - PostgreSQL configurado
   - Módulo `Config.database_config` disponível
   - Schemas: `cte`, `core`, `ibge`

3. **Preparar arquivos de teste:**
   - XMLs válidos de CT-e em: `/Users/sergiomendes/Documents/CT-e/mes_1_2025/CT-e/Autorizados/`

### Executar TODOS os Testes

```bash
cd Tests
python run_all_tests.py
```

### Executar por Categoria

```bash
# Apenas unitários
pytest unitarios/ -v

# Apenas funcionais
pytest funcionais/ -v

# Apenas integração
pytest integracao/ -v
```

### Executar com Filtros

```bash
# Pular testes que requerem banco de dados
pytest -m "not database"

# Apenas testes rápidos (não marcados como lento)
pytest -m "not lento"

# Apenas testes de XML
pytest -m xml

# Categoria + filtro
pytest unitarios/ -m "not database" -v
```

## 🏷️ Marcadores (Markers)

Os testes utilizam marcadores pytest para organização:

- `@pytest.mark.unitario` - Testes unitários
- `@pytest.mark.funcional` - Testes funcionais
- `@pytest.mark.integracao` - Testes de integração
- `@pytest.mark.database` - Requer conexão com banco
- `@pytest.mark.xml` - Processa arquivos XML
- `@pytest.mark.lento` - Testes demorados

## 📊 Relatórios

### Geração Automática de Relatórios Completos

**🆕 NOVO:** Sistema de relatórios detalhados para artigos científicos!

```bash
python generate_report.py
```

Este comando gera **4 formatos diferentes** de relatório:

1. **JSON Completo** (`report_YYYYMMDD_HHMMSS.json`)
   - Todos os dados brutos e métricas
   - Ideal para processamento automatizado

2. **Markdown Formatado** (`report_YYYYMMDD_HHMMSS.md`)
   - Documentação legível
   - Métricas de qualidade
   - Resultados por categoria

3. **Sumário Executivo** (`summary_YYYYMMDD_HHMMSS.md`)
   - Versão condensada para artigos
   - Conclusões e recomendações
   - Tabelas resumidas

4. **Tabela LaTeX** (`table_YYYYMMDD_HHMMSS.tex`)
   - Formatação LaTeX pronta para copiar
   - Ideal para artigos acadêmicos

**Localização:** `resultados/`

**Links simbólicos:**
- `latest_report.json` → último relatório JSON
- `latest_report.md` → último relatório Markdown

### Métricas Coletadas

- ✅ **Cobertura:** Total de testes, aprovados, reprovados
- ⏱️ **Performance:** Duração total e média por teste
- 📈 **Qualidade:** Confiabilidade, eficiência, completude
- 📊 **Estatísticas por Categoria:** Unitários, funcionais, integração

### Como Usar nos Resultados do Artigo

📖 **Consulte o guia completo:** [GUIA_RELATORIOS.md](GUIA_RELATORIOS.md)

**Exemplo de tabela para artigo:**

| Categoria | Testes | Aprovados | Taxa de Sucesso | Duração |
|-----------|--------|-----------|-----------------|---------|
| Unitários | 45 | 45 | 100% | 1.2s |
| Funcionais | 38 | 36 | 94.7% | 2.8s |
| Integração | 35 | 33 | 94.3% | 3.5s |
| **Total** | **118** | **114** | **96.6%** | **7.5s** |

### Relatórios de Teste Individuais

Os testes também **geram relatórios específicos** em formato JSON:

**Tipos de relatório individual:**
- `unitarios_*.json` - Resultados de testes unitários
- `funcionais_lote_*.json` - Processamento de lotes
- `funcionais_pipeline_*.json` - Fluxo completo de pipeline
- `integracao_4_camadas_*.json` - Integração das 4 camadas
- `integracao_lote_*.json` - Lote através das 4 camadas

## 🛠️ Configuração

### pytest.ini

Configuração principal do pytest:
- Diretórios de teste: `unitarios/`, `funcionais/`, `integracao/`
- Marcadores personalizados
- Logging habilitado

### conftest.py

Fixtures compartilhadas:
- `sample_xml_path` - Caminho para XML de teste
- `sample_xml_dir` - Diretório com XMLs
- `db_connection` - Conexão com PostgreSQL
- `temp_dir` - Diretório temporário
- `results_dir` - Diretório para relatórios
- `test_timestamp` - Timestamp único por teste

## ⚠️ Observações Importantes

### Testes com Banco de Dados

Testes marcados com `@pytest.mark.database` requerem:
- PostgreSQL em execução
- Credenciais configuradas em `Config.database_config`
- Schemas `cte`, `core`, `ibge` criados

**Se o banco não estiver disponível**, esses testes serão **automaticamente pulados** (skip).

### Arquivos XML de Teste

Os testes buscam XMLs em:
1. `/Users/sergiomendes/Documents/CT-e/mes_1_2025/CT-e/Autorizados/`
2. Diretórios alternativos (fallback)

Se não encontrar arquivos, alguns testes serão pulados.

## 📈 Exemplo de Execução

```bash
$ python run_all_tests.py

================================================================================
🎯 EXECUÇÃO COMPLETA DE TESTES
================================================================================
⏰ Início: 2025-01-28 15:30:00

================================================================================
🧪 TESTES UNITÁRIOS
================================================================================
Comando: python -m pytest unitarios/ -v --tb=short

unitarios/test_unitarios.py::TestLeituraXML::test_xml_bem_formado PASSED
unitarios/test_unitarios.py::TestLeituraXML::test_extrair_chave_cte PASSED
unitarios/test_unitarios.py::TestValidacaoDados::test_validar_cnpj PASSED
unitarios/test_unitarios.py::TestValidacaoDados::test_validar_cpf PASSED
...

================================================================================
🧪 TESTES FUNCIONAIS
================================================================================
...

================================================================================
🧪 TESTES DE INTEGRAÇÃO
================================================================================
...

================================================================================
📊 RELATÓRIO FINAL
================================================================================
UNITARIOS            : ✅ PASSOU
FUNCIONAIS           : ✅ PASSOU
INTEGRACAO           : ✅ PASSOU
================================================================================
Total: 3/3 categorias passaram
⏰ Fim: 2025-01-28 15:35:00
================================================================================
```

## 🤝 Contribuindo

Para adicionar novos testes:

1. Coloque no diretório apropriado (`unitarios/`, `funcionais/`, `integracao/`)
2. Use os marcadores corretos (`@pytest.mark.*`)
3. Reutilize fixtures do `conftest.py`
4. Gere relatórios JSON quando apropriado
5. Execute `python run_all_tests.py` para validar

## 📝 Notas Técnicas

- **Framework**: pytest ≥ 7.4.0
- **Banco de Dados**: PostgreSQL com psycopg ≥ 3.1.0
- **Python**: 3.9+
- **Módulo Principal**: `cte_extractor`
- **Namespace XML**: `http://www.portalfiscal.inf.br/cte`

---

**Última atualização:** 2025-01-28  
**Versão:** 2.0  
**Autor:** Sistema SACT
