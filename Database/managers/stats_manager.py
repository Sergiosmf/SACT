# -*- coding: utf-8 -*-
"""
Stats Manager - Gerenciamento de estatísticas e relatórios
"""

import time
from typing import Dict, Any
from datetime import datetime


class StatsManager:
    """
    Manager para controle de estatísticas e geração de relatórios.
    Implementa Single Responsibility Principle para métricas.
    """
    
    def __init__(self):
        """Inicializa o manager de estatísticas."""
        self.estatisticas = {
            'pessoas_inseridas': 0,
            'enderecos_inseridos': 0,
            'veiculos_inseridos': 0,
            'documentos_inseridos': 0,
            'documentos_duplicados': 0,
            'sucessos': 0,
            'erros': 0,
            'arquivos_processados': 0,
            'tempo_inicio': None,
            'tempo_fim': None
        }
        
        self.detalhes_erros = []
        self.arquivos_sucesso = []
        self.arquivos_erro = []
    
    def iniciar_cronometro(self) -> None:
        """Inicia contagem de tempo de processamento."""
        self.estatisticas['tempo_inicio'] = time.time()
        print(f"⏱️  Cronômetro iniciado: {datetime.now().strftime('%H:%M:%S')}")
    
    def parar_cronometro(self) -> float:
        """
        Para cronômetro e retorna tempo decorrido.
        
        Returns:
            Tempo total em segundos
        """
        self.estatisticas['tempo_fim'] = time.time()
        tempo_total = self.get_tempo_decorrido()
        print(f"⏱️  Cronômetro parado: {datetime.now().strftime('%H:%M:%S')}")
        return tempo_total
    
    def get_tempo_decorrido(self) -> float:
        """
        Calcula tempo decorrido desde início.
        
        Returns:
            Tempo em segundos
        """
        if not self.estatisticas['tempo_inicio']:
            return 0
        
        fim = self.estatisticas['tempo_fim'] or time.time()
        return fim - self.estatisticas['tempo_inicio']
    
    def incrementar(self, categoria: str, quantidade: int = 1) -> None:
        """
        Incrementa contador de uma categoria.
        
        Args:
            categoria: Nome da categoria estatística
            quantidade: Quantidade a incrementar
        """
        if categoria in self.estatisticas:
            self.estatisticas[categoria] += quantidade
        else:
            print(f"⚠️ Categoria desconhecida: {categoria}")
    
    def registrar_sucesso(self, arquivo: str, detalhes: Dict[str, Any] = None) -> None:
        """
        Registra sucesso no processamento de arquivo.
        
        Args:
            arquivo: Nome do arquivo processado
            detalhes: Detalhes opcionais do processamento
        """
        self.incrementar('sucessos')
        self.incrementar('arquivos_processados')
        
        self.arquivos_sucesso.append({
            'arquivo': arquivo,
            'timestamp': datetime.now(),
            'detalhes': detalhes or {}
        })
    
    def registrar_erro(self, arquivo: str, erro: str, detalhes: Dict[str, Any] = None) -> None:
        """
        Registra erro no processamento de arquivo.
        
        Args:
            arquivo: Nome do arquivo com erro
            erro: Descrição do erro
            detalhes: Detalhes opcionais do erro
        """
        self.incrementar('erros')
        self.incrementar('arquivos_processados')
        
        erro_info = {
            'arquivo': arquivo,
            'erro': erro,
            'timestamp': datetime.now(),
            'detalhes': detalhes or {}
        }
        
        self.detalhes_erros.append(erro_info)
        self.arquivos_erro.append(erro_info)
    
    def get_taxa_sucesso(self) -> float:
        """
        Calcula taxa de sucesso percentual.
        
        Returns:
            Taxa de sucesso (0-100)
        """
        total = self.estatisticas['arquivos_processados']
        if total == 0:
            return 0.0
        
        sucessos = self.estatisticas['sucessos']
        return (sucessos / total) * 100
    
    def get_throughput(self) -> float:
        """
        Calcula throughput (arquivos por minuto).
        
        Returns:
            Arquivos processados por minuto
        """
        tempo_total = self.get_tempo_decorrido()
        if tempo_total == 0:
            return 0.0
        
        total_arquivos = self.estatisticas['arquivos_processados']
        return (total_arquivos / tempo_total) * 60
    
    def imprimir_progresso(self, atual: int, total: int) -> None:
        """
        Imprime progresso atual do processamento.
        
        Args:
            atual: Arquivo atual sendo processado
            total: Total de arquivos
        """
        if atual % 10 == 0 or atual == total:  # A cada 10 arquivos ou no final
            tempo_decorrido = self.get_tempo_decorrido()
            progresso = (atual / total) * 100
            taxa_sucesso = self.get_taxa_sucesso()
            
            # Estimativa de tempo restante
            if atual > 0:
                tempo_por_arquivo = tempo_decorrido / atual
                tempo_restante = tempo_por_arquivo * (total - atual)
                tempo_restante_min = tempo_restante / 60
            else:
                tempo_restante_min = 0
            
            print(f"📊 Progresso: {progresso:.1f}% ({atual}/{total}) - "
                  f"Sucessos: {self.estatisticas['sucessos']} - "
                  f"Erros: {self.estatisticas['erros']} - "
                  f"Taxa: {taxa_sucesso:.1f}% - "
                  f"Restante: {tempo_restante_min:.1f}min")
    
    def imprimir_relatorio_resumido(self) -> None:
        """Imprime relatório resumido durante processamento."""
        total = self.estatisticas['arquivos_processados']
        if total > 0:
            print(f"\n📈 RELATÓRIO PARCIAL (Processados: {total})")
            print(f"✅ Sucessos: {self.estatisticas['sucessos']}")
            print(f"❌ Erros: {self.estatisticas['erros']}")
            print(f"📊 Taxa de sucesso: {self.get_taxa_sucesso():.1f}%")
            print(f"⚡ Throughput: {self.get_throughput():.1f} arquivos/min")
    
    def imprimir_relatorio_final(self, tempo_total: float = None) -> None:
        """
        Imprime relatório final completo.
        
        Args:
            tempo_total: Tempo total opcional (se não informado, calcula automaticamente)
        """
        if tempo_total is None:
            tempo_total = self.get_tempo_decorrido()
        
        total_arquivos = self.estatisticas['arquivos_processados']
        taxa_sucesso = self.get_taxa_sucesso()
        throughput = self.get_throughput()
        
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO FINAL DE PROCESSAMENTO")
        print("="*60)
        
        # Métricas temporais
        print(f"⏱️  TEMPO DE EXECUÇÃO:")
        print(f"   • Tempo total: {tempo_total/60:.2f} minutos ({tempo_total:.1f}s)")
        print(f"   • Início: {datetime.fromtimestamp(self.estatisticas['tempo_inicio']).strftime('%H:%M:%S') if self.estatisticas['tempo_inicio'] else 'N/A'}")
        print(f"   • Fim: {datetime.fromtimestamp(self.estatisticas['tempo_fim']).strftime('%H:%M:%S') if self.estatisticas['tempo_fim'] else datetime.now().strftime('%H:%M:%S')}")
        
        # Métricas de processamento
        print(f"\n📄 PROCESSAMENTO DE ARQUIVOS:")
        print(f"   • Total processado: {total_arquivos}")
        print(f"   • ✅ Sucessos: {self.estatisticas['sucessos']}")
        print(f"   • ❌ Erros: {self.estatisticas['erros']}")
        print(f"   • 📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        print(f"   • ⚡ Throughput: {throughput:.1f} arquivos/min")
        
        # Métricas de banco de dados
        print(f"\n🗄️  ESTATÍSTICAS DO BANCO:")
        print(f"   • 👥 Pessoas inseridas: {self.estatisticas['pessoas_inseridas']}")
        print(f"   • 📍 Endereços inseridos: {self.estatisticas['enderecos_inseridos']}")
        print(f"   • 🚛 Veículos inseridos: {self.estatisticas['veiculos_inseridos']}")
        print(f"   • 📋 Documentos inseridos: {self.estatisticas['documentos_inseridos']}")
        print(f"   • 🔄 Documentos duplicados: {self.estatisticas['documentos_duplicados']}")
        
        # Classificação de performance
        classificacao = self._classificar_performance(taxa_sucesso, throughput)
        print(f"\n🏆 CLASSIFICAÇÃO: {classificacao}")
        
        # Erros detalhados (se houver)
        if self.estatisticas['erros'] > 0:
            self._imprimir_detalhes_erros()
        
        print("="*60)
    
    def _classificar_performance(self, taxa_sucesso: float, throughput: float) -> str:
        """
        Classifica performance do processamento.
        
        Args:
            taxa_sucesso: Taxa de sucesso percentual
            throughput: Arquivos por minuto
            
        Returns:
            Classificação textual
        """
        if taxa_sucesso >= 95 and throughput >= 30:
            return "🔥 EXCELENTE - Sistema operando perfeitamente"
        elif taxa_sucesso >= 90 and throughput >= 20:
            return "✅ BOM - Performance satisfatória"
        elif taxa_sucesso >= 80 and throughput >= 10:
            return "⚠️ REGULAR - Pode ser melhorado"
        elif taxa_sucesso >= 60:
            return "🔧 CRÍTICO - Requer investigação"
        else:
            return "❌ FALHA - Sistema com problemas graves"
    
    def _imprimir_detalhes_erros(self) -> None:
        """Imprime detalhes dos erros encontrados."""
        print(f"\n❌ DETALHES DOS ERROS ({len(self.detalhes_erros)} erros):")
        print("-" * 60)
        
        # Agrupar erros por tipo
        tipos_erro = {}
        for erro_info in self.detalhes_erros:
            tipo = erro_info['erro']
            if tipo not in tipos_erro:
                tipos_erro[tipo] = []
            tipos_erro[tipo].append(erro_info['arquivo'])
        
        # Mostrar apenas os tipos mais comuns
        for i, (tipo, arquivos) in enumerate(tipos_erro.items(), 1):
            print(f"{i}. {tipo} ({len(arquivos)} ocorrências)")
            
            # Mostrar apenas alguns exemplos
            exemplos = arquivos[:3]
            for arquivo in exemplos:
                print(f"   📄 {arquivo}")
            
            if len(arquivos) > 3:
                print(f"   ... e mais {len(arquivos) - 3} arquivos")
            
            if i >= 5:  # Limitar a 5 tipos de erro
                break
    
    def exportar_relatorio(self, arquivo_saida: str) -> bool:
        """
        Exporta relatório completo para arquivo.
        
        Args:
            arquivo_saida: Caminho do arquivo de saída
            
        Returns:
            True se exportação foi bem-sucedida
        """
        try:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(f"# Relatório de Processamento CT-e\n")
                f.write(f"# Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                # Estatísticas básicas
                f.write(f"## Estatísticas Gerais\n")
                f.write(f"- Arquivos processados: {self.estatisticas['arquivos_processados']}\n")
                f.write(f"- Sucessos: {self.estatisticas['sucessos']}\n")
                f.write(f"- Erros: {self.estatisticas['erros']}\n")
                f.write(f"- Taxa de sucesso: {self.get_taxa_sucesso():.1f}%\n")
                f.write(f"- Throughput: {self.get_throughput():.1f} arquivos/min\n\n")
                
                # Lista de sucessos
                if self.arquivos_sucesso:
                    f.write(f"## Arquivos Processados com Sucesso ({len(self.arquivos_sucesso)})\n")
                    for item in self.arquivos_sucesso:
                        f.write(f"- {item['arquivo']}\n")
                    f.write("\n")
                
                # Lista de erros
                if self.arquivos_erro:
                    f.write(f"## Arquivos com Erro ({len(self.arquivos_erro)})\n")
                    for item in self.arquivos_erro:
                        f.write(f"- {item['arquivo']}: {item['erro']}\n")
            
            print(f"📄 Relatório exportado: {arquivo_saida}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar relatório: {e}")
            return False
    
    def reset(self) -> None:
        """Reseta todas as estatísticas."""
        self.__init__()