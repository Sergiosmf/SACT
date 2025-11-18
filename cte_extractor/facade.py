# -*- coding: utf-8 -*-
"""
Módulo Facade - Interface simplificada para uso do CT-e Extractor
"""
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .factory import CTEExtractorFactory, ExtractorBuilder
from .exceptions import CTEExtractionError
from .utils import logger, PerformanceMonitor, config_manager


class CTEFacade:
    """
    Facade principal para o sistema CT-e Extractor.
    
    Fornece interface simplificada e unificada para todas as funcionalidades
    do sistema, ocultando a complexidade interna e aplicando o padrão Facade.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o facade com configuração opcional.
        
        Args:
            config: Configuração customizada do sistema
        """
        self._config = config or {}
        self._apply_global_config()
        
        # Estado interno
        self._last_extractor = None
        self._extraction_history = []
    
    def _apply_global_config(self):
        """Aplica configuração global ao sistema."""
        if self._config:
            for section, values in self._config.items():
                for key, value in values.items():
                    config_manager.set(section, key, value)
    
    # ========== MÉTODOS SIMPLES (API BÁSICA) ==========
    
    def extrair(self, arquivo: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de um CT-e de forma simples.
        
        Args:
            arquivo: Caminho para o arquivo XML do CT-e
            
        Returns:
            Dicionário com dados extraídos ou None se erro
            
        Example:
            >>> facade = CTEFacade()
            >>> dados = facade.extrair('cte.xml')
            >>> print(dados['CT-e_numero'])
        """
        try:
            arquivo_str = str(arquivo)
            
            with PerformanceMonitor("simple_extraction") as monitor:
                # Criar extrator automaticamente
                extrator = CTEExtractorFactory.create_from_xml(arquivo_str)
                self._last_extractor = extrator
                
                # Extrair dados
                with extrator:
                    dados = extrator.extrair_dados(arquivo_str)
                
                monitor.add_metric("file", arquivo_str)
                monitor.add_metric("success", dados is not None)
            
            # Registrar no histórico
            self._extraction_history.append({
                'arquivo': arquivo_str,
                'sucesso': dados is not None,
                'campos': len(dados) if dados else 0
            })
            
            return dados
            
        except Exception as e:
            logger.log_error("facade_simple_extraction_error", str(e), str(arquivo))
            return None
    
    def extrair_multiplos(self, arquivos: List[Union[str, Path]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Extrai dados de múltiplos CT-e.
        
        Args:
            arquivos: Lista de caminhos para arquivos XML
            
        Returns:
            Dicionário com nome do arquivo como chave e dados como valor
            
        Example:
            >>> facade = CTEFacade()
            >>> resultados = facade.extrair_multiplos(['cte1.xml', 'cte2.xml'])
        """
        resultados = {}
        
        with PerformanceMonitor("multiple_extraction") as monitor:
            sucessos = 0
            
            for arquivo in arquivos:
                arquivo_str = str(arquivo)
                try:
                    dados = self.extrair(arquivo_str)
                    resultados[arquivo_str] = dados
                    if dados:
                        sucessos += 1
                except Exception as e:
                    logger.log_error("facade_multiple_extraction_error", str(e), arquivo_str)
                    resultados[arquivo_str] = None
            
            monitor.add_metric("total_files", len(arquivos))
            monitor.add_metric("successful_extractions", sucessos)
            monitor.add_metric("success_rate", sucessos / len(arquivos) if arquivos else 0)
        
        return resultados
    
    def extrair_simples(self, arquivo: Union[str, Path]) -> Dict[str, str]:
        """
        Extrai apenas campos básicos de um CT-e.
        
        Args:
            arquivo: Caminho para o arquivo XML
            
        Returns:
            Dicionário com campos básicos simplificados
            
        Example:
            >>> facade = CTEFacade()
            >>> basico = facade.extrair_simples('cte.xml')
            >>> print(f"CT-e: {basico['numero']} - Valor: {basico['valor']}")
        """
        dados_completos = self.extrair(arquivo)
        if not dados_completos:
            return {}
        
        # Extrair apenas campos essenciais
        campos_basicos = {
            'chave': dados_completos.get('CT-e_chave', ''),
            'numero': dados_completos.get('CT-e_numero', ''),
            'serie': dados_completos.get('CT-e_serie', ''),
            'data': dados_completos.get('Data_emissao', ''),
            'valor': dados_completos.get('Valor_frete', ''),
            'placa': dados_completos.get('Placa', ''),
            'cfop': dados_completos.get('CFOP', ''),
            'remetente': '',
            'destinatario': ''
        }
        
        # Extrair nomes de pessoas
        remetente = dados_completos.get('Remetente', {})
        if isinstance(remetente, dict) and 'nome' in remetente:
            campos_basicos['remetente'] = remetente['nome']
        
        destinatario = dados_completos.get('Destinatario', {})
        if isinstance(destinatario, dict) and 'nome' in destinatario:
            campos_basicos['destinatario'] = destinatario['nome']
        
        return campos_basicos
    
    # ========== MÉTODOS AVANÇADOS (API CONFIGURÁVEL) ==========
    
    def extrair_com_config(
        self,
        arquivo: Union[str, Path],
        versao_schema: str = 'auto',
        validar: bool = True,
        usar_cache: bool = True,
        **opcoes
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai dados com configuração específica.
        
        Args:
            arquivo: Caminho para o arquivo XML
            versao_schema: Versão do schema ('v3', 'auto', etc.)
            validar: Se deve validar os dados
            usar_cache: Se deve usar cache
            **opcoes: Opções adicionais
            
        Returns:
            Dados extraídos com configurações específicas
        """
        try:
            arquivo_str = str(arquivo)
            
            # Criar extrator com configurações específicas
            extrator = CTEExtractorFactory.create_extractor(
                schema_version=versao_schema,
                validate_data=validar,
                cache_enabled=usar_cache,
                config=opcoes
            )
            
            # Extrair dados
            with extrator:
                dados = extrator.extrair_dados(arquivo_str)
            
            return dados
            
        except Exception as e:
            logger.log_error("facade_config_extraction_error", str(e), str(arquivo))
            return None
    
    def criar_extrator_customizado(self) -> ExtractorBuilder:
        """
        Retorna builder para criar extrator customizado.
        
        Returns:
            Builder para configuração fluente
            
        Example:
            >>> facade = CTEFacade()
            >>> extrator = (facade.criar_extrator_customizado()
            ...              .version('v3')
            ...              .validation(True)
            ...              .cache(True, 'lru', 200)
            ...              .build())
        """
        return ExtractorBuilder()
    
    # ========== MÉTODOS DE VALIDAÇÃO E ANÁLISE ==========
    
    def validar_arquivo(self, arquivo: Union[str, Path]) -> Dict[str, Any]:
        """
        Valida se um arquivo é um CT-e válido.
        
        Args:
            arquivo: Caminho para o arquivo XML
            
        Returns:
            Dicionário com resultado da validação
        """
        arquivo_path = Path(arquivo)
        resultado = {
            'arquivo': str(arquivo),
            'existe': arquivo_path.exists(),
            'eh_xml': False,
            'eh_cte': False,
            'versao_schema': None,
            'erros': []
        }
        
        if not resultado['existe']:
            resultado['erros'].append("Arquivo não encontrado")
            return resultado
        
        try:
            import xml.etree.ElementTree as ET
            
            # Tentar parsear XML
            tree = ET.parse(arquivo)
            resultado['eh_xml'] = True
            
            # Verificar se é CT-e
            root = tree.getroot()
            if 'cte' in root.tag.lower() or root.find('.//{http://www.portalfiscal.inf.br/cte}infCte') is not None:
                resultado['eh_cte'] = True
                
                # Detectar versão
                version = (root.get('versao') or 
                          root.findtext('.//{http://www.portalfiscal.inf.br/cte}versao') or
                          'desconhecida')
                resultado['versao_schema'] = version
            else:
                resultado['erros'].append("Arquivo não é um CT-e válido")
                
        except ET.ParseError as e:
            resultado['erros'].append(f"Erro de parsing XML: {e}")
        except Exception as e:
            resultado['erros'].append(f"Erro inesperado: {e}")
        
        return resultado
    
    def analisar_diretorio(self, diretorio: Union[str, Path]) -> Dict[str, Any]:
        """
        Analisa diretório em busca de arquivos CT-e.
        
        Args:
            diretorio: Caminho para o diretório
            
        Returns:
            Análise completa do diretório
        """
        dir_path = Path(diretorio)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return {'erro': 'Diretório não encontrado'}
        
        # Buscar arquivos XML
        arquivos_xml = list(dir_path.glob('*.xml'))
        
        analise = {
            'diretorio': str(diretorio),
            'total_arquivos_xml': len(arquivos_xml),
            'arquivos_cte': [],
            'arquivos_invalidos': [],
            'resumo_versoes': {},
            'total_cte_validos': 0
        }
        
        for arquivo in arquivos_xml:
            validacao = self.validar_arquivo(arquivo)
            
            if validacao['eh_cte']:
                analise['arquivos_cte'].append({
                    'arquivo': arquivo.name,
                    'versao': validacao['versao_schema']
                })
                analise['total_cte_validos'] += 1
                
                # Contar versões
                versao = validacao['versao_schema']
                analise['resumo_versoes'][versao] = analise['resumo_versoes'].get(versao, 0) + 1
            else:
                analise['arquivos_invalidos'].append({
                    'arquivo': arquivo.name,
                    'erros': validacao['erros']
                })
        
        return analise
    
    # ========== MÉTODOS DE INFORMAÇÃO E STATUS ==========
    
    def get_historico(self) -> List[Dict[str, Any]]:
        """Retorna histórico de extrações."""
        return self._extraction_history.copy()
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso."""
        if not self._extraction_history:
            return {'total_extracoes': 0}
        
        total = len(self._extraction_history)
        sucessos = sum(1 for h in self._extraction_history if h['sucesso'])
        
        return {
            'total_extracoes': total,
            'sucessos': sucessos,
            'falhas': total - sucessos,
            'taxa_sucesso': sucessos / total if total > 0 else 0,
            'media_campos_extraidos': sum(h['campos'] for h in self._extraction_history if h['sucesso']) / sucessos if sucessos > 0 else 0
        }
    
    def limpar_historico(self):
        """Limpa o histórico de extrações."""
        self._extraction_history.clear()
    
    def get_configuracao_atual(self) -> Dict[str, Any]:
        """Retorna configuração atual do sistema."""
        return {
            'config_global': config_manager.config,
            'versoes_suportadas': CTEExtractorFactory.get_supported_versions(),
            'ultimo_extrator': type(self._last_extractor).__name__ if self._last_extractor else None
        }


# ========== CONTEXT MANAGER PARA USO AVANÇADO ==========

@contextmanager
def cte_extractor_facade(config: Dict[str, Any] = None):
    """
    Context manager para uso avançado do Facade.
    
    Example:
        >>> with cte_extractor_facade({'validation': {'strict_mode': False}}) as facade:
        ...     dados = facade.extrair('cte.xml')
    """
    facade = CTEFacade(config)
    try:
        yield facade
    finally:
        # Limpeza se necessário
        pass


# ========== FUNÇÕES DE CONVENIÊNCIA ==========

def extrair_cte_simples(arquivo: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Função de conveniência para extração simples.
    
    Args:
        arquivo: Caminho para o arquivo CT-e
        
    Returns:
        Dados extraídos ou None
    """
    facade = CTEFacade()
    return facade.extrair(arquivo)


def validar_cte(arquivo: Union[str, Path]) -> bool:
    """
    Função de conveniência para validação rápida.
    
    Args:
        arquivo: Caminho para o arquivo
        
    Returns:
        True se é um CT-e válido
    """
    facade = CTEFacade()
    validacao = facade.validar_arquivo(arquivo)
    return validacao['eh_cte'] and not validacao['erros']


# Exemplo de uso
if __name__ == "__main__":
    # Demonstração do Facade
    facade = CTEFacade()
    
    # Uso simples
    # dados = facade.extrair('exemplo.xml')
    
    # Uso com configuração
    # dados = facade.extrair_com_config('exemplo.xml', versao_schema='v3', validar=True)
    
    # Builder pattern
    extrator_custom = (facade.criar_extrator_customizado()
                      .version('v3')
                      .validation(True)
                      .cache(True, 'lru', 100)
                      .build())
    
    print("✅ Facade testado com sucesso!")
    print(f"Configuração atual: {facade.get_configuracao_atual()}")
