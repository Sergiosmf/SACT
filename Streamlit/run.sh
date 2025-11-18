#!/bin/bash
# -*- coding: utf-8 -*-
"""
Script de execução da interface Streamlit
Sistema CT-e - Camada de Visualização
"""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚛 Sistema CT-e - Interface Streamlit"
echo "===================================="

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado!${NC}"
    exit 1
fi

# Verificar se streamlit está instalado
if ! python3 -c "import streamlit" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit não instalado. Instalando...${NC}"
    pip3 install streamlit
fi

# Mudar para diretório do script
cd "$(dirname "$0")"

echo -e "${GREEN}✅ Iniciando interface Streamlit...${NC}"
echo "🌐 A aplicação será aberta no navegador automaticamente"
echo "🛑 Para parar: Ctrl+C"
echo ""

# Executar Streamlit
python3 -m streamlit run app.py