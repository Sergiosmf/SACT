# 💬 Sistema de Feedback do Usuário

## 📋 Descrição

Este diretório armazena os feedbacks enviados pelos usuários do sistema CT-e através da interface Streamlit.

## 📁 Estrutura dos Arquivos

Cada feedback é salvo em um arquivo `.txt` individual com o seguinte formato de nome:

```
feedback_YYYYMMDD_HHMMSS.txt
```

**Exemplo:**
- `feedback_20251111_143025.txt` - Feedback enviado em 11/11/2025 às 14:30:25

## 📄 Formato do Conteúdo

Cada arquivo contém as seguintes informações:

```
================================================================================
FEEDBACK DO USUÁRIO - Sistema CT-e
================================================================================

Data/Hora: DD/MM/YYYY HH:MM:SS
Nome: [Nome do usuário ou "Anônimo"]
Categoria: [Categoria selecionada]

================================================================================
SUGESTÃO/COMENTÁRIO:
================================================================================

[Texto completo do feedback]

================================================================================
Fim do feedback
================================================================================
```

## 🏷️ Categorias Disponíveis

- **Geral** - Comentários gerais sobre o sistema
- **Nova Funcionalidade** - Sugestões de novas features
- **Bug/Problema** - Reportes de problemas ou erros
- **Melhoria de Interface** - Sugestões de melhorias na UI/UX
- **Performance** - Questões relacionadas a performance
- **Documentação** - Sugestões sobre documentação
- **Outro** - Outros tipos de feedback

## 🔍 Como Acessar os Feedbacks

### Via Terminal/Finder (macOS)

```bash
# Navegar até o diretório
cd /Users/sergiomendes/Documents/SACT/Streamlit/feedback

# Listar todos os feedbacks
ls -lt feedback_*.txt

# Ler um feedback específico
cat feedback_20251111_143025.txt

# Buscar feedbacks por categoria
grep -l "Categoria: Nova Funcionalidade" *.txt
```

### Via Python

```python
from pathlib import Path

feedback_dir = Path("Streamlit/feedback")

# Listar todos os feedbacks
feedbacks = sorted(feedback_dir.glob("feedback_*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)

# Ler um feedback
with open(feedbacks[0], 'r', encoding='utf-8') as f:
    conteudo = f.read()
    print(conteudo)
```

## 📊 Estatísticas

As estatísticas de feedback podem ser visualizadas diretamente na interface Streamlit, na página "💬 Feedback".

## 🔒 Privacidade

- Os feedbacks são armazenados localmente no servidor
- Apenas a equipe de desenvolvimento tem acesso aos arquivos
- Usuários podem optar por permanecer anônimos
- O conteúdo completo dos feedbacks não é exibido publicamente na interface

## 🛠️ Manutenção

### Backup dos Feedbacks

```bash
# Criar backup comprimido
cd /Users/sergiomendes/Documents/SACT/Streamlit
tar -czf feedback_backup_$(date +%Y%m%d).tar.gz feedback/*.txt
```

### Organizar por Categoria

```bash
# Criar diretórios por categoria
mkdir -p feedback/categorias/{geral,nova_funcionalidade,bug,melhoria,performance,documentacao,outro}

# Mover arquivos para categorias (exemplo)
grep -l "Categoria: Bug/Problema" feedback/*.txt | xargs -I {} mv {} feedback/categorias/bug/
```

### Análise de Feedbacks

```python
from pathlib import Path
import re
from collections import Counter

feedback_dir = Path("Streamlit/feedback")
feedbacks = list(feedback_dir.glob("feedback_*.txt"))

# Contar por categoria
categorias = []
for fb in feedbacks:
    with open(fb, 'r') as f:
        conteudo = f.read()
        match = re.search(r'Categoria: (.+)', conteudo)
        if match:
            categorias.append(match.group(1))

print("Distribuição por categoria:")
for cat, count in Counter(categorias).most_common():
    print(f"  {cat}: {count}")
```

## 📝 Exemplo de Uso

1. Usuário acessa a página "💬 Feedback" no Streamlit
2. Preenche nome (opcional), categoria e texto do feedback
3. Clica em "📨 Enviar Feedback"
4. Sistema salva o feedback em `feedback_[timestamp].txt`
5. Equipe de desenvolvimento pode acessar e analisar os feedbacks

## 🔄 Versionamento

- **v1.0** (11/11/2025) - Sistema inicial de feedback implementado
  - Formulário com nome, categoria e texto
  - Salvamento em arquivos .txt individuais
  - Estatísticas básicas na interface
  - Visualização de últimos feedbacks (metadados apenas)

## 📞 Contato

Para questões sobre o sistema de feedback, entre em contato com a equipe de desenvolvimento.
