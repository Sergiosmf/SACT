# -*- coding: utf-8 -*-
"""
Módulo de Modelos - Dataclasses para representação dos dados do CT-e
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional
from datetime import datetime

from .strategies import StrategyFactory


@dataclass
class Endereco:
    """Representação de um endereço com validação."""
    xlgr: Optional[str] = None          # Logradouro
    nro: Optional[str] = None           # Número
    xbairro: Optional[str] = None       # Bairro
    xmun: Optional[str] = None          # Município
    uf: Optional[str] = None            # UF
    cep: Optional[str] = None           # CEP
    
    def __post_init__(self):
        """Validação pós-inicialização usando Strategy."""
        if self.cep:
            # Usar estratégia de validação personalizada se necessário
            self._validar_cep()
    
    def _validar_cep(self) -> None:
        """Valida CEP usando regex."""
        import re
        if self.cep and not re.match(r'^\d{8}$', re.sub(r'[^0-9]', '', self.cep)):
            from .utils import logger
            logger.log_error("invalid_cep", f"CEP inválido: {self.cep}")
    
    @property
    def endereco_completo(self) -> str:
        """Retorna endereço formatado."""
        partes = [self.xlgr, self.nro, self.xbairro, self.xmun, self.uf]
        return ", ".join(filter(None, partes))
    
    @property
    def endereco_resumido(self) -> str:
        """Retorna endereço resumido (cidade - UF)."""
        if self.xmun and self.uf:
            return f"{self.xmun} - {self.uf}"
        return self.xmun or self.uf or "N/A"


@dataclass
class Documentos:
    """Documentos de identificação com validação usando Strategy."""
    cpf: Optional[str] = None
    cnpj: Optional[str] = None 
    ie: Optional[str] = None
    
    def __post_init__(self):
        """Validação pós-inicialização usando Strategy."""
        self._validar_documentos()
    
    def _validar_documentos(self) -> None:
        """Valida documentos usando estratégias específicas."""
        from .utils import logger
        
        if self.cpf:
            cpf_validator = StrategyFactory.create_validator('cpf')
            if not cpf_validator.validate(self.cpf):
                logger.log_error("invalid_cpf", f"CPF inválido: {self.cpf}")
        
        if self.cnpj:
            cnpj_validator = StrategyFactory.create_validator('cnpj')
            if not cnpj_validator.validate(self.cnpj):
                logger.log_error("invalid_cnpj", f"CNPJ inválido: {self.cnpj}")
    
    @property
    def documento_principal(self) -> Optional[str]:
        """Retorna o documento principal (CNPJ ou CPF)."""
        return self.cnpj or self.cpf
    
    @property
    def tipo_documento(self) -> str:
        """Retorna o tipo do documento principal."""
        if self.cnpj:
            return "CNPJ"
        elif self.cpf:
            return "CPF"
        return "N/A"


@dataclass
class Pessoa:
    """Representação de uma pessoa com dados completos e validação."""
    nome: Optional[str] = None
    documentos: Optional[Documentos] = None
    endereco: Optional[Endereco] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    
    def __post_init__(self):
        """Pós-processamento e validação."""
        if self.nome:
            self.nome = self.nome.strip()
        if self.email:
            self._validar_email()
    
    def _validar_email(self) -> None:
        """Valida formato do email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, self.email):
            from .utils import logger
            logger.log_error("invalid_email", f"Email inválido: {self.email}")
    
    @property
    def tipo_pessoa(self) -> str:
        """Identifica se é pessoa física ou jurídica."""
        if self.documentos:
            return "PJ" if self.documentos.cnpj else "PF" if self.documentos.cpf else "N/A"
        return "N/A"
    
    @property
    def identificacao(self) -> str:
        """Retorna identificação completa (nome + documento)."""
        nome = self.nome or "Nome não informado"
        documento = self.documentos.documento_principal if self.documentos else None
        if documento:
            return f"{nome} ({documento})"
        return nome


