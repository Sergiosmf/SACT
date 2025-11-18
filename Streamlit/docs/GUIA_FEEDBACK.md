# 💬 Guia Rápido - Sistema de Feedback

## 🎯 Para Usuários

### Como Enviar Feedback

1. **Acesse a aplicação Streamlit:**
   ```bash
   cd /Users/sergiomendes/Documents/SACT/Streamlit
   ./run.sh
   ```

2. **No menu principal, selecione:**
   ```
   💬 Feedback
   ```

3. **Preencha o formulário:**
   - **Nome** (opcional): Digite seu nome ou deixe em branco para ser anônimo
   - **Categoria**: Selecione o tipo de feedback:
     - 📝 Geral
     - ✨ Nova Funcionalidade
     - 🐛 Bug/Problema
     - 🎨 Melhoria de Interface
     - ⚡ Performance
     - 📚 Documentação
     - 🔧 Outro

4. **Escreva sua mensagem:**
   - Mínimo de 10 caracteres
   - Seja claro e específico
   - Inclua exemplos se possível

5. **Envie:**
   - Clique em "📨 Enviar Feedback"
   - Aguarde a confirmação de sucesso
   - Veja as estatísticas atualizadas

### 📝 Exemplos de Bons Feedbacks

#### ✨ Nova Funcionalidade
```
Gostaria de sugerir a adição de um filtro de data nas 
visualizações de rotas. Isso facilitaria muito a análise 
de períodos específicos, como comparar dados de meses 
diferentes.
```

#### 🐛 Bug/Problema
```
Ao tentar processar arquivos com mais de 500 CTes, o 
sistema apresenta um erro de timeout. O erro ocorre na 
etapa de cálculo de quilometragem. 

Arquivo de exemplo: cte_outubro_2025.xml
```

#### 🎨 Melhoria de Interface
```
A página de visualização de dados está ótima, mas seria 
interessante ter a opção de exportar os gráficos em 
formato PNG ou PDF para incluir em apresentações.
```

### ❌ Evite

- Feedbacks muito curtos: "legal" ou "tem bug"
- Sem contexto: "Não funciona"
- Informações sensíveis: senhas, dados pessoais
- CAPS LOCK ou linguagem ofensiva

### ✅ Boas Práticas

- ✨ Seja específico sobre o problema ou sugestão
- 📝 Inclua passos para reproduzir bugs
- 💡 Explique o benefício da sua sugestão
- 🎯 Foque em um tema por feedback
- 📊 Inclua dados ou exemplos quando relevante

---

## 🛠️ Para Desenvolvedores

### Localização dos Feedbacks

```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit/feedback
```

### Listar Todos os Feedbacks

```bash
ls -lt feedback_*.txt
```

### Ler um Feedback Específico

```bash
cat feedback_20251111_143025.txt
```

### Buscar por Categoria

```bash
# Buscar feedbacks sobre bugs
grep -l "Categoria: Bug/Problema" *.txt

# Buscar sugestões de features
grep -l "Categoria: Nova Funcionalidade" *.txt
```

### Buscar por Palavra-chave

```bash
# Buscar feedbacks que mencionam "exportar"
grep -i "exportar" feedback_*.txt

# Buscar feedbacks sobre "visualização"
grep -i "visualização" feedback_*.txt
```

### Análise Rápida com Python

```python
from pathlib import Path
import re
from collections import Counter

feedback_dir = Path("feedback")

# Contar por categoria
categorias = []
for fb in feedback_dir.glob("feedback_*.txt"):
    with open(fb, 'r') as f:
        if match := re.search(r'Categoria: (.+)', f.read()):
            categorias.append(match.group(1))

print("Distribuição por categoria:")
for cat, count in Counter(categorias).most_common():
    print(f"  {cat}: {count}")
```

### Backup Regular

```bash
# Criar backup diário
cd /Users/sergiomendes/Documents/SACT/Streamlit
tar -czf feedback_backup_$(date +%Y%m%d).tar.gz feedback/*.txt

# Mover para pasta de backups
mkdir -p backups
mv feedback_backup_*.tar.gz backups/
```

### Organizar por Categoria

```bash
# Criar estrutura de diretórios
cd feedback
mkdir -p categorias/{geral,feature,bug,ui,performance,docs,outro}

# Copiar (não mover) para categorias
grep -l "Categoria: Bug/Problema" feedback_*.txt | \
  xargs -I {} cp {} categorias/bug/

grep -l "Categoria: Nova Funcionalidade" feedback_*.txt | \
  xargs -I {} cp {} categorias/feature/

# ... repetir para outras categorias
```

### Gerar Relatório Mensal

```python
from pathlib import Path
from datetime import datetime
import re

feedback_dir = Path("feedback")
mes_atual = datetime.now().strftime("%Y%m")

feedbacks_mes = []
for fb in feedback_dir.glob(f"feedback_{mes_atual}*.txt"):
    with open(fb, 'r', encoding='utf-8') as f:
        conteudo = f.read()
        
        # Extrair informações
        nome = re.search(r'Nome: (.+)', conteudo).group(1)
        categoria = re.search(r'Categoria: (.+)', conteudo).group(1)
        data = re.search(r'Data/Hora: (.+)', conteudo).group(1)
        
        feedbacks_mes.append({
            'arquivo': fb.name,
            'nome': nome,
            'categoria': categoria,
            'data': data
        })

print(f"📊 Relatório de Feedbacks - {mes_atual}")
print(f"Total: {len(feedbacks_mes)}")
print(f"\nDetalhes:")
for fb in feedbacks_mes:
    print(f"  - [{fb['categoria']}] {fb['nome']} em {fb['data']}")
```

### Estatísticas Rápidas

```bash
# Total de feedbacks
ls feedback_*.txt 2>/dev/null | wc -l

# Feedbacks hoje
ls feedback_$(date +%Y%m%d)_*.txt 2>/dev/null | wc -l

# Feedbacks este mês
ls feedback_$(date +%Y%m)*.txt 2>/dev/null | wc -l
```

### Integração com Git

```bash
# Não versionar feedbacks de usuários (já configurado no .gitignore)
cd /Users/sergiomendes/Documents/SACT
git status Streamlit/feedback/

# Deve mostrar apenas:
# - README.md
# - .gitignore
# - feedback_exemplo.txt
```

---

## 🔍 Troubleshooting

### Problema: Feedback não está sendo salvo

**Solução:**
1. Verifique se o diretório `feedback/` existe
2. Verifique permissões de escrita:
   ```bash
   ls -la Streamlit/feedback/
   chmod 755 Streamlit/feedback/
   ```

### Problema: Erro ao importar componente

**Solução:**
1. Verifique se o arquivo existe:
   ```bash
   ls -la Streamlit/components/feedback.py
   ```
2. Verifique o Python path no `app.py`

### Problema: Não consigo ver os feedbacks

**Solução:**
```bash
cd /Users/sergiomendes/Documents/SACT/Streamlit/feedback
ls -la feedback_*.txt
```

Se não houver arquivos, nenhum feedback foi enviado ainda.

---

## 📞 Suporte

- **Documentação completa:** `feedback/README.md`
- **Testes:** Execute `python3 test_feedback.py`
- **Exemplos:** Veja `feedback_exemplo.txt`

---

**💡 Dica:** Use o feedback! É a melhor maneira de melhorar o sistema! 🚀
