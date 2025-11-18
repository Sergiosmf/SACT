#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar todos os testes organizados
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_pytest(categoria, nome, *args):
    """Executa pytest com os argumentos fornecidos."""
    print("\n" + "="*80)
    print(f"🧪 {nome.upper()}")
    print("="*80)
    
    cmd = [sys.executable, "-m", "pytest", categoria] + list(args)
    
    print(f"Comando: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n⚠️  {nome} finalizou com código {result.returncode}")
    
    return result.returncode


def main():
    """Executa todos os testes."""
    print("="*80)
    print("🎯 EXECUÇÃO COMPLETA DE TESTES")
    print("="*80)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    resultados = {}
    
    # (I) Testes Unitários
    resultados['unitarios'] = run_pytest(
        'unitarios/',
        'Testes Unitários',
        '-v',
        '--tb=short'
    )
    
    # (II) Testes Funcionais
    resultados['funcionais'] = run_pytest(
        'funcionais/',
        'Testes Funcionais',
        '-v',
        '--tb=short'
    )
    
    # (III) Testes de Integração
    resultados['integracao'] = run_pytest(
        'integracao/',
        'Testes de Integração',
        '-v',
        '--tb=short'
    )
    
    # Relatório Final
    print("\n" + "="*80)
    print("📊 RELATÓRIO FINAL")
    print("="*80)
    
    total_categorias = len(resultados)
    total_sucesso = sum(1 for r in resultados.values() if r == 0)
    
    for categoria, codigo in resultados.items():
        status = "✅ PASSOU" if codigo == 0 else f"❌ FALHOU ({codigo})"
        print(f"{categoria.upper():20s} : {status}")
    
    print("="*80)
    print(f"Total: {total_sucesso}/{total_categorias} categorias passaram")
    print(f"⏰ Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Código de saída
    sys.exit(0 if total_sucesso == total_categorias else 1)


if __name__ == '__main__':
    main()
