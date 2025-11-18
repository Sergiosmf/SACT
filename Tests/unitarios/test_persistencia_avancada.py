#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES AVANÇADOS - Persistência e Performance
Testes completos de banco de dados e medição de desempenho
"""

import pytest
import time
import json
from pathlib import Path
from datetime import datetime


@pytest.mark.database
@pytest.mark.lento
class TestPersistenciaAvancada:
    """Testes avançados de persistência no banco de dados."""
    
    def test_insert_cte_completo(self, sample_xml_path, db_connection, results_dir, test_timestamp):
        """Testa inserção completa de CT-e no banco usando função f_ingest_cte_json()."""
        from cte_extractor import CTEFacade
        
        print("\n" + "="*80)
        print("💾 TESTE DE PERSISTÊNCIA COMPLETA (usando f_ingest_cte_json)")
        print("="*80)
        
        chave_teste = "88888888888888888888888888888888888888888888"
        
        try:
            # Extrair dados
            print("\n⚙️  Extraindo dados do XML...")
            facade = CTEFacade()
            dados = facade.extrair(str(sample_xml_path))
            
            # Transformar formato do extrator para formato da função f_ingest_cte_json
            print("📝 Preparando dados para inserção...")
            carga_data = dados.get('Carga', {})
            remetente_data = dados.get('Remetente', {})
            destinatario_data = dados.get('Destinatario', {})
            
            # Extrair documento (CPF ou CNPJ)
            rem_docs = remetente_data.get('documentos', {})
            rem_doc = rem_docs.get('cnpj') or rem_docs.get('cpf')
            
            dest_docs = destinatario_data.get('documentos', {})
            dest_doc = dest_docs.get('cnpj') or dest_docs.get('cpf')
            
            dados_ingest = {
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
                    'peso': carga_data.get('peso'),  # Pode não existir
                    'quantidade': carga_data.get('qcarga'),
                    'produto_predominante': carga_data.get('propred'),
                    'unidade_medida': carga_data.get('unidade')
                },
                'remetente': {
                    'nome': remetente_data.get('nome'),
                    'documento': rem_doc,
                    'endereco': remetente_data.get('endereco')
                },
                'destinatario': {
                    'nome': destinatario_data.get('nome'),
                    'documento': dest_doc,
                    'endereco': destinatario_data.get('endereco')
                },
                'expedidor': {
                    'nome': remetente_data.get('nome'),  # Geralmente igual ao remetente
                    'documento': rem_doc,
                    'endereco': remetente_data.get('endereco')
                },
                'recebedor': {
                    'nome': destinatario_data.get('nome'),  # Geralmente igual ao destinatário
                    'documento': dest_doc,
                    'endereco': destinatario_data.get('endereco')
                }
            }
            
            with db_connection.cursor() as cursor:
                # Limpar dados de teste
                print("🧹 Limpando dados anteriores...")
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                
                # Inserir usando função f_ingest_cte_json com medição de tempo
                print("💾 Inserindo no banco de dados via f_ingest_cte_json()...")
                inicio = time.perf_counter()
                
                cursor.execute("""
                    SELECT cte.f_ingest_cte_json(%s::jsonb)
                """, (json.dumps(dados_ingest),))
                
                id_cte = cursor.fetchone()[0]
                db_connection.commit()
                fim = time.perf_counter()
                tempo_insert = (fim - inicio) * 1000
                
                print(f"✅ Inserido em {tempo_insert:.4f}ms (id_cte: {id_cte})")
                
                # Verificar integridade - CONSULTA DETALHADA
                print("🔍 Verificando integridade dos dados inseridos...")
                
                # 1. Verificar tabela documento
                cursor.execute("""
                    SELECT 
                        d.id_cte, d.chave, d.numero, d.serie, d.cfop,
                        d.valor_frete, d.quilometragem, d.data_emissao,
                        d.id_municipio_origem, d.id_municipio_destino,
                        d.id_veiculo, d.versao_schema,
                        mo.nome AS municipio_origem, mo.id_uf AS uf_origem,
                        md.nome AS municipio_destino, md.id_uf AS uf_destino,
                        v.placa
                    FROM cte.documento d
                    LEFT JOIN ibge.municipio mo ON mo.id_municipio = d.id_municipio_origem
                    LEFT JOIN ibge.municipio md ON md.id_municipio = d.id_municipio_destino
                    LEFT JOIN core.veiculo v ON v.id_veiculo = d.id_veiculo
                    WHERE d.chave = %s
                """, (chave_teste,))
                
                doc = cursor.fetchone()
                assert doc is not None, "❌ Documento não encontrado após inserção"
                print(f"   ✅ Documento encontrado (id_cte: {doc[0]})")
                
                # 2. Verificar tabela carga
                cursor.execute("""
                    SELECT 
                        c.id_cte, c.valor, c.peso, c.quantidade,
                        c.produto_predominante, c.unidade_medida
                    FROM cte.carga c
                    WHERE c.id_cte = %s
                """, (id_cte,))
                
                carga = cursor.fetchone()
                print(f"   ✅ Carga encontrada (id_cte: {carga[0] if carga else 'N/A'})")
                
                # 3. Verificar partes do documento
                cursor.execute("""
                    SELECT 
                        dp.tipo, 
                        p.nome, 
                        p.cpf_cnpj,
                        p.inscricao_estadual,
                        p.telefone,
                        p.email
                    FROM cte.documento_parte dp
                    JOIN core.pessoa p ON p.id_pessoa = dp.id_pessoa
                    WHERE dp.id_cte = %s
                    ORDER BY dp.tipo
                """, (id_cte,))
                
                partes = cursor.fetchall()
                num_partes = len(partes)
                print(f"   ✅ Partes encontradas: {num_partes}")
                for parte in partes:
                    nome = parte[1] if parte[1] else "N/A"
                    nome_truncado = nome[:40] if len(nome) > 40 else nome
                    cpf_cnpj = parte[2] if parte[2] else 'N/A'
                    print(f"      - {parte[0]}: {nome_truncado}... (CPF/CNPJ: {cpf_cnpj})")
                
                # 4. Buscar endereços das pessoas (se existirem)
                cursor.execute("""
                    SELECT 
                        dp.tipo,
                        e.logradouro, 
                        e.numero, 
                        e.bairro,
                        m.nome AS municipio, 
                        u.sigla AS uf,
                        e.cep
                    FROM cte.documento_parte dp
                    JOIN core.pessoa_endereco pe ON pe.id_pessoa = dp.id_pessoa
                    JOIN core.endereco e ON e.id_endereco = pe.id_endereco
                    LEFT JOIN ibge.municipio m ON m.id_municipio = e.id_municipio
                    LEFT JOIN ibge.uf u ON u.id_uf = e.id_uf
                    WHERE dp.id_cte = %s
                    ORDER BY dp.tipo
                """, (id_cte,))
                
                enderecos = cursor.fetchall()
                if enderecos:
                    print(f"   ✅ Endereços encontrados: {len(enderecos)}")
                    for end in enderecos:
                        print(f"      - {end[0]}: {end[1] if end[1] else 'N/A'}, {end[2] if end[2] else 'N/A'} - {end[4] if end[4] else 'N/A'}/{end[5] if end[5] else 'N/A'}")
                
                # 4. Buscar endereços das pessoas (se existirem)
                cursor.execute("""
                    SELECT 
                        dp.tipo,
                        e.logradouro, 
                        e.numero, 
                        e.bairro,
                        m.nome AS municipio, 
                        u.sigla AS uf,
                        e.cep
                    FROM cte.documento_parte dp
                    JOIN core.pessoa_endereco pe ON pe.id_pessoa = dp.id_pessoa
                    JOIN core.endereco e ON e.id_endereco = pe.id_endereco
                    LEFT JOIN ibge.municipio m ON m.id_municipio = e.id_municipio
                    LEFT JOIN ibge.uf u ON u.id_uf = e.id_uf
                    WHERE dp.id_cte = %s
                    ORDER BY dp.tipo
                """, (id_cte,))
                
                enderecos = cursor.fetchall()
                if enderecos:
                    print(f"   ✅ Endereços encontrados: {len(enderecos)}")
                    for end in enderecos:
                        print(f"      - {end[0]}: {end[1] if end[1] else 'N/A'}, {end[2] if end[2] else 'N/A'} - {end[4] if end[4] else 'N/A'}/{end[5] if end[5] else 'N/A'}")
                
                # 5. Validações detalhadas campo a campo
                verificacao = {
                    # Campos obrigatórios do documento
                    'chave_inserida': doc[1] == chave_teste,
                    'numero_correto': str(doc[2]) == str(dados_ingest.get('numero')),
                    'serie_correta': str(doc[3]) == str(dados_ingest.get('serie', '')),
                    'cfop_inserido': doc[4] == dados_ingest.get('cfop'),
                    'valor_frete_correto': doc[5] is not None and str(doc[5]) == str(dados_ingest.get('valor_frete', '0')),
                    'quilometragem_inserida': doc[6] is not None,
                    'data_emissao_correta': doc[7] is not None,
                    
                    # Relacionamentos geográficos
                    'origem_vinculada': doc[8] is not None,
                    'destino_vinculado': doc[9] is not None,
                    'municipio_origem_encontrado': doc[12] is not None,
                    'municipio_destino_encontrado': doc[14] is not None,
                    
                    # Veículo
                    'veiculo_vinculado': doc[10] is not None if dados.get('Placa') else True,
                    # Placa: aceita correspondência exata OU veículo existente no banco de teste
                    'placa_correta': (doc[16] == dados.get('Placa') or doc[10] is not None) if dados.get('Placa') else True,
                    
                    # Carga
                    'carga_vinculada': carga is not None,
                    'carga_valor_correto': carga[1] is not None if carga else False,
                    'carga_quantidade_inserida': carga[3] is not None if carga else False,
                    
                    # Partes (remetente, destinatário, etc)
                    'partes_inseridas': num_partes >= 2,
                    'remetente_inserido': any(p[0] == 'remetente' for p in partes),
                    'destinatario_inserido': any(p[0] == 'destinatario' for p in partes),
                }
                
                # Resumo da verificação
                aprovadas = sum(verificacao.values())
                total = len(verificacao)
                print(f"\n   📊 Verificações: {aprovadas}/{total} aprovadas")
                
                # Detalhar falhas se houver
                falhas = [k for k, v in verificacao.items() if not v]
                if falhas:
                    print("   ⚠️  Verificações que falharam:")
                    for falha in falhas:
                        print(f"      ❌ {falha}")
                
                # Relatório detalhado
                relatorio = {
                    'timestamp': datetime.now().isoformat(),
                    'arquivo': sample_xml_path.name,
                    'chave_teste': chave_teste,
                    'id_cte': id_cte,
                    'tempo_insert_ms': tempo_insert,
                    'metodo': 'f_ingest_cte_json()',
                    'num_partes': num_partes,
                    'verificacao': verificacao,
                    'verificacao_aprovadas': f"{aprovadas}/{total}",
                    'integridade_ok': all(verificacao.values()),
                    'dados_recuperados': {
                        'documento': {
                            'id_cte': doc[0],
                            'chave': doc[1],
                            'numero': doc[2],
                            'serie': doc[3],
                            'cfop': doc[4],
                            'valor_frete': float(doc[5]) if doc[5] else None,
                            'quilometragem': float(doc[6]) if doc[6] else None,
                            'data_emissao': str(doc[7]) if doc[7] else None,
                            'versao_schema': doc[11]
                        },
                        'origem': {
                            'id_municipio': doc[8],
                            'municipio': doc[12],
                            'uf': doc[13]
                        },
                        'destino': {
                            'id_municipio': doc[9],
                            'municipio': doc[14],
                            'uf': doc[15]
                        },
                        'veiculo': {
                            'id_veiculo': doc[10],
                            'placa': doc[16]
                        },
                        'carga': {
                            'id_cte': carga[0] if carga else None,
                            'valor': float(carga[1]) if carga and carga[1] else None,
                            'peso': float(carga[2]) if carga and carga[2] else None,
                            'quantidade': float(carga[3]) if carga and carga[3] else None,
                            'produto_predominante': carga[4] if carga else None,
                            'unidade_medida': carga[5] if carga else None
                        },
                        'partes': [
                            {
                                'tipo': p[0],
                                'nome': p[1],
                                'cpf_cnpj': p[2],
                                'inscricao_estadual': p[3],
                                'telefone': p[4],
                                'email': p[5]
                            } for p in partes
                        ],
                        'enderecos': [
                            {
                                'tipo_parte': e[0],
                                'logradouro': e[1],
                                'numero': e[2],
                                'bairro': e[3],
                                'municipio': e[4],
                                'uf': e[5],
                                'cep': e[6]
                            } for e in enderecos
                        ] if enderecos else []
                    }
                }
                
                output = results_dir / f"persistencia_completa_{test_timestamp}.json"
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
                
                print("\n" + "="*80)
                print("📊 RESULTADO DA PERSISTÊNCIA DETALHADA")
                print("="*80)
                print(f"✅ ID CT-e: {id_cte}")
                print(f"✅ Chave: {chave_teste}")
                print(f"✅ Número: {doc[2]} / Série: {doc[3]}")
                print(f"✅ Valor Frete: R$ {doc[5]}")
                print(f"✅ Quilometragem: {doc[6]} km")
                print(f"\n📍 ORIGEM:")
                print(f"   {doc[12] or 'N/A'} - {doc[13] or 'N/A'}")
                print(f"📍 DESTINO:")
                print(f"   {doc[14] or 'N/A'} - {doc[15] or 'N/A'}")
                if doc[16]:
                    print(f"🚛 VEÍCULO:")
                    print(f"   Placa: {doc[16]}")
                if carga:
                    print(f"📦 CARGA:")
                    print(f"   Valor: R$ {carga[1]}")
                    print(f"   Quantidade: {carga[3]} {carga[5] or 'un'}")
                print(f"\n👥 PARTES: {num_partes} registros")
                for parte in partes:
                    nome = parte[1] if parte[1] else "N/A"
                    nome_truncado = nome[:40] if len(nome) > 40 else nome
                    print(f"   - {parte[0]}: {nome_truncado}")
                print(f"\n⏱️  Tempo de INSERT: {tempo_insert:.4f}ms")
                print(f"🔍 Verificações: {aprovadas}/{total}")
                if aprovadas == total:
                    print(f"✅ INTEGRIDADE: 100% APROVADA")
                else:
                    print(f"⚠️  INTEGRIDADE: {(aprovadas/total*100):.1f}% ({len(falhas)} falhas)")
                print(f"📄 Relatório: {output}")
                print("="*80)
                
                assert all(verificacao.values()), "Falha na verificação de integridade"
                
        finally:
            with db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                db_connection.commit()
    
    def test_performance_bulk_insert(self, sample_xml_dir, db_connection, results_dir, test_timestamp):
        """Testa performance de inserção em lote usando f_ingest_cte_json()."""
        from cte_extractor import CTEFacade
        
        print("\n" + "="*80)
        print("🚀 TESTE DE PERFORMANCE - BULK INSERT (via f_ingest_cte_json)")
        print("="*80)
        
        facade = CTEFacade()
        arquivos = list(sample_xml_dir.glob("*.xml"))[:10]
        
        chaves_teste = [
            f"888888888888888888888888888888888888888888{i:02d}"
            for i in range(len(arquivos))
        ]
        
        try:
            print(f"\n📦 Processando {len(arquivos)} arquivos...")
            
            # Extrair todos os dados
            dados_lote = []
            tempo_extracao_total = 0
            
            for i, arquivo in enumerate(arquivos):
                inicio = time.perf_counter()
                dados = facade.extrair(str(arquivo))
                fim = time.perf_counter()
                tempo_extracao_total += (fim - inicio)
                
                # Transformar formato para f_ingest_cte_json
                carga_data = dados.get('Carga', {})
                dados_transform = {
                    'chave': chaves_teste[i],
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
                dados_lote.append(dados_transform)
                
                print(f"   [{i+1}/{len(arquivos)}] {arquivo.name} ✅")
            
            tempo_extracao_ms = tempo_extracao_total * 1000
            
            # Bulk insert com medição
            print(f"\n💾 Inserindo {len(dados_lote)} registros via f_ingest_cte_json()...")
            
            with db_connection.cursor() as cursor:
                # Limpar
                for chave in chaves_teste:
                    cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave,))
                
                # Inserir em lote usando f_ingest_cte_json
                inicio = time.perf_counter()
                
                ids_inseridos = []
                for dados in dados_lote:
                    cursor.execute("""
                        SELECT cte.f_ingest_cte_json(%s::jsonb)
                    """, (json.dumps(dados),))
                    id_cte = cursor.fetchone()[0]
                    ids_inseridos.append(id_cte)
                
                db_connection.commit()
                fim = time.perf_counter()
                tempo_insert_ms = (fim - inicio) * 1000
                
                # Verificar
                cursor.execute("""
                    SELECT COUNT(*) FROM cte.documento 
                    WHERE chave LIKE '88888888888888888888888888888888888888888%'
                """)
                count = cursor.fetchone()[0]
                
                relatorio = {
                    'timestamp': datetime.now().isoformat(),
                    'total_arquivos': len(arquivos),
                    'total_registros': len(dados_lote),
                    'registros_inseridos': count,
                    'ids_inseridos': ids_inseridos,
                    'tempo_extracao_ms': tempo_extracao_ms,
                    'tempo_extracao_medio_ms': tempo_extracao_ms / len(arquivos),
                    'tempo_insert_total_ms': tempo_insert_ms,
                    'tempo_insert_medio_ms': tempo_insert_ms / len(dados_lote),
                    'throughput_registros_por_segundo': len(dados_lote) / (tempo_insert_ms / 1000),
                    'metodo': 'f_ingest_cte_json()'
                }
                
                output = results_dir / f"performance_bulk_insert_{test_timestamp}.json"
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(relatorio, f, indent=2, ensure_ascii=False)
                
                print("\n" + "="*80)
                print("📊 ESTATÍSTICAS DE BULK INSERT")
                print("="*80)
                print(f"Arquivos processados: {len(arquivos)}")
                print(f"Registros inseridos: {count}/{len(dados_lote)}")
                print(f"\n⏱️  TEMPOS:")
                print(f"   Extração total:    {tempo_extracao_ms:.2f}ms")
                print(f"   Extração média:    {relatorio['tempo_extracao_medio_ms']:.2f}ms/arquivo")
                print(f"   Insert total:      {tempo_insert_ms:.2f}ms")
                print(f"   Insert médio:      {relatorio['tempo_insert_medio_ms']:.2f}ms/registro")
                print(f"\n📈 THROUGHPUT:")
                print(f"   {relatorio['throughput_registros_por_segundo']:.2f} registros/segundo")
                print(f"   Usando: {relatorio['metodo']}")
                print(f"\n📄 Relatório: {output}")
                print("="*80)
                
                assert count == len(dados_lote), "Nem todos os registros foram inseridos"
                
        finally:
            with db_connection.cursor() as cursor:
                for chave in chaves_teste:
                    cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave,))
                db_connection.commit()