@dataclass
class Localidade:
    """Representação de uma localidade com dados geográficos."""
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cod_municipio: Optional[str] = None
    pais: Optional[str] = "Brasil"  # Padrão Brasil
    
    def __post_init__(self):
        """Pós-processamento dos dados."""
        if self.cidade:
            self.cidade = self.cidade.strip().title()
        if self.uf:
            self.uf = self.uf.strip().upper()
    
    @property
    def localidade_completa(self) -> str:
        """Retorna localidade formatada."""
        if self.cidade and self.uf:
            return f"{self.cidade} - {self.uf}"
        return self.cidade or self.uf or "N/A"
    
    @property
    def codigo_ibge(self) -> Optional[str]:
        """Retorna código IBGE do município."""
        return self.cod_municipio


@dataclass
class Veiculo:
    """Informações detalhadas do veículo com validação."""
    placa: Optional[str] = None
    renavam: Optional[str] = None
    proprietario: Optional[str] = None
    uf_licenciamento: Optional[str] = None
    
    def __post_init__(self):
        """Validação e formatação da placa."""
        if self.placa:
            self.placa = self.placa.strip().upper()
            self._validar_placa()
        if self.uf_licenciamento:
            self.uf_licenciamento = self.uf_licenciamento.strip().upper()
    
    def _validar_placa(self) -> None:
        """Valida placa usando Strategy."""
        if self.placa == "Placa não encontrada":
            return  # Não validar placas não encontradas
            
        placa_validator = StrategyFactory.create_validator('placa')
        if not placa_validator.validate(self.placa):
            from .utils import logger
            logger.log_error("invalid_placa", f"Placa inválida: {self.placa}")
    
    @property
    def placa_formatada(self) -> Optional[str]:
        """Retorna placa formatada com hífen."""
        if not self.placa:
            return None
        
        placa_limpa = self.placa.replace('-', '').replace(' ', '')
        if len(placa_limpa) == 7:
            return f"{placa_limpa[:3]}-{placa_limpa[3:]}"
        return self.placa
    
    @property
    def identificacao_veiculo(self) -> str:
        """Retorna identificação do veículo."""
        placa = self.placa_formatada or "Placa não informada"
        if self.proprietario:
            return f"{placa} ({self.proprietario})"
        return placa


@dataclass
class Carga:
    """Informações sobre a carga transportada com validação robusta."""
    vcarga: Optional[Decimal] = None    # Valor da carga
    propred: Optional[str] = None       # Produto predominante  
    qcarga: Optional[Decimal] = None    # Quantidade da carga
    unidade: Optional[str] = None       # Unidade de medida
    
    def __post_init__(self):
        """Conversão e validação de valores usando Decimal."""
        self._converter_valores()
        if self.propred:
            self.propred = self.propred.strip().title()
    
    def _converter_valores(self) -> None:
        """Converte valores para Decimal com tratamento de erro."""
        try:
            if isinstance(self.vcarga, (int, float, str)):
                self.vcarga = Decimal(str(self.vcarga)) if str(self.vcarga).strip() else None
        except (InvalidOperation, ValueError):
            self.vcarga = None
        
        try:
            if isinstance(self.qcarga, (int, float, str)):
                self.qcarga = Decimal(str(self.qcarga)) if str(self.qcarga).strip() else None
        except (InvalidOperation, ValueError):
            self.qcarga = None
    
    @property
    def valor_formatado(self) -> str:
        """Retorna valor da carga formatado como moeda."""
        if self.vcarga:
            return f"R$ {self.vcarga:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "Valor não informado"
    
    @property
    def quantidade_formatada(self) -> str:
        """Retorna quantidade formatada com unidade."""
        if self.qcarga and self.unidade:
            return f"{self.qcarga} {self.unidade}"
        elif self.qcarga:
            return str(self.qcarga)
        return "Quantidade não informada"


