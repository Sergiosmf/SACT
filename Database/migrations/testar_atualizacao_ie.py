#!/usr/bin/env python3
"""
Teste de Atualização de IE
===========================
Testa a lógica de atualização automática de IE quando uma empresa
já existe no banco e aparece em um novo CT-e com IE preenchida.

Autor: Sistema SACT
Data: 2025-01-13
"""

import sys
from pathlib import Path

# Adicionar paths
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

from Database.services.etl_service import ETLService
from Config.database_config import DATABASE_CONFIG

def testar_atualizacao_ie():
    """
    Testa o processamento de um CT-e específico para verificar
    se a IE está sendo extraída e atualizada corretamente.
    """
    print("=" * 80)
    print("🧪 TESTE DE ATUALIZAÇÃO DE IE")
    print("=" * 80)
    
    # Arquivo CT-e de teste
    cte_path = "/Users/sergiomendes/Documents/CT-e/mes_10_2025/CT-e/Autorizados/CTe21251035263415000132570010000019471851037310.xml"
    
    print(f"\n📄 Arquivo: {Path(cte_path).name}")
    
    # Empresas esperadas neste CT-e
    empresas_esperadas = {
        "09614350000112": {
            "nome": "AGROPECUARIA LAVORO LTDA",
            "ie": "194659640"
        },
        "05699871000169": {
            "nome": "FRIGORIFICO DE TIMON SA",
            "ie": "120754908"
        }
    }
    
    print("\n📋 Empresas esperadas no CT-e:")
    for cnpj, dados in empresas_esperadas.items():
        print(f"   • {dados['nome']}")
        print(f"     CNPJ: {cnpj}")
        print(f"     IE: {dados['ie']}")
    
    # Verificar estado atual no banco
    print("\n" + "=" * 80)
    print("📊 ESTADO ATUAL NO BANCO (ANTES)")
    print("=" * 80)
    
    import psycopg2
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        for cnpj in empresas_esperadas.keys():
            cursor.execute("""
                SELECT 
                    id_pessoa,
                    nome,
                    cpf_cnpj,
                    inscricao_estadual,
                    telefone,
                    email,
                    created_at,
                    updated_at
                FROM core.pessoa
                WHERE cpf_cnpj = %s
            """, (cnpj,))
            
            pessoa = cursor.fetchone()
            
            if pessoa:
                print(f"\n✅ Empresa encontrada:")
                print(f"   ID: {pessoa[0]}")
                print(f"   Nome: {pessoa[1]}")
                print(f"   CNPJ: {pessoa[2]}")
                print(f"   IE: {pessoa[3] or '❌ NULL'}")
                print(f"   Telefone: {pessoa[4] or '(vazio)'}")
                print(f"   Email: {pessoa[5] or '(vazio)'}")
                print(f"   Criado: {pessoa[6]}")
                print(f"   Atualizado: {pessoa[7]}")
            else:
                print(f"\n❌ Empresa NÃO encontrada (CNPJ: {cnpj})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return
    
    # Processar CT-e
    print("\n" + "=" * 80)
    print("⚙️  PROCESSANDO CT-E")
    print("=" * 80)
    
    from Database.managers.database_manager import CTEDatabaseManager
    from Database.managers.stats_manager import StatsManager
    
    db_manager = CTEDatabaseManager(DATABASE_CONFIG)
    stats_manager = StatsManager()
    etl = ETLService(db_manager, stats_manager)
    
    # Processar como lote com um único arquivo
    sucesso = etl.processar_lote_arquivos([Path(cte_path)], custo_por_km=5.0)
    
    if sucesso:
        print("\n✅ CT-e processado com sucesso!")
    else:
        print("\n❌ Erro ao processar CT-e")
        return
    
    # Verificar estado após processamento
    print("\n" + "=" * 80)
    print("📊 ESTADO APÓS PROCESSAMENTO")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        mudancas_detectadas = False
        
        for cnpj, dados_esperados in empresas_esperadas.items():
            cursor.execute("""
                SELECT 
                    id_pessoa,
                    nome,
                    cpf_cnpj,
                    inscricao_estadual,
                    telefone,
                    email,
                    created_at,
                    updated_at
                FROM core.pessoa
                WHERE cpf_cnpj = %s
            """, (cnpj,))
            
            pessoa = cursor.fetchone()
            
            if pessoa:
                print(f"\n✅ Empresa: {dados_esperados['nome']}")
                print(f"   ID: {pessoa[0]}")
                print(f"   CNPJ: {pessoa[2]}")
                
                # Verificar IE
                ie_atual = pessoa[3]
                ie_esperada = dados_esperados['ie']
                
                if ie_atual == ie_esperada:
                    print(f"   ✅ IE: {ie_atual} (CORRETO!)")
                    mudancas_detectadas = True
                elif ie_atual:
                    print(f"   ⚠️  IE: {ie_atual} (esperado: {ie_esperada})")
                else:
                    print(f"   ❌ IE: NULL (esperado: {ie_esperada})")
                
                print(f"   Telefone: {pessoa[4] or '(vazio)'}")
                print(f"   Email: {pessoa[5] or '(vazio)'}")
                print(f"   Criado: {pessoa[6]}")
                print(f"   Atualizado: {pessoa[7]}")
            else:
                print(f"\n❌ Empresa NÃO encontrada (CNPJ: {cnpj})")
        
        cursor.close()
        conn.close()
        
        # Resumo
        print("\n" + "=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        
        if mudancas_detectadas:
            print("\n✅ Teste BEM-SUCEDIDO!")
            print("   As IEs foram atualizadas corretamente.")
        else:
            print("\n⚠️  Teste INCOMPLETO")
            print("   As IEs não foram atualizadas.")
            print("   Verifique os logs acima para detalhes.")
        
    except Exception as e:
        print(f"❌ Erro ao verificar resultado: {e}")

if __name__ == "__main__":
    testar_atualizacao_ie()
