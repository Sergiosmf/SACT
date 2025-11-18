# -*- coding: utf-8 -*-
"""
Quilometragem Service - Serviço para cálculos de quilometragem
"""

from typing import Dict, Any


class QuilometragemService:
    """
    Serviço responsável pelos cálculos de quilometragem.
    Implementa lógica de negócio específica para cálculos de transporte.
    """
    
    def __init__(self):
        """Inicializa o serviço de quilometragem."""
        self.custo_padrao_por_km = 2.50  # R$ por km padrão
    
    def configurar_custo_por_km(self) -> float:
        """
        Configura o custo por quilômetro para cálculos.
        
        Returns:
            Custo por quilômetro configurado
        """
        print("\n" + "=" * 60)
        print("CONFIGURAÇÃO DE QUILOMETRAGEM")
        print("=" * 60)
        print("💰 Esta configuração será usada para calcular a quilometragem")
        print("   dos transportes baseada no valor do frete.")
        print(f"\n💡 Fórmula: Quilometragem = Valor do Frete ÷ Custo por KM")
        print(f"📊 Valor padrão sugerido: R$ {self.custo_padrao_por_km:.2f} por km")
        
        while True:
            try:
                entrada = input(f"\n💰 Digite o custo por km (ou Enter para usar R$ {self.custo_padrao_por_km:.2f}): ")
                
                if not entrada.strip():
                    # Usar valor padrão
                    custo_por_km = self.custo_padrao_por_km
                    print(f"✅ Usando valor padrão: R$ {custo_por_km:.2f} por km")
                    break
                
                # Tentar converter entrada
                custo_por_km = float(entrada.replace(',', '.').strip())
                
                if custo_por_km <= 0:
                    print("❌ O custo por km deve ser maior que zero!")
                    continue
                
                if custo_por_km > 50:
                    confirmacao = input(f"⚠️  Custo muito alto (R$ {custo_por_km:.2f}). Confirmar? (s/n): ")
                    if not confirmacao.lower().startswith('s'):
                        continue
                
                print(f"✅ Custo configurado: R$ {custo_por_km:.2f} por km")
                break
                
            except ValueError:
                print("❌ Valor inválido! Digite um número válido (ex: 2.50)")
            except KeyboardInterrupt:
                print("\n⚠️  Operação cancelada")
                return self.custo_padrao_por_km
        
        return custo_por_km
    
    def calcular_quilometragem(self, valor_frete: float, custo_por_km: float) -> float:
        """
        Calcula quilometragem baseada no valor do frete.
        
        Args:
            valor_frete: Valor do frete em reais
            custo_por_km: Custo por quilômetro
            
        Returns:
            Quilometragem calculada (arredondada para 2 decimais)
        """
        if custo_por_km <= 0:
            return 0.0
        
        if valor_frete <= 0:
            return 0.0
        
        quilometragem = valor_frete / custo_por_km
        return round(quilometragem, 2)
    
    def validar_quilometragem(self, quilometragem: float) -> Dict[str, Any]:
        """
        Valida se quilometragem calculada está dentro de parâmetros razoáveis.
        
        Args:
            quilometragem: Quilometragem a validar
            
        Returns:
            Dicionário com resultado da validação
        """
        resultado = {
            'valida': True,
            'warnings': [],
            'categoria': 'NORMAL'
        }
        
        if quilometragem <= 0:
            resultado['valida'] = False
            resultado['warnings'].append("Quilometragem deve ser maior que zero")
            resultado['categoria'] = 'INVÁLIDA'
            return resultado
        
        # Verificar faixas de distância
        if quilometragem < 10:
            resultado['warnings'].append("Distância muito curta (< 10 km)")
            resultado['categoria'] = 'CURTA'
        elif quilometragem > 5000:
            resultado['warnings'].append("Distância muito longa (> 5000 km)")
            resultado['categoria'] = 'LONGA'
        elif quilometragem > 2000:
            resultado['warnings'].append("Distância longa (> 2000 km)")
            resultado['categoria'] = 'LONGA'
        elif quilometragem < 50:
            resultado['categoria'] = 'CURTA'
        
        return resultado
    
    def calcular_estatisticas_quilometragem(self, dados_ctes: list) -> Dict[str, Any]:
        """
        Calcula estatísticas de quilometragem para um lote de CT-es.
        
        Args:
            dados_ctes: Lista de dados de CT-e
            
        Returns:
            Estatísticas de quilometragem
        """
        if not dados_ctes:
            return {}
        
        quilometragens = []
        valores_frete = []
        
        for cte in dados_ctes:
            km = cte.get('quilometragem', 0)
            valor = cte.get('valor_frete', 0)
            
            if km > 0:
                quilometragens.append(km)
            if valor > 0:
                valores_frete.append(valor)
        
        if not quilometragens:
            return {'erro': 'Nenhuma quilometragem válida encontrada'}
        
        estatisticas = {
            'total_ctes': len(dados_ctes),
            'ctes_com_quilometragem': len(quilometragens),
            'quilometragem_total': sum(quilometragens),
            'quilometragem_media': sum(quilometragens) / len(quilometragens),
            'quilometragem_min': min(quilometragens),
            'quilometragem_max': max(quilometragens),
            'valor_frete_total': sum(valores_frete),
            'valor_frete_medio': sum(valores_frete) / len(valores_frete) if valores_frete else 0
        }
        
        # Calcular custo médio por km
        if estatisticas['quilometragem_total'] > 0 and estatisticas['valor_frete_total'] > 0:
            estatisticas['custo_medio_por_km'] = estatisticas['valor_frete_total'] / estatisticas['quilometragem_total']
        else:
            estatisticas['custo_medio_por_km'] = 0
        
        return estatisticas
    
    def formatar_quilometragem(self, quilometragem: float) -> str:
        """
        Formata quilometragem para exibição.
        
        Args:
            quilometragem: Valor da quilometragem
            
        Returns:
            String formatada
        """
        if quilometragem == 0:
            return "0 km"
        
        if quilometragem < 1:
            metros = quilometragem * 1000
            return f"{metros:.0f}m"
        
        return f"{quilometragem:.2f} km"
    
    def classificar_distancia(self, quilometragem: float) -> str:
        """
        Classifica distância por categoria.
        
        Args:
            quilometragem: Quilometragem a classificar
            
        Returns:
            Classificação da distância
        """
        if quilometragem <= 0:
            return "❌ INVÁLIDA"
        elif quilometragem < 50:
            return "🏘️ URBANA"
        elif quilometragem < 200:
            return "🏞️ REGIONAL"
        elif quilometragem < 800:
            return "🛣️ ESTADUAL"
        elif quilometragem < 2000:
            return "🗺️ INTERESTADUAL"
        else:
            return "🌍 LONGA DISTÂNCIA"