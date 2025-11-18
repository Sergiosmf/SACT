#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(I) TESTES UNITÁRIOS
Verificação de funções críticas de leitura, validação e persistência de dados
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path


@pytest.mark.unitario
class TestLeituraXML:
    """Testes de leitura e parsing de XML."""
    
    def test_arquivo_xml_existe(self, sample_xml_path):
        """Verifica se arquivo XML existe."""
        assert sample_xml_path.exists()
        assert sample_xml_path.suffix == ".xml"
    
    def test_xml_bem_formado(self, sample_xml_path):
        """Testa se XML está bem formado."""
        tree = ET.parse(str(sample_xml_path))
        root = tree.getroot()
        assert root is not None
    
    def test_extrair_chave_cte(self, sample_xml_path):
        """Testa extração da chave do CT-e."""
        tree = ET.parse(str(sample_xml_path))
        root = tree.getroot()
        ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        
        # Buscar chave no atributo Id
        inf_cte = root.find('.//cte:infCte', ns)
        if inf_cte is not None and 'Id' in inf_cte.attrib:
            chave = inf_cte.attrib['Id'].replace('CTe', '')
        else:
            # Buscar em chCTe
            ch_cte = root.find('.//cte:chCTe', ns)
            chave = ch_cte.text if ch_cte is not None else None
        
        assert chave is not None
        assert len(chave) == 44
        assert chave.isdigit()
    
    def test_extrair_numero_cte(self, sample_xml_path):
        """Testa extração do número do CT-e."""
        tree = ET.parse(str(sample_xml_path))
        root = tree.getroot()
        ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        
        nct = root.find('.//cte:ide/cte:nCT', ns)
        assert nct is not None
        assert nct.text.isdigit()
    
    def test_extrair_emitente(self, sample_xml_path):
        """Testa extração de dados do emitente."""
        tree = ET.parse(str(sample_xml_path))
        root = tree.getroot()
        ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        
        emit = root.find('.//cte:emit', ns)
        assert emit is not None
        
        # Deve ter CNPJ ou CPF
        cnpj = emit.find('cte:CNPJ', ns)
        cpf = emit.find('cte:CPF', ns)
        assert cnpj is not None or cpf is not None
        
        # Deve ter nome
        xnome = emit.find('cte:xNome', ns)
        assert xnome is not None
        assert xnome.text


@pytest.mark.unitario
class TestValidacaoDados:
    """Testes de validação de dados."""
    
    def test_validar_chave_cte(self):
        """Valida formato de chave CT-e."""
        chave_valida = "35210112345678901234570010000001234567890123"
        assert len(chave_valida) == 44
        assert chave_valida.isdigit()
    
    def test_validar_cnpj(self):
        """Valida formato de CNPJ."""
        cnpj = "12345678901234"
        assert len(cnpj) == 14
        assert cnpj.isdigit()
    
    def test_validar_cpf(self):
        """Valida formato de CPF."""
        cpf = "12345678901"
        assert len(cpf) == 11
        assert cpf.isdigit()
    
    def test_validar_valores_numericos(self):
        """Valida conversão de valores."""
        valores = ["100.00", "1000.50", "0.00"]
        for val_str in valores:
            valor = float(val_str)
            assert valor >= 0
            assert isinstance(valor, float)