@dataclass
class CTe:
    """
    Dados completos e aprimorados de um CT-e com validação e propriedades computadas.
    
    Esta classe representa o modelo principal do CT-e, agregando todas as informações
    extraídas do documento fiscal eletrônico.
    """
    # Dados básicos
    chave: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    data_emissao: Optional[str] = None
    data_vencimento: Optional[str] = None
    
    # Pessoas envolvidas
    remetente: Optional[Pessoa] = None
    destinatario: Optional[Pessoa] = None
    expedidor: Optional[Pessoa] = None
    recebedor: Optional[Pessoa] = None
    tomador: Optional[Pessoa] = None
    
    # Valores financeiros
    valor_frete: Optional[Decimal] = None
    valor_receber: Optional[Decimal] = None
    
    # Transporte
    veiculo: Optional[Veiculo] = None
    
    # Localidades
    origem: Optional[Localidade] = None
    destino: Optional[Localidade] = None
    
    # Outros dados
    cfop: Optional[str] = None
    carga: Optional[Carga] = None
    
    # Metadados
    observacoes: Optional[str] = None
    status: Optional[str] = None
    versao_schema: Optional[str] = None
    
    def __post_init__(self):
        """Validação e conversão de dados pós-inicialização."""
        self._converter_valores_monetarios()
        self._validar_datas()
        self._processar_chave()
    
    def _converter_valores_monetarios(self) -> None:
        """Converte valores monetários para Decimal com precisão."""
        for campo in ['valor_frete', 'valor_receber']:
            valor = getattr(self, campo)
            if isinstance(valor, (int, float, str)) and str(valor).strip():
                try:
                    setattr(self, campo, Decimal(str(valor)))
                except (InvalidOperation, ValueError):
                    setattr(self, campo, None)
    
    def _validar_datas(self) -> None:
        """Valida datas usando Strategy."""
        if self.data_emissao:
            date_validator = StrategyFactory.create_validator('date')
            if not date_validator.validate(self.data_emissao):
                from .utils import logger
                logger.log_error("invalid_emission_date", f"Data de emissão inválida: {self.data_emissao}")
    
    def _processar_chave(self) -> None:
        """Processa e valida a chave do CT-e."""
        if self.chave:
            # Remove prefixos como "CTe" se existir
            import re
            self.chave = re.sub(r'^CTe', '', self.chave).strip()
    
    # Propriedades computadas
    @property
    def valor_total_formatado(self) -> str:
        """Retorna valor total formatado como moeda."""
        valor = self.valor_frete or self.valor_receber
        if valor:
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "Valor não informado"
    
    @property
    def rota_completa(self) -> str:
        """Retorna rota completa (origem → destino)."""
        origem_str = self.origem.localidade_completa if self.origem else "Origem não informada"
        destino_str = self.destino.localidade_completa if self.destino else "Destino não informado"
        return f"{origem_str} → {destino_str}"
    
    @property
    def identificacao_cte(self) -> str:
        """Retorna identificação única do CT-e."""
        numero = self.numero or "N/A"
        serie = self.serie or "N/A"
        return f"CT-e {numero}/{serie}"
    
    @property
    def resumo_transporte(self) -> str:
        """Retorna resumo do transporte."""
        partes = []
        
        if self.remetente and self.remetente.nome:
            partes.append(f"Remetente: {self.remetente.nome}")
        
        if self.destinatario and self.destinatario.nome:
            partes.append(f"Destinatário: {self.destinatario.nome}")
        
        if self.veiculo and self.veiculo.placa:
            partes.append(f"Veículo: {self.veiculo.placa_formatada}")
        
        return " | ".join(partes) if partes else "Informações não disponíveis"
    
    def to_dict_simples(self) -> dict:
        """Converte para dicionário simples (apenas valores básicos)."""
        return {
            'chave': self.chave,
            'numero': self.numero,
            'serie': self.serie,
            'data_emissao': self.data_emissao,
            'valor_frete': str(self.valor_frete) if self.valor_frete else None,
            'cfop': self.cfop,
            'rota': self.rota_completa,
            'identificacao': self.identificacao_cte
        }
