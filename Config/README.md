# ⚙️ Config - Configurações do Sistema

Esta pasta contém todos os arquivos de configuração do SACT.

## 📁 **ARQUIVOS DE CONFIGURAÇÃO**

| Arquivo | Descrição |
|---------|-----------|
| **database_config.py** | Configurações de conexão PostgreSQL |
| **.env** | Variáveis de ambiente e credenciais |

## 🔧 **CONFIGURAÇÃO DO BANCO**

### **database_config.py**
Contém as configurações padrão de conexão:
```python
# Configurações utilizadas pelo sistema
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'sact',
    'user': 'sergiomendes',
    'password': '123456',
    'port': 5432
}
```

### **.env**
Variáveis de ambiente para diferentes configurações:
```bash
# Exemplo de configuração
DB_HOST=localhost
DB_NAME=sact
DB_USER=sergiomendes
DB_PASSWORD=123456
DB_PORT=5432
```

## 🚀 **COMO USAR**

### **1. Importar configurações**
```python
from Config.database_config import DATABASE_CONFIG

# Usar nas conexões
conn = psycopg2.connect(**DATABASE_CONFIG)
```

### **2. Modificar configurações**
Para alterar configurações de banco:
1. Edite `database_config.py` para mudanças permanentes
2. Ou modifique `.env` para variáveis de ambiente

## 🔒 **SEGURANÇA**

- ⚠️ **Nunca commitar credenciais** no git
- ✅ Usar variáveis de ambiente para produção
- ✅ Manter `.env` no `.gitignore`

## 📋 **CONFIGURAÇÕES SUPORTADAS**

### **PostgreSQL**
- Host/IP do servidor
- Nome do banco de dados
- Usuário e senha
- Porta de conexão
- Parâmetros SSL (se necessário)

### **Sistema**
- Logs de debug
- Timeouts de conexão
- Pool de conexões
- Encoding de caracteres

---
**💡 Mantenha sempre backups das configurações importantes**