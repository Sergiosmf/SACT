#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(II) TESTES FUNCIONAIS
Execução de fluxos completos de importação e processamento de lotes de XML
"""

import pytest
from pathlib import Path
import json
from datetime import datetime


@pytest.mark.funcional
@pytest.mark.xml
class TestProcessamentoLote:
    """Testes de processamento em lote."""
    
    def test_processar_arquivo_unico(self, sample_xml_path, results_dir, test_timestamp):
        """Processa um único arquivo XML."""
        from cte_extractor import CTEFacade
        
        facade = CTEFacade()
        resultado = facade.extrair(str(sample_xml_path))
        
        assert resultado is not None
        assert isinstance(resultado, dict)
        
        # Salvar resultado
        output = results_dir / f"processamento_unico_{test_timestamp}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Resultado salvo: {output}")
    
    def test_processar_multiplos_arquivos(self, sample_xml_dir, results_dir, test_timestamp):
        """Processa múltiplos arquivos XML."""
        from cte_extractor import CTEFacade
        
        facade = CTEFacade()
        arquivos = list(sample_xml_dir.glob("*.xml"))[:5]
        
        assert len(arquivos) > 0
        
        resultados = []
        for arquivo in arquivos:
            try:
                dados = facade.extrair(str(arquivo))
                resultados.append({
                    'arquivo': arquivo.name,
                    'sucesso': True,
                    'dados': dados
                })
            except Exception as e:
                resultados.append({
                    'arquivo': arquivo.name,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        # Relatório
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'total': len(arquivos),
            'sucesso': len([r for r in resultados if r['sucesso']]),
            'erro': len([r for r in resultados if not r['sucesso']]),
            'resultados': resultados
        }
        
        output = results_dir / f"processamento_lote_{test_timestamp}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Processados: {relatorio['sucesso']}/{relatorio['total']}")
        print(f"📄 Relatório: {output}")
        
        assert relatorio['sucesso'] > 0


@pytest.mark.funcional
@pytest.mark.lento
class TestFluxoCompleto:
    """Testes de fluxo completo."""
    
    def test_fluxo_descoberta_extracao(self, sample_xml_dir, results_dir, test_timestamp):
        """Testa fluxo: descoberta → extração → validação."""
        from cte_extractor import CTEFacade
        
        # 1. Descoberta
        arquivos = list(sample_xml_dir.glob("*.xml"))[:5]
        print(f"📂 Descobertos: {len(arquivos)} arquivos")
        
        # 2. Extração
        facade = CTEFacade()
        resultados = []
        
        for i, arquivo in enumerate(arquivos, 1):
            print(f"⚙️ [{i}/{len(arquivos)}] {arquivo.name}")
            try:
                dados = facade.extrair(str(arquivo))
                resultados.append({
                    'arquivo': arquivo.name,
                    'sucesso': True,
                    'campos': len(dados)
                })
            except Exception as e:
                resultados.append({
                    'arquivo': arquivo.name,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        # 3. Relatório
        relatorio = {
            'fluxo': 'descoberta_extracao',
            'timestamp': datetime.now().isoformat(),
            'arquivos_descobertos': len(arquivos),
            'arquivos_processados': len(resultados),
            'sucesso': sum(1 for r in resultados if r['sucesso']),
            'resultados': resultados
        }
        
        output = results_dir / f"fluxo_completo_{test_timestamp}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Resumo:")
        print(f"   Sucesso: {relatorio['sucesso']}/{relatorio['arquivos_processados']}")
        print(f"📄 Relatório: {output}")
        
        assert relatorio['sucesso'] > 0


@pytest.mark.funcional
@pytest.mark.database
class TestPipelineComPersistencia:
    """Testes de pipeline completo com banco."""
    
    def test_pipeline_extracao_persistencia(self, sample_xml_path, db_connection, results_dir, test_timestamp):
        """Testa: extração → transformação → persistência."""
        from cte_extractor import CTEFacade
        
        # 1. Extração
        facade = CTEFacade()
        dados = facade.extrair(str(sample_xml_path))
        print("✅ Dados extraídos")
        
        # 2. Preparar para persistência (transformar formato)
        chave_teste = "88888888888888888888888888888888888888888888"
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
        
        try:
            with db_connection.cursor() as cursor:
                # Limpar
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                
                # 3. Persistir usando f_ingest_cte_json
                cursor.execute("""
                    SELECT cte.f_ingest_cte_json(%s::jsonb)
                """, (json.dumps(dados_transform),))
                
                id_cte = cursor.fetchone()[0]
                db_connection.commit()
                print("✅ Dados persistidos")
                
                # 4. Verificar
                cursor.execute("SELECT chave FROM cte.documento WHERE chave = %s", (chave_teste,))
                resultado = cursor.fetchone()
                assert resultado is not None
                print("✅ Verificação OK")
                
                # Relatório
                relatorio = {
                    'timestamp': datetime.now().isoformat(),
                    'pipeline': 'extracao_persistencia',
                    'arquivo': sample_xml_path.name,
                    'etapas': {
                        'extracao': 'sucesso',
                        'transformacao': 'sucesso',
                        'persistencia': 'sucesso',
                        'verificacao': 'sucesso'
                    }
                }
                
                output = results_dir / f"pipeline_{test_timestamp}.json"
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(relatorio, f, indent=2, ensure_ascii=False)
                
                print(f"📄 Relatório: {output}")
                
        finally:
            with db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                db_connection.commit()
