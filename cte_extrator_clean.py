# -*- coding: utf-8 -*-
"""
Extrator de dados de CT-e (Conhecimento de Transporte Eletrônico) - Versão Refatorada
Este módulo fornece classes e funções para extrair informações de arquivos XML de CT-e.
"""
import xml.etree.ElementTree as ET
import re
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CTEExtractionError(Exception):
    """Erro durante a extração de dados do CT-e."""
    pass


@dataclass
class Endereco:
    """Representação de um endereço."""
    xlgr: Optional[str] = None          # Logradouro
    nro: Optional[str] = None           # Número
    xbairro: Optional[str] = None       # Bairro
    xmun: Optional[str] = None          # Município
    uf: Optional[str] = None            # UF
    cep: Optional[str] = None           # CEP


@dataclass
class Documentos:
    """Documentos de identificação (CPF, CNPJ, IE)."""
    cpf: Optional[str] = None
    cnpj: Optional[str] = None 
    ie: Optional[str] = None


@dataclass
class Pessoa:
    """Representação de uma pessoa (remetente ou destinatário)."""
    nome: Optional[str] = None
    documentos: Optional[Documentos] = None
    endereco: Optional[Endereco] = None


@dataclass
class Localidade:
    """Representação de uma localidade (origem ou destino)."""
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cod_municipio: Optional[str] = None


@dataclass
class Carga:
    """Informações sobre a carga transportada."""
    vcarga: Optional[float] = None      # Valor da carga
    propred: Optional[str] = None       # Produto predominante
    qcarga: Optional[float] = None      # Quantidade da carga


@dataclass
class CTe:
    """Dados completos de um CT-e."""
    chave: Optional[str] = None
    numero: Optional[str] = None
    data_emissao: Optional[str] = None
    remetente: Optional[Pessoa] = None
    destinatario: Optional[Pessoa] = None
    valor_frete: Optional[str] = None
    placa: Optional[str] = None
    origem: Optional[Localidade] = None
    cfop: Optional[str] = None
    carga: Optional[Carga] = None


def flatten_cte_data(cte_obj: CTe) -> Dict[str, Any]:
    """
    Converte objeto CTe estruturado em dicionário achatado para exportação.
    
    Args:
        cte_obj: Objeto CTe com dados estruturados
        
    Returns:
        Dicionário com dados achatados no formato esperado
    """
    flattened = {}
    
    # Mapeamento de campos simples
    field_mapping = {
        'chave': 'CT-e_chave',
        'numero': 'CT-e_numero', 
        'data_emissao': 'Data_emissao',
        'valor_frete': 'Valor_frete',
        'placa': 'Placa',
        'cfop': 'CFOP'
    }
    
    # Processar campos simples
    cte_dict = asdict(cte_obj)
    for original_field, mapped_field in field_mapping.items():
        if original_field in cte_dict and cte_dict[original_field] is not None:
            flattened[mapped_field] = cte_dict[original_field]
    
    # Processar objetos complexos
    if cte_obj.remetente:
        flattened['Remetente'] = asdict(cte_obj.remetente)
    
    if cte_obj.destinatario:
        flattened['Destinatario'] = asdict(cte_obj.destinatario)
    
    if cte_obj.origem:
        flattened['Origem'] = asdict(cte_obj.origem)
    
    if cte_obj.carga:
        flattened['Carga'] = asdict(cte_obj.carga)
    
    return flattened