@pytest.mark.unitario
class TestCTEExtractor:
    """Testes do módulo cte_extractor."""
    
    def test_importar_modulo(self):
        """Testa importação do cte_extractor."""
        import cte_extractor
        assert cte_extractor is not None
    
    def test_criar_facade(self):
        """Testa criação da facade."""
        from cte_extractor import CTEFacade
        facade = CTEFacade()
        assert facade is not None
        assert hasattr(facade, 'extrair')
    
    def test_extrair_xml(self, sample_xml_path):
        """Testa extração de dados do XML."""
        from cte_extractor import CTEFacade
        
        facade = CTEFacade()
        resultado = facade.extrair(str(sample_xml_path))
        
        assert resultado is not None
        assert isinstance(resultado, dict)
        assert len(resultado) > 0
    
    def test_tempo_extracao_xml(self, sample_xml_path, results_dir, test_timestamp):
        """Mede tempo de extração de um arquivo XML completo."""
        import time
        import json
        from cte_extractor import CTEFacade
        
        print("\n" + "="*80)
        print("⏱️  TESTE DE PERFORMANCE - TEMPO DE EXTRAÇÃO")
        print("="*80)
        
        facade = CTEFacade()
        
        # Aquecimento (warm-up)
        facade.extrair(str(sample_xml_path))
        
        # Medições múltiplas para precisão
        tempos = []
        num_execucoes = 10
        
        print(f"\n📊 Executando {num_execucoes} medições...")
        
        for i in range(num_execucoes):
            inicio = time.perf_counter()
            resultado = facade.extrair(str(sample_xml_path))
            fim = time.perf_counter()
            
            tempo_ms = (fim - inicio) * 1000
            tempos.append(tempo_ms)
            print(f"   Execução {i+1}: {tempo_ms:.4f}ms")
        
        # Estatísticas
        tempo_medio = sum(tempos) / len(tempos)
        tempo_min = min(tempos)
        tempo_max = max(tempos)
        tempo_total = sum(tempos)
        
        relatorio = {
            'arquivo': sample_xml_path.name,
            'tamanho_kb': sample_xml_path.stat().st_size / 1024,
            'num_execucoes': num_execucoes,
            'tempos_ms': tempos,
            'estatisticas': {
                'tempo_medio_ms': tempo_medio,
                'tempo_minimo_ms': tempo_min,
                'tempo_maximo_ms': tempo_max,
                'tempo_total_ms': tempo_total,
                'desvio_padrao_ms': (sum((t - tempo_medio)**2 for t in tempos) / len(tempos))**0.5
            },
            'campos_extraidos': len(resultado),
            'timestamp': test_timestamp
        }
        
        # Salvar relatório
        output = results_dir / f"performance_extracao_{test_timestamp}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("📊 ESTATÍSTICAS DE PERFORMANCE")
        print("="*80)
        print(f"Arquivo: {sample_xml_path.name}")
        print(f"Tamanho: {relatorio['tamanho_kb']:.2f} KB")
        print(f"Campos extraídos: {len(resultado)}")
        print(f"\n⏱️  TEMPOS:")
        print(f"   Médio:   {tempo_medio:.4f}ms")
        print(f"   Mínimo:  {tempo_min:.4f}ms")
        print(f"   Máximo:  {tempo_max:.4f}ms")
        print(f"   Desvio:  {relatorio['estatisticas']['desvio_padrao_ms']:.4f}ms")
        print(f"\n📄 Relatório: {output}")
        print("="*80)
        
        # Validações
        assert tempo_medio < 100, f"Tempo médio muito alto: {tempo_medio:.2f}ms"
        assert resultado is not None
        assert len(resultado) > 0


@pytest.mark.unitario
@pytest.mark.database
class TestPersistenciaDados:
    """Testes de persistência no banco."""
    
    def test_conectar_banco(self, db_connection):
        """Testa conexão com banco."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_verificar_schemas(self, db_connection):
        """Verifica se schemas existem."""
        schemas = ['cte', 'core', 'ibge']
        
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('cte', 'core', 'ibge')
            """)
            existentes = [row[0] for row in cursor.fetchall()]
        
        for schema in schemas:
            assert schema in existentes
    
    def test_crud_basico(self, db_connection):
        """Testa operações CRUD."""
        chave_teste = "99999999999999999999999999999999999999999999"
        
        try:
            with db_connection.cursor() as cursor:
                # Limpar
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                
                # Inserir (quilometragem é NOT NULL, precisa ser incluído)
                cursor.execute("""
                    INSERT INTO cte.documento (
                        chave, numero, serie, valor_frete, quilometragem
                    ) VALUES (%s, '999', '1', 100.00, 0)
                """, (chave_teste,))
                db_connection.commit()
                
                # Verificar
                cursor.execute("SELECT chave FROM cte.documento WHERE chave = %s", (chave_teste,))
                resultado = cursor.fetchone()
                assert resultado is not None
                
        finally:
            with db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM cte.documento WHERE chave = %s", (chave_teste,))
                db_connection.commit()
