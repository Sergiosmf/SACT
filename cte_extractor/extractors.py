# -*- coding: utf-8 -*-
"""
Módulo de Extratores - Implementações concretas dos extratores de CT-e
"""
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

from .base import BaseExtractor
from .exceptions import CTEParsingError, CTESchemaError, CTEExtractionError
from .models import CTe, Pessoa, Endereco, Documentos, Localidade, Veiculo, Carga
from .strategies import StrategyFactory
from .utils import logger, PerformanceMonitor, XMLHelper, DataConverter


class CTEExtractorV3(BaseExtractor):
    """
    Extrator específico para CT-e versão 3.x
    
    Implementa extração otimizada para documentos CT-e versão 3.x,
    com foco em performance e compatibilidade.
    """
    
    def _setup_extractor(self) -> None:
        """Configuração específica para versão 3.x."""
        self.namespaces = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        self.version = "3.x"
        
        # Configurar estratégias
        self.cache_strategy = StrategyFactory.create_cache(
            'lru' if self._cache_enabled else 'none',
            max_size=50
        )
        
        self.extraction_strategy = StrategyFactory.create_extraction_strategy(
            'standard',
            namespaces=self.namespaces
        )
        
        # Estado interno
        self.tree: Optional[ET.ElementTree] = None
        self.raiz: Optional[ET.Element] = None
        self.infCte: Optional[ET.Element] = None
        self.protCte: Optional[ET.Element] = None
    
    def _carregar_xml(self, caminho_arquivo: str) -> None:
        """Carrega XML específico para versão 3.x."""
        try:
            arquivo_path = Path(caminho_arquivo)
            if not arquivo_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
            
            self.tree = ET.parse(caminho_arquivo)
            self.raiz = self.tree.getroot()
            
            if self.raiz is None:
                raise CTEParsingError(f"Erro ao parsear XML: {caminho_arquivo}")
            
            # Localizar elementos específicos da v3.x
            self.infCte = self.raiz.find('.//cte:infCte', self.namespaces)
            self.protCte = self.raiz.find('.//cte:protCTe', self.namespaces)
            
            if self.infCte is None:
                raise CTESchemaError(
                    f"Elemento 'infCte' não encontrado",
                    elemento_esperado="infCte",
                    arquivo=caminho_arquivo
                )
                
        except ET.ParseError as e:
            raise CTEParsingError(f"Erro de parsing XML: {e}", arquivo=caminho_arquivo) from e
        except FileNotFoundError as e:
            raise CTEParsingError(f"Arquivo não encontrado: {caminho_arquivo}") from e
    
    def _extrair_dados_principais(self) -> Dict[str, Any]:
        """Extrai dados principais usando estratégias otimizadas."""
        with PerformanceMonitor("extract_main_data") as monitor:
            
            # Criar objeto CTe
            cte = CTe(
                chave=self._extrair_chave(),
                numero=self._safe_find('.//cte:ide/cte:nCT'),
                serie=self._safe_find('.//cte:ide/cte:serie'),
                data_emissao=self._safe_find('.//cte:ide/cte:dhEmi'),
                
                # Pessoas
                remetente=self._extrair_pessoa('.//cte:rem'),
                destinatario=self._extrair_pessoa('.//cte:dest'),
                expedidor=self._extrair_pessoa('.//cte:exped'),
                recebedor=self._extrair_pessoa('.//cte:receb'),
                
                # Valores
                valor_frete=self._safe_find('.//cte:vTPrest'),
                
                # Transporte
                veiculo=self._extrair_veiculo(),
                
                # Localidades
                origem=self._extrair_localidade("origem"),
                destino=self._extrair_localidade("destino"),
                
                # Outros
                cfop=self._safe_find('.//cte:ide/cte:CFOP'),
                carga=self._extrair_carga(),
                observacoes=self._safe_find('.//cte:compl/cte:xObs'),
                versao_schema=self.version
            )
            
            # Converter para dicionário achatado
            dados_achatados = self._flatten_cte_data(cte)
            
            monitor.add_metric("fields_extracted", len(dados_achatados))
            monitor.add_metric("extractor_version", self.version)
            
            return dados_achatados
    
    def _extrair_chave(self) -> Optional[str]:
        """Extrai chave com múltiplas fontes específicas da v3.x."""
        caminhos = [
            './/cte:protCTe/cte:infProt/cte:chCTe',
            './/cte:infCte/@Id',
            './/cte:chCTe'
        ]
        
        for caminho in caminhos:
            chave = self._safe_find(caminho)
            if chave:
                # Limpar prefixos específicos da v3.x
                chave = re.sub(r'^CTe', '', chave)
                return chave
        return None
    
    def _extrair_pessoa(self, xpath: str) -> Optional[Pessoa]:
        """Extrai pessoa com validação específica da v3.x."""
        if self.infCte is None:
            return None
        
        pessoa_node = self.infCte.find(xpath, self.namespaces)
        if pessoa_node is None:
            return None
        
        # Mapeamento de endereços específicos da v3.x
        endereco_tags = {
            'rem': 'cte:enderReme',
            'dest': 'cte:enderDest',
            'exped': 'cte:enderExped',
            'receb': 'cte:enderReceb'
        }
        
        endereco_tag = next(
            (tag for key, tag in endereco_tags.items() if key in xpath),
            'cte:endereco'
        )
        endereco_node = pessoa_node.find(endereco_tag, self.namespaces)
        
        nome = XMLHelper.safe_findtext(pessoa_node, 'cte:xNome', self.namespaces)
        telefone = XMLHelper.get_element_text(pessoa_node, 'fone', self.namespaces)
        email = XMLHelper.get_element_text(pessoa_node, 'email', self.namespaces)
        
        return Pessoa(
            nome=DataConverter.clean_string(nome),
            documentos=self._extrair_documentos(pessoa_node),
            endereco=self._extrair_endereco(endereco_node),
            telefone=DataConverter.clean_string(telefone),
            email=DataConverter.clean_string(email)
        )
    
    def _extrair_documentos(self, node: Optional[ET.Element]) -> Documentos:
        """Extrai documentos com normalização."""
        if node is None:
            return Documentos()
        
        cpf = XMLHelper.get_element_text(node, 'CPF', self.namespaces)
        cnpj = XMLHelper.get_element_text(node, 'CNPJ', self.namespaces)
        ie = XMLHelper.get_element_text(node, 'IE', self.namespaces)
        
        return Documentos(
            cpf=DataConverter.normalize_document(cpf) if cpf else None,
            cnpj=DataConverter.normalize_document(cnpj) if cnpj else None,
            ie=DataConverter.clean_string(ie)
        )
    
    def _extrair_endereco(self, node: Optional[ET.Element]) -> Endereco:
        """Extrai endereço com campos específicos da v3.x."""
        if node is None:
            return Endereco()
        
        return Endereco(
            xlgr=XMLHelper.get_element_text(node, 'xLgr', self.namespaces),
            nro=XMLHelper.get_element_text(node, 'nro', self.namespaces),
            xbairro=XMLHelper.get_element_text(node, 'xBairro', self.namespaces),
            xmun=XMLHelper.get_element_text(node, 'xMun', self.namespaces),
            uf=XMLHelper.get_element_text(node, 'UF', self.namespaces),
            cep=DataConverter.normalize_document(
                XMLHelper.get_element_text(node, 'CEP', self.namespaces)
            )
        )
    
    def _extrair_veiculo(self) -> Optional[Veiculo]:
        """Extrai veículo com estratégia multi-fonte."""
        if self.infCte is None:
            return None
        
        # Estratégia 1: Placa de múltiplas fontes
        placa = self._extrair_placa_multiplas_fontes()
        
        # Estratégia 2: Dados do veículo
        veiculo_node = self.infCte.find('.//cte:veicTransp', self.namespaces)
        
        renavam = proprietario = uf_licenciamento = None
        if veiculo_node is not None:
            renavam = XMLHelper.get_element_text(veiculo_node, 'RENAVAM', self.namespaces)
            proprietario = XMLHelper.get_element_text(veiculo_node, 'xNome', self.namespaces)
            uf_licenciamento = XMLHelper.get_element_text(veiculo_node, 'UF', self.namespaces)
        
        if any([placa, renavam, proprietario]):
            return Veiculo(
                placa=placa,
                renavam=renavam,
                proprietario=proprietario,
                uf_licenciamento=uf_licenciamento
            )
        return None
    
    def _extrair_placa_multiplas_fontes(self) -> Optional[str]:
        """Extrai placa usando estratégia regex multi-fonte."""
        if self.infCte is None:
            return None
        
        # Estratégia de extração por regex
        regex_strategy = StrategyFactory.create_extraction_strategy(
            'regex',
            pattern=r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}'
        )
        
        # Fonte 1: Campo xObs
        try:
            texto = XMLHelper.safe_findtext(
                self.infCte, './/cte:compl/cte:xObs', self.namespaces
            )
            if texto:
                placa = regex_strategy.extract_element(texto.upper())
                if placa and len(placa) == 7:
                    return f'{placa[:3]}-{placa[3:]}'
        except:
            pass
        
        # Fonte 2: Campo veicTransp/placa
        try:
            placa = XMLHelper.safe_findtext(
                self.infCte, './/cte:veicTransp/cte:placa', self.namespaces
            )
            if placa:
                placa = placa.strip().upper()
                placa_validator = StrategyFactory.create_validator('placa')
                if placa_validator.validate(placa):
                    return placa
                # Tentar formatar
                if len(placa) == 7:
                    return f'{placa[:3]}-{placa[3:]}'
        except:
            pass
        
        return "Placa não encontrada"
    
    def _extrair_localidade(self, tipo: str) -> Optional[Localidade]:
        """Extrai localidade de origem ou destino."""
        if self.infCte is None:
            return None
        
        if tipo == "origem":
            cidade = XMLHelper.safe_findtext(self.infCte, './/cte:xMunIni', self.namespaces)
            uf = XMLHelper.safe_findtext(self.infCte, './/cte:UFIni', self.namespaces)
            cod_municipio = XMLHelper.safe_findtext(self.infCte, './/cte:cMunIni', self.namespaces)
        elif tipo == "destino":
            cidade = XMLHelper.safe_findtext(self.infCte, './/cte:xMunFim', self.namespaces)
            uf = XMLHelper.safe_findtext(self.infCte, './/cte:UFFim', self.namespaces)
            cod_municipio = XMLHelper.safe_findtext(self.infCte, './/cte:cMunFim', self.namespaces)
        else:
            return None
        
        if any([cidade, uf, cod_municipio]):
            return Localidade(
                cidade=DataConverter.clean_string(cidade),
                uf=DataConverter.clean_string(uf),
                cod_municipio=DataConverter.clean_string(cod_municipio)
            )
        return None
    
    def _extrair_carga(self) -> Optional[Carga]:
        """Extrai carga com conversão robusta."""
        if self.infCte is None:
            return None
        
        infCarga = self.infCte.find('.//cte:infCarga', self.namespaces)
        if infCarga is None:
            return None
        
        infQ = infCarga.find('.//cte:infQ', self.namespaces)
        
        try:
            vcarga_text = XMLHelper.get_element_text(infCarga, 'vCarga', self.namespaces)
            vcarga = DataConverter.to_decimal(vcarga_text)
            
            qcarga_text = XMLHelper.get_element_text(infQ, 'qCarga', self.namespaces) if infQ else None
            qcarga = DataConverter.to_decimal(qcarga_text)
            
            propred = XMLHelper.get_element_text(infCarga, 'proPred', self.namespaces)
            unidade = XMLHelper.get_element_text(infQ, 'cUnid', self.namespaces) if infQ else None
            
            return Carga(
                vcarga=vcarga,
                propred=DataConverter.clean_string(propred),
                qcarga=qcarga,
                unidade=DataConverter.clean_string(unidade)
            )
            
        except Exception as e:
            logger.log_error("carga_extraction_error", str(e))
            return None
    
    def _safe_find(self, path: str) -> Optional[str]:
        """Busca segura com cache específico da v3.x."""
        if self._cache_enabled:
            cached = self.cache_strategy.get(path)
            if cached is not None:
                return cached
        
        if self.raiz is None:
            return None
        
        result = XMLHelper.safe_findtext(self.raiz, path, self.namespaces)
        
        if self._cache_enabled:
            self.cache_strategy.set(path, result)
        
        return result
    
    def _flatten_cte_data(self, cte_obj: CTe) -> Dict[str, Any]:
        """Converte CTe em dicionário achatado otimizado."""
        from dataclasses import asdict
        
        flattened = {}
        
        # Campos simples com mapeamento
        field_mapping = {
            'chave': 'CT-e_chave',
            'numero': 'CT-e_numero',
            'serie': 'CT-e_serie',
            'data_emissao': 'Data_emissao',
            'valor_frete': 'Valor_frete',
            'cfop': 'CFOP',
            'observacoes': 'Observacoes',
            'versao_schema': 'Versao_Schema'
        }
        
        cte_dict = asdict(cte_obj)
        for original_field, mapped_field in field_mapping.items():
            value = cte_dict.get(original_field)
            if value is not None:
                if isinstance(value, Decimal):
                    value = str(value)
                flattened[mapped_field] = value
        
        # Veículo
        if cte_obj.veiculo:
            veiculo_dict = asdict(cte_obj.veiculo)
            flattened['Veiculo'] = veiculo_dict
            flattened['Placa'] = veiculo_dict.get('placa', 'Placa não encontrada')
        else:
            flattened['Placa'] = 'Placa não encontrada'
        
        # Pessoas
        pessoas_mapping = {
            'remetente': 'Remetente',
            'destinatario': 'Destinatario',
            'expedidor': 'Expedidor',
            'recebedor': 'Recebedor'
        }
        
        for attr_name, key_name in pessoas_mapping.items():
            pessoa = getattr(cte_obj, attr_name)
            if pessoa:
                pessoa_dict = asdict(pessoa)
                flattened[key_name] = self._convert_decimals_in_dict(pessoa_dict)
        
        # Localidades
        if cte_obj.origem:
            flattened['Origem'] = asdict(cte_obj.origem)
        if cte_obj.destino:
            flattened['Destino'] = asdict(cte_obj.destino)
        
        # Carga
        if cte_obj.carga:
            carga_dict = asdict(cte_obj.carga)
            flattened['Carga'] = self._convert_decimals_in_dict(carga_dict)
        
        return flattened
    
    def _convert_decimals_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte Decimals recursivamente."""
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, dict):
                data[key] = self._convert_decimals_in_dict(value)
        return data
    
    def _validar_dados(self, dados: Dict[str, Any]) -> bool:
        """Valida dados extraídos usando Strategy."""
        if not self._validate_data:
            return True
        
        validator = StrategyFactory.create_validator('strict')
        return validator.validate(dados)
    
    def _handle_error(self, error: Exception, arquivo: str) -> None:
        """Trata erros com logging estruturado."""
        logger.log_error(
            "extraction_error",
            str(error),
            arquivo,
            extractor_version=self.version,
            error_type=type(error).__name__
        )
    
    def _limpar_recursos(self) -> None:
        """Limpa recursos específicos da v3.x."""
        self.tree = None
        self.raiz = None
        self.infCte = None
        self.protCte = None
        if self.cache_strategy:
            self.cache_strategy.clear()


# Alias para compatibilidade com código anterior
CTEExtractorAprimorado = CTEExtractorV3
