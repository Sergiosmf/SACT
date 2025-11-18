#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatórios de Testes para Artigo Científico
Executa testes e gera relatórios detalhados com métricas e estatísticas
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Any
from collections import defaultdict


class TestReportGenerator:
    """Gerador de relatórios detalhados de testes"""
    
    def __init__(self, output_dir: Path = None):
        self.test_dir = Path(__file__).parent
        self.output_dir = output_dir or self.test_dir / 'resultados'
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now()
        self.results = {
            'metadata': {
                'timestamp': self.timestamp.isoformat(),
                'date': self.timestamp.strftime('%Y-%m-%d'),
                'time': self.timestamp.strftime('%H:%M:%S'),
                'python_version': sys.version,
                'working_directory': str(self.test_dir)
            },
            'categories': {},
            'summary': {},
            'metrics': {}
        }
    
    def run_pytest_with_json(self, category: str, display_name: str) -> Dict[str, Any]:
        """Executa pytest e captura resultados em JSON"""
        print(f"\n{'='*80}")
        print(f"🧪 Executando: {display_name}")
        print(f"{'='*80}")
        
        json_report = self.output_dir / f'pytest_{category}.json'
        
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.test_dir / category),
            '-v',
            '--tb=short',
            f'--json-report',
            f'--json-report-file={json_report}',
            '--json-report-indent=2'
        ]
        
        print(f"📝 Comando: {' '.join(cmd)}\n")
        
        # Capturar saída
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.test_dir
        )
        
        # Parsear saída do pytest
        output_lines = result.stdout.split('\n')
        
        # Extrair estatísticas da última linha
        stats = self._parse_pytest_output(result.stdout)
        
        # Extrair detalhes dos testes
        test_details = self._extract_test_details(result.stdout)
        
        # Tentar carregar relatório JSON se existir
        json_data = {}
        if json_report.exists():
            try:
                with open(json_report, 'r') as f:
                    json_data = json.load(f)
            except:
                pass
        
        category_result = {
            'name': display_name,
            'category': category,
            'return_code': result.returncode,
            'passed': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'statistics': stats,
            'test_details': test_details,
            'json_report': json_data,
            'duration': stats.get('duration', 0)
        }
        
        # Exibir resultado
        status = "✅ PASSOU" if result.returncode == 0 else f"❌ FALHOU"
        print(f"\n{status} - {display_name}")
        print(f"Testes: {stats.get('total', 0)} | "
              f"Passou: {stats.get('passed', 0)} | "
              f"Falhou: {stats.get('failed', 0)} | "
              f"Duração: {stats.get('duration', 0):.2f}s")
        
        return category_result
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Extrai estatísticas da saída do pytest"""
        stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'warnings': 0,
            'duration': 0.0
        }
        
        # Procurar linha de resumo: "10 passed in 2.45s"
        summary_pattern = r'(\d+)\s+passed'
        failed_pattern = r'(\d+)\s+failed'
        skipped_pattern = r'(\d+)\s+skipped'
        error_pattern = r'(\d+)\s+error'
        warning_pattern = r'(\d+)\s+warning'
        duration_pattern = r'in\s+([\d.]+)s'
        
        for line in output.split('\n'):
            if 'passed' in line.lower() or 'failed' in line.lower():
                # Passed
                match = re.search(summary_pattern, line)
                if match:
                    stats['passed'] = int(match.group(1))
                
                # Failed
                match = re.search(failed_pattern, line)
                if match:
                    stats['failed'] = int(match.group(1))
                
                # Skipped
                match = re.search(skipped_pattern, line)
                if match:
                    stats['skipped'] = int(match.group(1))
                
                # Errors
                match = re.search(error_pattern, line)
                if match:
                    stats['errors'] = int(match.group(1))
                
                # Warnings
                match = re.search(warning_pattern, line)
                if match:
                    stats['warnings'] = int(match.group(1))
                
                # Duration
                match = re.search(duration_pattern, line)
                if match:
                    stats['duration'] = float(match.group(1))
        
        stats['total'] = stats['passed'] + stats['failed'] + stats['skipped']
        
        return stats
    
    def _extract_test_details(self, output: str) -> List[Dict[str, str]]:
        """Extrai detalhes individuais de cada teste"""
        test_details = []
        
        # Padrão mais flexível: captura diferentes formatos do pytest -v
        # Formato 1: test_arquivo.py::TestClass::test_nome PASSED
        pattern1 = r'([\w/]+\.py)::([\w:]+)\s+(PASSED|FAILED|SKIPPED)'
        # Formato 2: test_arquivo.py::test_nome PASSED
        pattern2 = r'([\w/]+\.py)::(test_\w+)\s+(PASSED|FAILED|SKIPPED)'
        
        matches = list(re.finditer(pattern1, output)) + list(re.finditer(pattern2, output))
        
        seen_tests = set()
        
        for match in matches:
            file_path = match.group(1)
            test_path = match.group(2)
            status = match.group(3)
            
            # Evitar duplicatas
            test_id = f"{file_path}::{test_path}"
            if test_id in seen_tests:
                continue
            seen_tests.add(test_id)
            
            # Extrair nome do arquivo e do teste
            file_name = file_path.split('/')[-1].replace('.py', '')
            test_parts = test_path.split('::')
            
            # Nome legível do teste
            test_name = test_parts[-1].replace('test_', '').replace('_', ' ').title()
            
            test_details.append({
                'file': file_name,
                'full_path': test_path,
                'name': test_name,
                'status': status,
                'description': self._get_test_description(file_name, test_name)
            })
        
        # Se não conseguiu extrair pelo regex, tentar parse do JSON report
        if not test_details:
            test_details = self._extract_from_lines(output)
        
        return test_details
    
    def _extract_from_lines(self, output: str) -> List[Dict[str, str]]:
        """Fallback: extrai testes olhando linha por linha"""
        test_details = []
        
        # Primeiro, juntar linhas quebradas
        lines = output.split('\n')
        joined_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Se linha termina sem PASSED/FAILED/SKIPPED e próxima tem, juntar
            if '.py::' in line and not any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED']):
                # Procurar status nas próximas linhas
                for j in range(i+1, min(i+5, len(lines))):
                    if any(status in lines[j] for status in ['PASSED', 'FAILED', 'SKIPPED']):
                        line = line.strip() + ' ' + lines[j].strip()
                        i = j
                        break
            joined_lines.append(line)
            i += 1
        
        # Agora processar linhas unificadas
        for line in joined_lines:
            # Procurar por linhas que contenham .py:: e PASSED/FAILED/SKIPPED
            if '.py::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                # Determinar status
                status = 'PASSED' if 'PASSED' in line else 'FAILED' if 'FAILED' in line else 'SKIPPED'
                
                # Extrair o caminho do teste
                # Formato: path/test.py::Class::method PASSED
                match = re.search(r'([\w/]+\.py)::([\w:]+)', line)
                if match:
                    file_part = match.group(1)
                    test_part = match.group(2)
                    
                    file_name = file_part.split('/')[-1].replace('.py', '')
                    
                    # Extrair nome do teste (última parte após ::)
                    test_parts = test_part.split('::')
                    test_name = test_parts[-1].replace('test_', '').replace('_', ' ').title()
                    
                    test_details.append({
                        'file': file_name,
                        'full_path': test_part,
                        'name': test_name,
                        'status': status,
                        'description': self._get_test_description(file_name, test_name)
                    })
        
        return test_details
    
    def _get_test_description(self, file_name: str, test_name: str) -> str:
        """Retorna descrição do que o teste valida"""
        descriptions = {
            # Testes Unitários - test_unitarios.py
            'test_unitarios': {
                'Arquivo Xml Existe': 'Verifica se arquivo XML de CT-e existe no sistema',
                'Xml Bem Formado': 'Valida estrutura XML bem-formada e namespace correto',
                'Extrair Chave Cte': 'Extrai e valida chave de acesso do CT-e (44 dígitos)',
                'Extrair Numero Cte': 'Extrai número do documento CT-e do XML',
                'Extrair Emitente': 'Extrai CNPJ e razão social do emitente',
                'Validar Chave Cte': 'Valida formato da chave CT-e (44 dígitos numéricos)',
                'Validar Cnpj': 'Valida dígitos verificadores de CNPJ',
                'Validar Cpf': 'Valida dígitos verificadores de CPF',
                'Validar Valores Numericos': 'Valida tipos e formatos de valores monetários',
                'Importar Modulo': 'Testa importação do módulo cte_extractor',
                'Criar Facade': 'Instancia CTEFacade para extração de dados',
                'Extrair Xml': 'Extrai dados completos de arquivo XML real',
                'Tempo Extracao Xml': 'Valida performance (< 1s por extração)',
                'Conectar Banco': 'Testa conexão com PostgreSQL',
                'Verificar Schemas': 'Valida existência de schemas cte, core, ibge',
                'Crud Basico': 'Testa operações CREATE, READ, UPDATE, DELETE'
            },
            # Testes Unitários - test_persistencia_avancada.py
            'test_persistencia_avancada': {
                'Insert Cte Completo': 'Insere CT-e completo com dados reais no banco',
                'Performance Bulk Insert': 'Testa inserção em lote de múltiplos CT-es',
                'Update Dados Cte': 'Atualiza dados existentes no banco',
                'Delete Com Integridade': 'Remove dados mantendo integridade referencial',
                'Consulta Com Joins': 'Valida queries com múltiplas tabelas',
                'Transacao Rollback': 'Testa rollback de transação em erro'
            },
            # Testes Funcionais
            'test_funcionais': {
                'Processar Lote Arquivos': 'Processa lote de 5 arquivos XML',
                'Gerar Relatorio Processamento': 'Gera relatório JSON de processamento',
                'Fluxo Completo Pipeline': 'Executa pipeline completo: descoberta → extração → relatório',
                'Pipeline Com Persistencia': 'Pipeline completo com gravação no banco',
                'Validar Dados Persistidos': 'Valida integridade dos dados gravados',
                'Recuperacao Erro': 'Testa recuperação após erro de processamento'
            },
            # Testes Integração
            'test_integracao': {
                'Integracao 4 Camadas': 'Testa integração Upload → Extração → Parsing → Persistência',
                'Lote 4 Camadas': 'Processa lote através das 4 camadas',
                'Verificar Integridade': 'Valida integridade de dados entre camadas',
                'Performance Integracao': 'Mede performance do fluxo integrado',
                'Consistencia Dados': 'Valida consistência de dados no fluxo completo'
            }
        }
        
        # Buscar descrição específica
        if file_name in descriptions:
            return descriptions[file_name].get(test_name, 'Teste de validação do sistema')
        
        # Descrição genérica baseada no nome
        return f'Valida: {test_name.lower()}'
    
    def run_all_tests(self):
        """Executa todas as categorias de testes"""
        print(f"\n{'='*80}")
        print("🎯 EXECUÇÃO COMPLETA DE TESTES - GERAÇÃO DE RELATÓRIO")
        print(f"{'='*80}")
        print(f"⏰ Início: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Categorias de teste
        categories = [
            ('unitarios/', 'Testes Unitários'),
            ('funcionais/', 'Testes Funcionais'),
            ('integracao/', 'Testes de Integração')
        ]
        
        # Executar cada categoria
        for category_path, display_name in categories:
            category_key = category_path.rstrip('/')
            self.results['categories'][category_key] = self.run_pytest_with_json(
                category_path,
                display_name
            )
        
        # Gerar sumário
        self._generate_summary()
        
        # Gerar métricas
        self._generate_metrics()
        
        # Salvar relatórios
        self._save_reports()
        
        # Exibir resumo
        self._display_summary()
    
    def _generate_summary(self):
        """Gera sumário dos resultados"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_duration = 0.0
        categories_passed = 0
        
        for category, data in self.results['categories'].items():
            stats = data['statistics']
            total_tests += stats['total']
            total_passed += stats['passed']
            total_failed += stats['failed']
            total_skipped += stats['skipped']
            total_duration += stats['duration']
            
            if data['passed']:
                categories_passed += 1
        
        total_categories = len(self.results['categories'])
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        category_success_rate = (categories_passed / total_categories * 100) if total_categories > 0 else 0
        
        self.results['summary'] = {
            'total_categories': total_categories,
            'categories_passed': categories_passed,
            'categories_failed': total_categories - categories_passed,
            'category_success_rate': round(category_success_rate, 2),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'success_rate': round(success_rate, 2),
            'failure_rate': round((total_failed / total_tests * 100) if total_tests > 0 else 0, 2),
            'total_duration': round(total_duration, 2),
            'avg_duration_per_test': round((total_duration / total_tests) if total_tests > 0 else 0, 4)
        }
    
    def _generate_metrics(self):
        """Gera métricas detalhadas para análise"""
        metrics_by_category = {}
        
        for category, data in self.results['categories'].items():
            stats = data['statistics']
            
            metrics_by_category[category] = {
                'coverage': {
                    'tests_executed': stats['total'],
                    'tests_passed': stats['passed'],
                    'tests_failed': stats['failed'],
                    'success_rate': round((stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2)
                },
                'performance': {
                    'total_duration_seconds': stats['duration'],
                    'avg_duration_per_test': round((stats['duration'] / stats['total']) if stats['total'] > 0 else 0, 4)
                },
                'quality': {
                    'warnings': stats.get('warnings', 0),
                    'errors': stats.get('errors', 0),
                    'skipped': stats.get('skipped', 0)
                }
            }
        
        self.results['metrics'] = {
            'by_category': metrics_by_category,
            'overall': {
                'reliability': self.results['summary']['success_rate'],
                'efficiency': round(self.results['summary']['avg_duration_per_test'] * 1000, 2),  # em ms
                'completeness': round((self.results['summary']['total_tests'] / 
                                      (self.results['summary']['total_tests'] + 
                                       self.results['summary']['total_skipped']) * 100) 
                                     if (self.results['summary']['total_tests'] + 
                                         self.results['summary']['total_skipped']) > 0 else 0, 2)
            }
        }
    
    def _save_reports(self):
        """Salva relatórios em diferentes formatos"""
        timestamp_str = self.timestamp.strftime('%Y%m%d_%H%M%S')
        
        # 1. Relatório JSON completo
        json_file = self.output_dir / f'report_{timestamp_str}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Relatório JSON: {json_file}")
        
        # 2. Relatório Markdown para documentação
        md_file = self.output_dir / f'report_{timestamp_str}.md'
        self._generate_markdown_report(md_file)
        print(f"💾 Relatório Markdown: {md_file}")
        
        # 3. Sumário executivo (para artigo)
        summary_file = self.output_dir / f'summary_{timestamp_str}.md'
        self._generate_executive_summary(summary_file)
        print(f"💾 Sumário Executivo: {summary_file}")
        
        # 4. Tabela de resultados (LaTeX format)
        latex_file = self.output_dir / f'table_{timestamp_str}.tex'
        self._generate_latex_table(latex_file)
        print(f"💾 Tabela LaTeX: {latex_file}")
        
        # 5. Link simbólico para o mais recente
        latest_json = self.output_dir / 'latest_report.json'
        latest_md = self.output_dir / 'latest_report.md'
        
        if latest_json.exists():
            latest_json.unlink()
        if latest_md.exists():
            latest_md.unlink()
        
        latest_json.symlink_to(json_file.name)
        latest_md.symlink_to(md_file.name)
    
    def _generate_markdown_report(self, filepath: Path):
        """Gera relatório formatado em Markdown"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Relatório de Testes - Sistema CT-e\n\n")
            f.write(f"**Data:** {self.results['metadata']['date']}\n")
            f.write(f"**Hora:** {self.results['metadata']['time']}\n\n")
            
            f.write(f"## 📊 Sumário Executivo\n\n")
            s = self.results['summary']
            f.write(f"- **Total de Categorias:** {s['total_categories']}\n")
            f.write(f"- **Categorias Aprovadas:** {s['categories_passed']} ({s['category_success_rate']}%)\n")
            f.write(f"- **Total de Testes:** {s['total_tests']}\n")
            f.write(f"- **Testes Aprovados:** {s['total_passed']} ({s['success_rate']}%)\n")
            f.write(f"- **Testes Reprovados:** {s['total_failed']} ({s['failure_rate']}%)\n")
            f.write(f"- **Duração Total:** {s['total_duration']}s\n")
            f.write(f"- **Duração Média por Teste:** {s['avg_duration_per_test']}s\n\n")
            
            f.write(f"## 🎯 Métricas de Qualidade\n\n")
            m = self.results['metrics']['overall']
            f.write(f"- **Confiabilidade:** {m['reliability']}%\n")
            f.write(f"- **Eficiência:** {m['efficiency']}ms por teste\n")
            f.write(f"- **Completude:** {m['completeness']}%\n\n")
            
            f.write(f"## 📁 Resultados por Categoria\n\n")
            for category, data in self.results['categories'].items():
                status = "✅ PASSOU" if data['passed'] else "❌ FALHOU"
                f.write(f"### {data['name']} {status}\n\n")
                
                stats = data['statistics']
                f.write(f"- **Total de Testes:** {stats['total']}\n")
                f.write(f"- **Aprovados:** {stats['passed']}\n")
                f.write(f"- **Reprovados:** {stats['failed']}\n")
                f.write(f"- **Ignorados:** {stats['skipped']}\n")
                f.write(f"- **Duração:** {stats['duration']}s\n")
                
                metrics = self.results['metrics']['by_category'][category]
                f.write(f"- **Taxa de Sucesso:** {metrics['coverage']['success_rate']}%\n\n")
                
                # NOVO: Detalhar o que foi testado
                if 'test_details' in data and data['test_details']:
                    f.write(f"#### 🔍 Detalhes dos Testes\n\n")
                    f.write(f"| # | Teste | Status | O Que Foi Testado |\n")
                    f.write(f"|---|-------|--------|-------------------|\n")
                    
                    for idx, test in enumerate(data['test_details'], 1):
                        status_icon = "✅" if test['status'] == 'PASSED' else "❌" if test['status'] == 'FAILED' else "⏭️"
                        f.write(f"| {idx} | {test['name']} | {status_icon} | {test['description']} |\n")
                    
                    f.write(f"\n")
                
                # Agrupar por tipo
                if 'test_details' in data and data['test_details']:
                    passed_tests = [t for t in data['test_details'] if t['status'] == 'PASSED']
                    failed_tests = [t for t in data['test_details'] if t['status'] == 'FAILED']
                    
                    if passed_tests:
                        f.write(f"**✅ Testes Aprovados ({len(passed_tests)}):**\n")
                        for test in passed_tests:
                            f.write(f"- {test['name']}: {test['description']}\n")
                        f.write(f"\n")
                    
                    if failed_tests:
                        f.write(f"**❌ Testes Reprovados ({len(failed_tests)}):**\n")
                        for test in failed_tests:
                            f.write(f"- {test['name']}: {test['description']}\n")
                        f.write(f"\n")
    
    def _generate_executive_summary(self, filepath: Path):
        """Gera sumário executivo para o artigo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Sumário Executivo - Resultados dos Testes\n\n")
            f.write(f"*Gerado em: {self.results['metadata']['date']} às {self.results['metadata']['time']}*\n\n")
            
            s = self.results['summary']
            m = self.results['metrics']['overall']
            
            f.write(f"## Visão Geral\n\n")
            f.write(f"O sistema foi submetido a **{s['total_tests']} testes** distribuídos em "
                   f"**{s['total_categories']} categorias** (Unitários, Funcionais e Integração). ")
            f.write(f"Os resultados demonstram uma taxa de sucesso de **{s['success_rate']}%**, ")
            f.write(f"com **{s['total_passed']} testes aprovados** e **{s['total_failed']} reprovados**.\n\n")
            
            f.write(f"## Métricas de Qualidade\n\n")
            f.write(f"- **Confiabilidade:** {m['reliability']}% dos testes executados com sucesso\n")
            f.write(f"- **Eficiência:** Tempo médio de {m['efficiency']}ms por teste\n")
            f.write(f"- **Completude:** {m['completeness']}% de cobertura dos testes planejados\n\n")
            
            f.write(f"## Resultados por Categoria\n\n")
            f.write(f"| Categoria | Testes | Aprovados | Taxa de Sucesso | Duração |\n")
            f.write(f"|-----------|--------|-----------|-----------------|----------|\n")
            
            for category, data in self.results['categories'].items():
                stats = data['statistics']
                metrics = self.results['metrics']['by_category'][category]
                f.write(f"| {data['name']} | {stats['total']} | {stats['passed']} | "
                       f"{metrics['coverage']['success_rate']}% | {stats['duration']}s |\n")
            
            # NOVO: Seção detalhada do que foi testado
            f.write(f"\n## 🔍 O Que Foi Testado\n\n")
            
            for category, data in self.results['categories'].items():
                if 'test_details' in data and data['test_details']:
                    f.write(f"### {data['name']}\n\n")
                    
                    # Agrupar por arquivo/módulo
                    tests_by_file = defaultdict(list)
                    for test in data['test_details']:
                        tests_by_file[test['file']].append(test)
                    
                    for file_name, tests in tests_by_file.items():
                        f.write(f"**Módulo: `{file_name}`**\n\n")
                        for test in tests:
                            status_icon = "✅" if test['status'] == 'PASSED' else "❌" if test['status'] == 'FAILED' else "⏭️"
                            f.write(f"- {status_icon} **{test['name']}**: {test['description']}\n")
                        f.write(f"\n")
            
            f.write(f"## Conclusão\n\n")
            if s['success_rate'] >= 95:
                f.write(f"Os resultados indicam **excelente qualidade** do sistema, com taxa de sucesso "
                       f"superior a 95%. O sistema está pronto para produção.\n")
            elif s['success_rate'] >= 80:
                f.write(f"Os resultados indicam **boa qualidade** do sistema, com taxa de sucesso "
                       f"acima de 80%. Recomenda-se correção dos testes falhados antes da produção.\n")
            else:
                f.write(f"Os resultados indicam necessidade de **melhorias**, com taxa de sucesso "
                       f"abaixo de 80%. Revisão crítica necessária antes da produção.\n")
            
            # Adicionar resumo dos aspectos validados
            f.write(f"\n## 📋 Aspectos Validados\n\n")
            f.write(f"A suite de testes validou os seguintes aspectos críticos do sistema:\n\n")
            
            all_test_types = set()
            for category, data in self.results['categories'].items():
                if 'test_details' in data:
                    for test in data['test_details']:
                        # Extrair tipo de validação
                        desc_lower = test['description'].lower()
                        if 'xml' in desc_lower:
                            all_test_types.add('Processamento de XML')
                        if 'validação' in desc_lower or 'valida' in desc_lower:
                            all_test_types.add('Validação de Dados')
                        if 'banco' in desc_lower or 'persistência' in desc_lower or 'crud' in desc_lower:
                            all_test_types.add('Persistência em Banco de Dados')
                        if 'performance' in desc_lower or 'tempo' in desc_lower:
                            all_test_types.add('Performance e Eficiência')
                        if 'integração' in desc_lower or 'camadas' in desc_lower:
                            all_test_types.add('Integração entre Camadas')
                        if 'extração' in desc_lower or 'extrai' in desc_lower:
                            all_test_types.add('Extração de Dados')
            
            for test_type in sorted(all_test_types):
                f.write(f"- ✅ {test_type}\n")
            
            f.write(f"\n*Total de {s['total_tests']} testes executados em {s['total_duration']}s*\n")
    
    def _generate_latex_table(self, filepath: Path):
        """Gera tabela em formato LaTeX para o artigo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\\begin{table}[htbp]\n")
            f.write("\\centering\n")
            f.write("\\caption{Resultados dos Testes do Sistema CT-e}\n")
            f.write("\\label{tab:test-results}\n")
            f.write("\\begin{tabular}{lcccc}\n")
            f.write("\\hline\n")
            f.write("\\textbf{Categoria} & \\textbf{Testes} & \\textbf{Aprovados} & "
                   "\\textbf{Taxa} & \\textbf{Duração (s)} \\\\\n")
            f.write("\\hline\n")
            
            for category, data in self.results['categories'].items():
                stats = data['statistics']
                metrics = self.results['metrics']['by_category'][category]
                name = data['name'].replace('Testes ', '')
                f.write(f"{name} & {stats['total']} & {stats['passed']} & "
                       f"{metrics['coverage']['success_rate']}\\% & {stats['duration']:.2f} \\\\\n")
            
            f.write("\\hline\n")
            s = self.results['summary']
            f.write(f"\\textbf{{Total}} & {s['total_tests']} & {s['total_passed']} & "
                   f"{s['success_rate']}\\% & {s['total_duration']:.2f} \\\\\n")
            f.write("\\hline\n")
            f.write("\\end{tabular}\n")
            f.write("\\end{table}\n")
    
    def _display_summary(self):
        """Exibe resumo no console"""
        print(f"\n{'='*80}")
        print("📊 RESUMO FINAL DOS TESTES")
        print(f"{'='*80}\n")
        
        s = self.results['summary']
        
        print(f"📁 Categorias:")
        print(f"   Total: {s['total_categories']}")
        print(f"   Aprovadas: {s['categories_passed']} ({s['category_success_rate']}%)")
        print(f"   Reprovadas: {s['categories_failed']}\n")
        
        print(f"🧪 Testes:")
        print(f"   Total: {s['total_tests']}")
        print(f"   Aprovados: {s['total_passed']} ({s['success_rate']}%)")
        print(f"   Reprovados: {s['total_failed']} ({s['failure_rate']}%)")
        print(f"   Ignorados: {s['total_skipped']}\n")
        
        print(f"⏱️  Performance:")
        print(f"   Duração Total: {s['total_duration']}s")
        print(f"   Duração Média: {s['avg_duration_per_test']}s por teste\n")
        
        m = self.results['metrics']['overall']
        print(f"📈 Métricas de Qualidade:")
        print(f"   Confiabilidade: {m['reliability']}%")
        print(f"   Eficiência: {m['efficiency']}ms/teste")
        print(f"   Completude: {m['completeness']}%\n")
        
        print(f"💾 Relatórios salvos em: {self.output_dir}")
        print(f"{'='*80}\n")


def main():
    """Função principal"""
    generator = TestReportGenerator()
    generator.run_all_tests()
    
    # Código de saída baseado no sucesso
    success = generator.results['summary']['success_rate'] >= 80
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
