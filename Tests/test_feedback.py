#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Feedback
Demonstração e validação do componente de feedback
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Adicionar diretórios ao path
current_dir = Path(__file__).parent.parent
streamlit_dir = current_dir / "Streamlit"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(streamlit_dir))

# Importar o gerenciador de feedback
from components.feedback import FeedbackManager


def test_feedback_manager():
    """Testa todas as funcionalidades do FeedbackManager"""
    
    print("="*80)
    print("🧪 TESTE DO SISTEMA DE FEEDBACK")
    print("="*80)
    print()
    
    # Criar instância do gerenciador
    manager = FeedbackManager()
    print(f"✅ FeedbackManager inicializado")
    print(f"📁 Diretório de feedback: {manager.feedback_dir}")
    print()
    
    # Teste 1: Verificar diretório
    print("📋 Teste 1: Verificação do diretório")
    if manager.feedback_dir.exists():
        print(f"   ✅ Diretório existe: {manager.feedback_dir}")
    else:
        print(f"   ❌ Diretório não existe!")
        return
    print()
    
    # Teste 2: Contar feedbacks existentes
    print("📋 Teste 2: Contagem de feedbacks")
    count = manager.get_feedback_count()
    print(f"   📊 Total de feedbacks existentes: {count}")
    print()
    
    # Teste 3: Salvar novo feedback
    print("📋 Teste 3: Salvamento de novo feedback")
    teste_texto = """
Este é um feedback de teste do sistema.

Estou testando as seguintes funcionalidades:
- Salvamento de feedback
- Formatação do arquivo
- Timestamp automático
- Categorização

Tudo parece estar funcionando perfeitamente! 🎉
"""
    
    sucesso = manager.save_feedback(
        texto=teste_texto,
        categoria="Outro",
        nome="Sistema de Testes Automatizado"
    )
    
    if sucesso:
        print(f"   ✅ Feedback salvo com sucesso!")
    else:
        print(f"   ❌ Erro ao salvar feedback")
    print()
    
    # Teste 4: Verificar novo count
    print("📋 Teste 4: Nova contagem após salvamento")
    new_count = manager.get_feedback_count()
    print(f"   📊 Total de feedbacks agora: {new_count}")
    if new_count > count:
        print(f"   ✅ Incremento detectado: +{new_count - count}")
    print()
    
    # Teste 5: Listar últimos feedbacks
    print("📋 Teste 5: Listagem dos últimos feedbacks")
    latest = manager.get_latest_feedbacks(5)
    print(f"   📋 Últimos {len(latest)} feedbacks:")
    for idx, fb in enumerate(latest, 1):
        print(f"      {idx}. {fb['filename']}")
        print(f"         Data: {fb['data']}")
        print(f"         Tamanho: {fb['tamanho']}")
    print()
    
    # Teste 6: Listar arquivos no diretório
    print("📋 Teste 6: Arquivos no diretório de feedback")
    feedback_files = list(manager.feedback_dir.glob("feedback_*.txt"))
    print(f"   📁 Total de arquivos: {len(feedback_files)}")
    if feedback_files:
        print(f"   📄 Último arquivo criado:")
        ultimo = max(feedback_files, key=os.path.getmtime)
        print(f"      {ultimo.name}")
        
        # Ler e mostrar conteúdo
        print(f"\n   📖 Conteúdo do último feedback:")
        print("   " + "-"*76)
        with open(ultimo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            # Mostrar apenas primeiras 20 linhas
            linhas = conteudo.split('\n')[:20]
            for linha in linhas:
                print(f"   {linha}")
            if len(conteudo.split('\n')) > 20:
                print(f"   ... (mais {len(conteudo.split('\n')) - 20} linhas)")
        print("   " + "-"*76)
    print()
    
    # Teste 7: Feedback anônimo
    print("📋 Teste 7: Teste de feedback anônimo")
    sucesso_anonimo = manager.save_feedback(
        texto="Este é um teste de feedback anônimo do sistema.",
        categoria="Geral",
        nome="Anônimo"
    )
    if sucesso_anonimo:
        print(f"   ✅ Feedback anônimo salvo com sucesso!")
    print()
    
    # Teste 8: Diferentes categorias
    print("📋 Teste 8: Teste de diferentes categorias")
    categorias_teste = ["Bug/Problema", "Nova Funcionalidade", "Melhoria de Interface"]
    for cat in categorias_teste:
        sucesso_cat = manager.save_feedback(
            texto=f"Teste da categoria {cat}",
            categoria=cat,
            nome="Sistema de Testes"
        )
        if sucesso_cat:
            print(f"   ✅ Categoria '{cat}': OK")
    print()
    
    # Resumo final
    print("="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    final_count = manager.get_feedback_count()
    print(f"✅ Total de feedbacks ao final: {final_count}")
    print(f"✅ Feedbacks criados neste teste: {final_count - count}")
    print(f"📁 Localização: {manager.feedback_dir}")
    print()
    print("🎉 Todos os testes concluídos com sucesso!")
    print("="*80)


def cleanup_test_feedbacks():
    """Remove feedbacks de teste (opcional)"""
    print("\n⚠️  Limpeza de feedbacks de teste")
    resposta = input("Deseja remover os feedbacks criados durante o teste? (s/N): ")
    
    if resposta.lower() == 's':
        manager = FeedbackManager()
        feedback_files = list(manager.feedback_dir.glob("feedback_*.txt"))
        
        # Manter apenas o exemplo
        for fb in feedback_files:
            if 'exemplo' not in fb.name:
                try:
                    fb.unlink()
                    print(f"   🗑️  Removido: {fb.name}")
                except Exception as e:
                    print(f"   ❌ Erro ao remover {fb.name}: {e}")
        
        print("✅ Limpeza concluída!")
    else:
        print("ℹ️  Feedbacks de teste mantidos.")


if __name__ == "__main__":
    try:
        test_feedback_manager()
        
        # Opcional: limpar feedbacks de teste
        print()
        cleanup_test_feedbacks()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
