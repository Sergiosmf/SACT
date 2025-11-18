# 🚛 Interface Streamlit - Sistema CT-e

## Camada de Visualização

Esta é a **Camada de Visualização** do Sistema CT-e, desenvolvida em Streamlit e integrada com a **Camada de Aplicação** (`main.py`).

## 🎯 Funcionalidades

A interface engloba todo o fluxo do sistema CT-e:

1. **📋 Validação de Configuração**
   - Status da conexão com PostgreSQL
   - Verificação de credenciais e configurações

2. **📁 Seleção de Diretório**
   - Interface para inserir caminho dos arquivos XML
   - Validação automática de diretórios e arquivos
   - Contagem de arquivos CT-e encontrados

3. **⚙️ Configuração de Parâmetros**
   - Definição do custo por quilômetro
   - Parâmetros para cálculos de rendimento

4. **🚀 Processamento Completo**
   - Execução integrada com `CTEMainApplication`
   - Feedback em tempo real do processamento
   - Logs detalhados de cada etapa
   - Barra de progresso visual

5. **📊 Visualização de Dados**
   - Dashboard executivo com KPIs principais
   - Análises temporais e de valores
   - Mapeamento de rotas e distribuição geográfica
   - Análise de produtos transportados

6. **💬 Feedback do Usuário** ⭐ **NOVO!**
   - Formulário para sugestões e comentários
   - Categorização de feedback (Bug, Nova Funcionalidade, etc.)
   - Salvamento automático em arquivos .txt
   - Estatísticas de feedbacks recebidos
   - Sistema anônimo opcional

7. **📊 Resultados**
   - Resumo final do processamento
   - Métricas de tempo e performance
   - Status da criação de views analíticas

## 🏗️ Arquitetura

```
┌─────────────────────────────────────┐
│        Camada de Visualização       │
│            (Streamlit)              │
│  ┌─────────────────────────────────┐│
│  │    StreamlitCTEInterface        ││
│  │                                 ││
│  │  • setup_page()                 ││
│  │  • mostrar_status_configuracao()││
│  │  • selecionar_diretorio()       ││
│  │  • configurar_parametros()      ││
│  │  • executar_processamento()     ││
│  └─────────────────────────────────┘│
└─────────────────┬───────────────────┘
                  │ integra com
┌─────────────────▼───────────────────┐
│        Camada de Aplicação          │
│            (main.py)                │
│  ┌─────────────────────────────────┐│
│  │     CTEMainApplication          ││
│  │                                 ││
│  │  • inicializar_sistema()        ││
│  │  • processar_arquivos()         ││
│  │  • criar_views_analiticas()     ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## 🚀 Como Executar

### ⚠️ IMPORTANTE: Comando Correto

**NÃO USE:** `python3 app.py` (isso causará erro!)

**USE:** Os comandos abaixo que iniciam o servidor Streamlit:

### Opção 1: Script Automático (Recomendado) ✅
```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit
./run.sh
```

### Opção 2: Comando Streamlit Direto ✅
```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit
streamlit run app.py
```

### Opção 3: Via Módulo Python ✅
```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit
python3 -m streamlit run app.py
```

### Opção 4: Comando Único (sem mudar diretório) ✅
```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit && streamlit run app.py
```

> **Nota:** O Streamlit abrirá automaticamente no navegador em `http://localhost:8501`

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL configurado
- Arquivo `.env` com configurações do banco
- Arquivos XML de CT-e para processamento

## 🔧 Configuração

A interface utiliza as mesmas configurações da Camada de Aplicação:
- Banco de dados PostgreSQL
- Credenciais definidas em `Config/database_config.py`
- Schemas: `cte`, `core`, `ibge`

## 📊 Fluxo de Uso

1. **Abrir Interface**: Execute `./run.sh` ou comando manual
2. **Verificar Configuração**: Sistema valida automaticamente
3. **Selecionar Diretório**: Digite o caminho dos arquivos XML
4. **Configurar Parâmetros**: Definir custo por quilômetro
5. **Processar**: Clique em "Iniciar Processamento"
6. **Acompanhar**: Visualize logs e progresso em tempo real
7. **Verificar Resultados**: Consulte resumo final e métricas

## 🎨 Interface

- **Layout Responsivo**: Adaptável a diferentes tamanhos de tela
- **Feedback Visual**: Barras de progresso e status em tempo real
- **Logs Integrados**: Saída completa do processamento
- **Validação Automática**: Verificação de caminhos e configurações
- **Design Intuitivo**: Interface clara e fácil de usar

## 🔄 Integração

A interface Streamlit atua como uma **camada fina** sobre a Camada de Aplicação:
- **Não duplica lógica**: Reutiliza `CTEMainApplication`
- **Mantém separação**: Interface independente da lógica de negócio
- **Feedback visual**: Adiciona apenas elementos de UI e UX

## 📝 Logs

Durante o processamento, a interface captura e exibe:
- Logs de inicialização do sistema
- Progresso do processamento de arquivos
- Criação de views analíticas
- Erros e exceções detalhados

## 🎯 Próximos Passos

Esta é a **primeira versão** da camada de visualização, focada na integração com a Camada de Aplicação. Futuras versões podem incluir:
- Dashboard de análise de dados ✅ **Implementado**
- Visualizações gráficas ✅ **Implementado**
- Relatórios interativos ✅ **Implementado**
- Sistema de Feedback ✅ **Implementado**
- Monitoramento em tempo real
- Exportação de relatórios (Excel, PDF)
- Filtros avançados por período

## 💬 Sistema de Feedback

O sistema agora inclui uma página dedicada ao feedback do usuário! Acesse através do menu principal:

**Funcionalidades:**
- ✨ Formulário intuitivo para sugestões
- 🏷️ Categorização de feedback (Bug, Nova Funcionalidade, Melhoria, etc.)
- 🔒 Opção de anonimato para o usuário
- 💾 Salvamento automático em arquivos .txt com timestamp
- 📊 Estatísticas de feedbacks recebidos
- 📁 Arquivos organizados em `Streamlit/feedback/`

**Como funciona:**
1. Acesse a página "💬 Feedback" no menu
2. Digite seu nome (opcional) e selecione a categoria
3. Escreva sua sugestão ou comentário (mínimo 10 caracteres)
4. Clique em "📨 Enviar Feedback"
5. Pronto! Seu feedback é salvo em `feedback_[timestamp].txt`

**Para desenvolvedores:**
- Feedbacks são salvos em `Streamlit/feedback/`
- Cada arquivo contém: data/hora, nome, categoria e texto completo
- Veja `Streamlit/feedback/README.md` para detalhes de análise e organização