class CTEExtractor:
    """
    Extrator de dados de CT-e a partir de arquivos XML.
    
    Esta classe fornece métodos para extrair todas as informações relevantes
    de um arquivo XML de Conhecimento de Transporte Eletrônico (CT-e).
    """

    def __init__(self) -> None:
        """Inicializa o extrator com as configurações padrão."""
        self.namespaces = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        self.tree: Optional[ET.ElementTree] = None
        self.raiz: Optional[ET.Element] = None
        self.infCte: Optional[ET.Element] = None

    def _carregar_xml(self, caminho_arquivo: str) -> None:
        """
        Carrega e valida o arquivo XML.
        
        Args:
            caminho_arquivo: Caminho para o arquivo XML
            
        Raises:
            CTEExtractionError: Se houver erro no carregamento ou validação
        """
        try:
            self.tree = ET.parse(caminho_arquivo)
            self.raiz = self.tree.getroot()

            if self.raiz is None:
                raise CTEExtractionError(f"Erro ao parsear o arquivo XML: {caminho_arquivo}")
                
            self.infCte = self.raiz.find('.//cte:infCte', self.namespaces)
            if self.infCte is None:
                raise CTEExtractionError(f"Elemento 'infCte' não encontrado no arquivo: {caminho_arquivo}")

        except ET.ParseError as e:
            logger.error("Erro de parsing XML em %s: %s", caminho_arquivo, e)
            raise CTEExtractionError(f"Erro de parsing XML: {e}") from e
        except FileNotFoundError as e:
            logger.error("Arquivo não encontrado: %s", caminho_arquivo)
            raise CTEExtractionError(f"Arquivo não encontrado: {caminho_arquivo}") from e

    def _safe_find(self, path: str) -> Optional[str]:
        """
        Busca segura por elemento XML.
        
        Args:
            path: Caminho XPath para o elemento
            
        Returns:
            Texto do elemento ou None se não encontrado
        """
        if self.raiz is None:
            return None
        text = self.raiz.findtext(path, namespaces=self.namespaces)
        return text.strip() if text is not None else None

    def _get_text(self, node: Optional[ET.Element], tag: str) -> Optional[str]:
        """
        Extrai texto de um elemento XML específico.
        
        Args:
            node: Nó XML
            tag: Nome da tag a ser buscada
            
        Returns:
            Texto do elemento ou None se não encontrado
        """
        if node is None:
            return None
        text = node.findtext(f'cte:{tag}', namespaces=self.namespaces)
        return text.strip() if text else None

    def _extrair_documentos(self, node: Optional[ET.Element]) -> Documentos:
        """
        Extrai documentos (CPF, CNPJ, IE) de um nó XML.
        
        Args:
            node: Nó XML contendo os documentos
            
        Returns:
            Objeto Documentos preenchido
        """
        if node is None:
            return Documentos()
        
        cpf = node.findtext('cte:CPF', namespaces=self.namespaces)
        cnpj = node.findtext('cte:CNPJ', namespaces=self.namespaces)
        ie = node.findtext('cte:IE', namespaces=self.namespaces)
        
        return Documentos(
            cpf=cpf.strip() if cpf else None,
            cnpj=cnpj.strip() if cnpj else None,
            ie=ie.strip() if ie else None
        )

    def _extrair_endereco(self, node: Optional[ET.Element]) -> Endereco:
        """
        Extrai dados de endereço de um nó XML.
        
        Args:
            node: Nó XML contendo dados do endereço
            
        Returns:
            Objeto Endereco preenchido
        """
        if node is None:
            return Endereco()
        
        return Endereco(
            xlgr=self._get_text(node, 'xLgr'),
            nro=self._get_text(node, 'nro'),
            xbairro=self._get_text(node, 'xBairro'),
            xmun=self._get_text(node, 'xMun'),
            uf=self._get_text(node, 'UF'),
            cep=self._get_text(node, 'CEP')
        )

    def _extrair_pessoa(self, xpath: str) -> Optional[Pessoa]:
        """
        Extrai dados de uma pessoa (remetente ou destinatário).
        
        Args:
            xpath: Caminho XPath para o nó da pessoa
            
        Returns:
            Objeto Pessoa preenchido ou None se não encontrado
        """
        if self.infCte is None:
            return None
        
        pessoa_node = self.infCte.find(xpath, self.namespaces)
        if pessoa_node is None:
            return None
        
        # Determinar o tipo de endereço baseado no xpath
        endereco_tag = 'cte:enderReme' if 'rem' in xpath else 'cte:enderDest'
        endereco_node = pessoa_node.find(endereco_tag, self.namespaces)
        
        nome = pessoa_node.findtext('cte:xNome', namespaces=self.namespaces)

        return Pessoa(
            nome=nome.strip() if nome else None,
            documentos=self._extrair_documentos(pessoa_node),
            endereco=self._extrair_endereco(endereco_node)
        )

    def get_chave(self) -> Optional[str]:
        """Extrai a chave do CT-e."""
        return self._safe_find('.//cte:protCTe/cte:infProt/cte:chCTe')

    def get_numero(self) -> Optional[str]:
        """Extrai o número do CT-e."""
        return self._safe_find('.//cte:ide/cte:nCT')

    def get_data_emissao(self) -> Optional[str]:
        """Extrai a data de emissão no formato YYYY-MM-DD."""
        data = self._safe_find('.//cte:ide/cte:dhEmi')
        if data:
            return data.split('T')[0].replace('Z', '')
        return None

    def get_cfop(self) -> Optional[str]:
        """Extrai o CFOP."""
        return self._safe_find('.//cte:ide/cte:CFOP')

    def get_valor_frete(self) -> Optional[str]:
        """Extrai o valor do frete."""
        if self.infCte is None:
            return None
        text = self.infCte.findtext('.//cte:vTPrest', namespaces=self.namespaces)
        return text.strip() if text is not None else None

    def get_placa(self) -> str:
        """
        Extrai a placa do veículo do campo xObs.
        Suporta formatos: "PLACA NHL6G38", "PLACA: NHL6G38", ou "NHL6G38".
        
        Returns:
            Placa formatada (ex: NHL-6G38) ou "Placa não encontrada"
        """
        if self.infCte is None:
            return "Placa não encontrada"
        
        try:
            texto = self.infCte.findtext('.//cte:compl/cte:xObs', namespaces=self.namespaces)
            if not texto:
                return "Placa não encontrada"
                
            texto = texto.strip().upper()

            # Regex para padrões de placa (Mercosul e antigo)
            match = re.search(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', texto) or \
                    re.search(r'[A-Z]{3}-[0-9][A-Z0-9][0-9]{2}', texto)
            
            if match:
                placa = match.group(0).replace('-', '')
                return f'{placa[:3]}-{placa[3:]}'
            
            return "Placa não encontrada"

        except (AttributeError, TypeError) as e:
            logger.warning("Erro ao extrair placa: %s", e)
            return "Placa não encontrada"

    def get_remetente(self) -> Optional[Pessoa]:
        """Extrai dados do remetente."""
        return self._extrair_pessoa('.//cte:rem')

    def get_destinatario(self) -> Optional[Pessoa]:
        """Extrai dados do destinatário."""
        return self._extrair_pessoa('.//cte:dest')

    def get_origem(self) -> Optional[Localidade]:
        """Extrai dados da localidade de origem."""
        if self.infCte is None:
            return None
            
        cidade = self.infCte.findtext('.//cte:xMunIni', namespaces=self.namespaces)
        uf = self.infCte.findtext('.//cte:UFIni', namespaces=self.namespaces)
        cod_municipio = self.infCte.findtext('.//cte:cMunIni', namespaces=self.namespaces)

        return Localidade(
            cidade=cidade.strip() if cidade else None,
            uf=uf.strip() if uf else None,
            cod_municipio=cod_municipio.strip() if cod_municipio else None
        )

    def get_carga(self) -> Optional[Carga]:
        """Extrai informações da carga."""
        if self.infCte is None:
            return None
            
        infCarga = self.infCte.find('.//cte:infCarga', self.namespaces)
        if infCarga is None:
            return None
        
        infQ = infCarga.find('.//cte:infQ', self.namespaces)

        try:
            vcarga_text = self._get_text(infCarga, 'vCarga')
            vcarga = float(vcarga_text) if vcarga_text else None
            
            qcarga_text = self._get_text(infQ, 'qCarga')
            qcarga = float(qcarga_text) if qcarga_text else None
            
            return Carga(
                vcarga=vcarga,
                propred=self._get_text(infCarga, 'proPred'),
                qcarga=qcarga
            )

        except (ValueError, TypeError) as e:
            logger.warning("Erro ao converter valores numéricos da carga: %s", e)
            return None

    def extrair_dados(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """
        Método principal para extrair todos os dados do CT-e.
        
        Args:
            caminho_arquivo: Caminho para o arquivo XML do CT-e
            
        Returns:
            Dicionário com todos os dados extraídos do CT-e
            
        Raises:
            CTEExtractionError: Quando há problemas na extração dos dados
        """
        # Carregar e validar o XML
        self._carregar_xml(caminho_arquivo)
        
        logger.info("Extraindo dados do CT-e: %s", caminho_arquivo)

        # Criar objeto CTe com todos os dados extraídos
        cte = CTe(
            chave=self.get_chave(),
            numero=self.get_numero(),
            data_emissao=self.get_data_emissao(),
            cfop=self.get_cfop(),
            valor_frete=self.get_valor_frete(),
            remetente=self.get_remetente(),
            destinatario=self.get_destinatario(),
            placa=self.get_placa(),
            origem=self.get_origem(),
            carga=self.get_carga()
        )

        # Retornar dados achatados para compatibilidade
        return flatten_cte_data(cte)


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging detalhado para desenvolvimento
    logging.basicConfig(level=logging.DEBUG)
    
    extractor = CTEExtractor()
    
    # Arquivo de exemplo (ajuste o caminho conforme necessário)
    exemplo_xml = "/Users/sergiomendes/Documents/CT-e/mes_5_2025/CT-e/Autorizados/CTe21250535263415000132570010000011971277751110.xml"
    
    try:
        dados = extractor.extrair_dados(exemplo_xml)
        if dados:
            print("Extração realizada com sucesso!")
            print(f"Chave: {dados.get('CT-e_chave')}")
            print(f"Número: {dados.get('CT-e_numero')}")
            print(f"Remetente: {dados.get('Remetente', {}).get('nome')}")
        else:
            print("Nenhum dado foi extraído.")
    except CTEExtractionError as e:
        print(f"Erro na extração: {e}")
