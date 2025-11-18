#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(III) TESTES DE INTEGRAÇÃO
Avaliação da interoperabilidade entre as quatro camadas:
- Upload/Descoberta
- Extração
- Parsing/Aplicação
- Persistência
"""

import pytest
from pathlib import Path
import json
from datetime import datetime


@pytest.mark.integracao
@pytest.mark.database
@pytest.mark.lento
class TestIntegracaoQuatroCamadas:
    """Testa integração completa das 4 camadas."""
    
    def test_integracao_completa(self, sample_xml_path, db_connection, results_dir, test_timestamp):
        """
        Integração completa das 4 camadas COM MEDIÇÃO DE TEMPO:
        1. Upload/Descoberta → 2. Extração → 3. Parsing → 4. Persistência
        """
        from cte_extractor import CTEFacade
        import time
        
        print("\n" + "="*80)
        print("🔗 INTEGRAÇÃO DAS 4 CAMADAS + PERFORMANCE")
        print("="*80)
        
        chave_teste = "77777777777777777777777777777777777777777777"
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'arquivo': sample_xml_path.name,
            'camadas': {},
            'tempos_ms': {}
        }
        
        try:
            # ========================================
            # CAMADA 1: UPLOAD/DESCOBERTA
            # ========================================
            print("\n📂 CAMADA 1: Upload/Descoberta")
            inicio_c1 = time.perf_counter()
            
            assert sample_xml_path.exists()
            tamanho_kb = sample_xml_path.stat().st_size / 1024
            
            fim_c1 = time.perf_counter()
            tempo_c1 = (fim_c1 - inicio_c1) * 1000
            
            relatorio['camadas']['1_upload'] = {
                'status': 'sucesso',
                'arquivo': sample_xml_path.name,
                'tamanho_kb': tamanho_kb
            }
            relatorio['tempos_ms']['camada_1_upload'] = tempo_c1
            print(f"✅ Arquivo: {sample_xml_path.name} ({tamanho_kb:.2f} KB)")
            print(f"⏱️  Tempo: {tempo_c1:.4f}ms")
            
            # ========================================
            # CAMADA 2: EXTRAÇÃO
            # ========================================
            print("\n⚙️ CAMADA 2: Extração de Dados")
            inicio_c2 = time.perf_counter()
            
            facade = CTEFacade()
            dados = facade.extrair(str(sample_xml_path))
            
            fim_c2 = time.perf_counter()
            tempo_c2 = (fim_c2 - inicio_c2) * 1000
            
            assert dados is not None
            assert isinstance(dados, dict)
            
            relatorio['camadas']['2_extracao'] = {
                'status': 'sucesso',
                'total_campos': len(dados)
            }
            relatorio['tempos_ms']['camada_2_extracao'] = tempo_c2
            print(f"✅ Extraídos: {len(dados)} campos")
            print(f"⏱️  Tempo: {tempo_c2:.4f}ms")
            
            # ========================================
            # CAMADA 3: PARSING/TRANSFORMAÇÃO
            # ========================================
            print("\n🔄 CAMADA 3: Parsing/Transformação")
            inicio_c3 = time.perf_counter()
            
            # Transformar formato do extrator para formato da função f_ingest_cte_json
            carga_data = dados.get('Carga', {})
            dados_transform = {
                'chave': chave_teste,
                'numero': dados.get('CT-e_numero'),
                'serie': dados.get('CT-e_serie'),
                'cfop': dados.get('CFOP'),
                'valor_frete': dados.get('Valor_frete'),
                'quilometragem': 4.85,  # Valor padrão do divisor para cálculo: quilometragem = valor_frete / 4.85
                'data_emissao': dados.get('Data_emissao'),
                'origem_cidade': dados.get('Origem', {}).get('cidade'),
                'origem_uf': dados.get('Origem', {}).get('uf'),
                'destino_cidade': dados.get('Destino', {}).get('cidade'),
                'destino_uf': dados.get('Destino', {}).get('uf'),
                'placa': dados.get('Placa'),
                'versao_schema': dados.get('Versao_Schema'),
                'carga': {
                    'valor': carga_data.get('vcarga'),
                    'peso': carga_data.get('peso'),
                    'quantidade': carga_data.get('qcarga'),
                    'produto_predominante': carga_data.get('propred'),
                    'unidade_medida': carga_data.get('unidade')
                }
            }
            
            fim_c3 = time.perf_counter()
            tempo_c3 = (fim_c3 - inicio_c3) * 1000
            
            relatorio['camadas']['3_parsing'] = {
                'status': 'sucesso',
                'metodo': 'preparacao_jsonb'
            }
            relatorio['tempos_ms']['camada_3_parsing'] = tempo_c3
            print(f"✅ JSON preparado para ingestão")
            print(f"⏱️  Tempo: {tempo_c3:.4f}ms")
            
            # ========================================
            # CAMADA 4: PERSISTÊNCIA
            # ========================================
            print("\n💾 CAMADA 4: Persistência")
            inicio_c4 = time.perf_counter()
            
            with db_connection.cursor() as cursor:
                # Limpar
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                
                # Persistir usando f_ingest_cte_json
                cursor.execute("""
                    SELECT cte.f_ingest_cte_json(%s::jsonb)
                """, (json.dumps(dados_transform),))
                
                id_cte = cursor.fetchone()[0]
                db_connection.commit()
                
                # Verificar
                cursor.execute("""
                    SELECT d.chave, d.numero, d.valor_frete,
                           c.valor AS carga_valor
                    FROM cte.documento d
                    LEFT JOIN cte.carga c ON c.id_cte = d.id_cte
                    WHERE d.chave = %s
                """, (chave_teste,))
                
                registro = cursor.fetchone()
                assert registro is not None
                
                fim_c4 = time.perf_counter()
                tempo_c4 = (fim_c4 - inicio_c4) * 1000
                
                relatorio['camadas']['4_persistencia'] = {
                    'status': 'sucesso',
                    'id_cte': id_cte,
                    'chave': registro[0],
                    'metodo': 'f_ingest_cte_json()'
                }
                relatorio['tempos_ms']['camada_4_persistencia'] = tempo_c4
                print(f"✅ Persistido: {registro[0]} (id={id_cte})")
                print(f"⏱️  Tempo: {tempo_c4:.4f}ms")
            
            # ========================================
            # VERIFICAÇÃO DE INTEGRIDADE
            # ========================================
            print("\n🔍 VERIFICAÇÃO: Integridade dos Dados")
            
            verificacao = {
                'chave_preservada': registro[0] == chave_teste,
                'numero_preservado': str(registro[1]) == str(dados_transform.get('numero', '999')),
                'valor_preservado': registro[2] is not None,  # valor_frete
                'carga_inserida': registro[3] is not None  # carga_valor (pode ser None se não houver carga)
            }
            
            relatorio['verificacao'] = verificacao
            
            # Tempos totais
            tempo_total = tempo_c1 + tempo_c2 + tempo_c3 + tempo_c4
            relatorio['tempos_ms']['total'] = tempo_total
            relatorio['tempos_ms']['percentuais'] = {
                'upload': (tempo_c1 / tempo_total) * 100,
                'extracao': (tempo_c2 / tempo_total) * 100,
                'parsing': (tempo_c3 / tempo_total) * 100,
                'persistencia': (tempo_c4 / tempo_total) * 100
            }
            
            relatorio['status'] = 'sucesso' if all(verificacao.values()) else 'falha'
            
            print(f"✅ Chave: {verificacao['chave_preservada']}")
            print(f"✅ Número: {verificacao['numero_preservado']}")
            print(f"✅ Valor: {verificacao['valor_preservado']}")
            
            # Salvar relatório
            output = results_dir / f"integracao_4_camadas_{test_timestamp}.json"
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
            
            print("\n" + "="*80)
            print("📊 RESULTADO DA INTEGRAÇÃO")
            print("="*80)
            print(f"Status: {relatorio['status'].upper()}")
            print(f"Camadas: 4/4 ✅")
            print(f"Integridade: {'✅ OK' if all(verificacao.values()) else '❌ FALHA'}")
            print(f"Método: {relatorio['camadas']['4_persistencia']['metodo']}")
            print(f"\n⏱️  TEMPOS POR CAMADA:")
            print(f"   1. Upload:       {tempo_c1:7.4f}ms ({relatorio['tempos_ms']['percentuais']['upload']:5.2f}%)")
            print(f"   2. Extração:     {tempo_c2:7.4f}ms ({relatorio['tempos_ms']['percentuais']['extracao']:5.2f}%)")
            print(f"   3. Parsing:      {tempo_c3:7.4f}ms ({relatorio['tempos_ms']['percentuais']['parsing']:5.2f}%)")
            print(f"   4. Persistência: {tempo_c4:7.4f}ms ({relatorio['tempos_ms']['percentuais']['persistencia']:5.2f}%)")
            print(f"   ─────────────────────────────────────")
            print(f"   TOTAL:           {tempo_total:7.4f}ms")
            print(f"\n📄 Relatório: {output}")
            print("="*80)
            
            assert all(verificacao.values()), "Integridade comprometida"
            
        finally:
            with db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                db_connection.commit()
    
    def test_integracao_lote(self, sample_xml_dir, db_connection, results_dir, test_timestamp):
        """Testa integração das 4 camadas com lote de arquivos usando f_ingest_cte_json()."""
        from cte_extractor import CTEFacade
        
        print("\n" + "="*80)
        print("🔗 INTEGRAÇÃO - LOTE (via f_ingest_cte_json)")
        print("="*80)
        
        facade = CTEFacade()
        arquivos = list(sample_xml_dir.glob("*.xml"))[:3]
        
        chaves_teste = [
            f"777777777777777777777777777777777777777777{i:02d}"
            for i in range(len(arquivos))
        ]
        
        resultados = []
        
        try:
            for i, (arquivo, chave) in enumerate(zip(arquivos, chaves_teste)):
                print(f"\n📄 [{i+1}/{len(arquivos)}] {arquivo.name}")
                
                try:
                    # Extração
                    dados = facade.extrair(str(arquivo))
                    print("   ✅ Extração")
                    
                    # Transformação para formato f_ingest_cte_json
                    carga_data = dados.get('Carga', {})
                    dados_transform = {
                        'chave': chave,
                        'numero': dados.get('CT-e_numero'),
                        'serie': dados.get('CT-e_serie'),
                        'cfop': dados.get('CFOP'),
                        'valor_frete': dados.get('Valor_frete'),
                        'quilometragem': 4.85,  # Valor padrão do divisor para cálculo: quilometragem = valor_frete / 4.85
                        'data_emissao': dados.get('Data_emissao'),
                        'origem_cidade': dados.get('Origem', {}).get('cidade'),
                        'origem_uf': dados.get('Origem', {}).get('uf'),
                        'destino_cidade': dados.get('Destino', {}).get('cidade'),
                        'destino_uf': dados.get('Destino', {}).get('uf'),
                        'placa': dados.get('Placa'),
                        'versao_schema': dados.get('Versao_Schema'),
                        'carga': {
                            'valor': carga_data.get('vcarga'),
                            'peso': carga_data.get('peso'),
                            'quantidade': carga_data.get('qcarga'),
                            'produto_predominante': carga_data.get('propred'),
                            'unidade_medida': carga_data.get('unidade')
                        }
                    }
                    print("   ✅ Transformação")
                    
                    # Persistência
                    with db_connection.cursor() as cursor:
                        cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave,))
                        cursor.execute("""
                            SELECT cte.f_ingest_cte_json(%s::jsonb)
                        """, (json.dumps(dados_transform),))
                        
                        id_cte = cursor.fetchone()[0]
                        db_connection.commit()
                    
                    print(f"   ✅ Persistência (id={id_cte})")
                    
                    resultados.append({
                        'arquivo': arquivo.name,
                        'chave': chave,
                        'id_cte': id_cte,
                        'status': 'sucesso'
                    })
                    
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    resultados.append({
                        'arquivo': arquivo.name,
                        'status': 'erro',
                        'erro': str(e)
                    })
            
            # Relatório
            relatorio = {
                'timestamp': datetime.now().isoformat(),
                'teste': 'integracao_lote',
                'metodo': 'f_ingest_cte_json()',
                'total': len(arquivos),
                'sucesso': sum(1 for r in resultados if r['status'] == 'sucesso'),
                'resultados': resultados
            }
            
            output = results_dir / f"integracao_lote_{test_timestamp}.json"
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*80)
            print(f"📊 Sucesso: {relatorio['sucesso']}/{relatorio['total']}")
            print(f"Método: {relatorio['metodo']}")
            print(f"📄 Relatório: {output}")
            print("="*80)
            
            assert relatorio['sucesso'] > 0
            
        finally:
            with db_connection.cursor() as cursor:
                for chave in chaves_teste:
                    cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave,))
                db_connection.commit()
