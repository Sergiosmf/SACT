# -*- coding: utf-8 -*-
"""
Módulo de Exceções - Hierarquia de exceções específicas para CT-e
"""


class CTEExtractionError(Exception):
    """Erro base na extração de dados do CT-e."""
    
    def __init__(self, message: str, arquivo: str = None, codigo_erro: str = None):
        super().__init__(message)
        self.arquivo = arquivo
        self.codigo_erro = codigo_erro
    
    def __str__(self):
        msg = super().__str__()
        if self.arquivo:
            msg += f" (Arquivo: {self.arquivo})"
        if self.codigo_erro:
            msg += f" (Código: {self.codigo_erro})"
        return msg


class CTEValidationError(CTEExtractionError):
    """Erro de validação de dados do CT-e."""
    
    def __init__(self, message: str, campo: str = None, valor: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.campo = campo
        self.valor = valor


class CTEParsingError(CTEExtractionError):
    """Erro de parsing do XML do CT-e."""
    
    def __init__(self, message: str, linha: int = None, coluna: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.linha = linha
        self.coluna = coluna


class CTESchemaError(CTEExtractionError):
    """Erro de schema/estrutura do CT-e."""
    
    def __init__(self, message: str, elemento_esperado: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.elemento_esperado = elemento_esperado


class CTEConfigurationError(CTEExtractionError):
    """Erro de configuração do extrator."""
    pass


class CTECacheError(CTEExtractionError):
    """Erro relacionado ao sistema de cache."""
    pass


class CTENetworkError(CTEExtractionError):
    """Erro de rede (para futuras implementações com web services)."""
    pass
