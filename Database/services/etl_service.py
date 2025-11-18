# -*- coding: utf-8 -*-
"""
ETL Service - Serviço principal de ETL (Extract, Transform, Load)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Adicionar path para cte_extractor
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from cte_extractor.facade import CTEFacade
except ImportError:
    print("❌ Erro: módulo cte_extractor não encontrado")
    sys.exit(1)


class ETLService:
    """
    Serviço principal de ETL para processamento de CT-e.
    Orquestra extração, transformação e carregamento de dados.
    """
    
    def __init__(self, db_manager, stats_manager):
        """
        Inicializa o serviço ETL.
        
        Args:
            db_manager: Manager de banco de dados
            stats_manager: Manager de estatísticas
        """
        self.db_manager = db_manager
        self.stats_manager = stats_manager
        self.cte_facade = CTEFacade()
        
        # Repositórios (serão criados depois)
        self._pessoa_repo = None
        self._veiculo_repo = None
        self._documento_repo = None
    
    def processar_lote_arquivos(self, arquivos: List[Path], custo_por_km: float) -> bool:
        """
        Processa um lote de arquivos XML.
        
        Args:
            arquivos: Lista de arquivos para processar
            custo_por_km: Custo por quilômetro para cálculos
            
        Returns:
            True se processamento foi bem-sucedido
        """
        if not arquivos:
            print("❌ Nenhum arquivo para processar")
            return False
        
        print(f"🚀 Iniciando processamento de {len(arquivos)} arquivos...")
        self.stats_manager.iniciar_cronometro()
        
        try:
            for idx, arquivo in enumerate(arquivos, 1):
                self._processar_arquivo_individual(arquivo, custo_por_km, idx, len(arquivos))
            
            # Finalizar processamento
            tempo_total = self.stats_manager.parar_cronometro()
            
            # Considerar sucesso se pelo menos 50% dos arquivos foram processados
            taxa_sucesso = self.stats_manager.get_taxa_sucesso()
            sucesso = taxa_sucesso >= 50.0
            
            if sucesso:
                print(f"✅ Processamento concluído com sucesso!")
            else:
                print(f"⚠️ Processamento concluído com problemas (taxa: {taxa_sucesso:.1f}%)")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro grave no processamento: {e}")
            self.stats_manager.parar_cronometro()
            return False
    
    def _processar_arquivo_individual(self, arquivo: Path, custo_por_km: float, 
                                    idx: int, total: int) -> bool:
        """
        Processa um arquivo XML individual.
        
        Args:
            arquivo: Path do arquivo XML
            custo_por_km: Custo por quilômetro
            idx: Índice atual
            total: Total de arquivos
            
        Returns:
            True se processamento foi bem-sucedido
        """
        try:
            # 1. EXTRACT - Extrair dados do XML
            dados_cte = self._extrair_dados(arquivo)
            if not dados_cte:
                self.stats_manager.registrar_erro(
                    arquivo.name, 
                    "Falha na extração de dados"
                )
                return False
            
            # 2. TRANSFORM - Transformar e validar dados
            dados_transformados = self._transformar_dados(dados_cte, custo_por_km)
            if not dados_transformados:
                self.stats_manager.registrar_erro(
                    arquivo.name, 
                    "Falha na transformação de dados"
                )
                return False
            
            # 3. LOAD - Carregar no banco de dados
            sucesso_load = self._carregar_dados(dados_transformados)
            if not sucesso_load:
                self.stats_manager.registrar_erro(
                    arquivo.name, 
                    "Falha no carregamento no banco"
                )
                return False
            
            # Registrar sucesso
            self.stats_manager.registrar_sucesso(
                arquivo.name,
                {
                    'chave_cte': dados_cte.get('CT-e_chave', ''),
                    'valor_frete': dados_transformados.get('valor_frete', 0),
                    'quilometragem': dados_transformados.get('quilometragem', 0)
                }
            )
            
            # Mostrar progresso
            self.stats_manager.imprimir_progresso(idx, total)
            
            return True
            
        except Exception as e:
            self.stats_manager.registrar_erro(
                arquivo.name, 
                f"Erro inesperado: {str(e)}"
            )
            return False
    
    def _extrair_dados(self, arquivo: Path) -> Optional[Dict[str, Any]]:
        """
        Extrai dados do arquivo XML usando o CTE Facade.
        
        Args:
            arquivo: Path do arquivo XML
            
        Returns:
            Dados extraídos ou None se falhou
        """
        try:
            dados = self.cte_facade.extrair(arquivo)
            
            if not dados:
                print(f"   ❌ Extração falhou: {arquivo.name}")
                return None
            
            # Validações básicas
            chave = dados.get('CT-e_chave', '')
            if not chave or len(chave) != 44:
                print(f"   ❌ Chave CT-e inválida: {arquivo.name}")
                return None
            
            return dados
            
        except Exception as e:
            print(f"   ❌ Erro na extração {arquivo.name}: {e}")
            return None
    
    def _transformar_dados(self, dados_cte: Dict[str, Any], custo_por_km: float) -> Optional[Dict[str, Any]]:
        """
        Transforma e enriquece dados extraídos.
        
        Args:
            dados_cte: Dados extraídos do CT-e
            custo_por_km: Custo por quilômetro
            
        Returns:
            Dados transformados ou None se falhou
        """
        try:
            # Imports locais para evitar dependência circular
            from .quilometragem_service import QuilometragemService
            
            quilometragem_service = QuilometragemService()
            
            # Cálculo de quilometragem
            valor_frete = float(dados_cte.get('Valor_frete', 0))
            quilometragem = quilometragem_service.calcular_quilometragem(valor_frete, custo_por_km)
            
            # Normalização de dados de pessoa
            remetente = self._normalizar_dados_pessoa(dados_cte.get('Remetente', {}))
            destinatario = self._normalizar_dados_pessoa(dados_cte.get('Destinatario', {}))
            
            # Normalização de dados de veículo
            veiculo = self._normalizar_dados_veiculo(dados_cte)
            
            # Dados transformados
            dados_transformados = {
                'documento': {
                    'chave': dados_cte.get('CT-e_chave', ''),
                    'numero': dados_cte.get('CT-e_numero', ''),
                    'serie': dados_cte.get('CT-e_serie', ''),
                    'data_emissao': dados_cte.get('Data_emissao', ''),
                    'cfop': dados_cte.get('CFOP', ''),
                    'valor_frete': valor_frete,
                    'quilometragem': quilometragem
                },
                'remetente': remetente,
                'destinatario': destinatario,
                'veiculo': veiculo,
                'carga': self._extrair_dados_carga(dados_cte)
            }
            
            return dados_transformados
            
        except Exception as e:
            print(f"   ❌ Erro na transformação: {e}")
            return None
    
    def _normalizar_dados_pessoa(self, dados_pessoa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados de pessoa (remetente/destinatário).
        
        Args:
            dados_pessoa: Dados brutos da pessoa
            
        Returns:
            Dados normalizados
        """
        # Extrair documento corretamente baseado no script que funcionava
        documentos = dados_pessoa.get('documentos', {})
        cpf_cnpj = documentos.get('cnpj') or documentos.get('cpf', '')
        inscricao_estadual = documentos.get('ie', '').strip() if documentos.get('ie') else None
        
        return {
            'nome': dados_pessoa.get('nome', '').strip(),
            'cpf_cnpj': self._normalizar_documento(cpf_cnpj),
            'inscricao_estadual': inscricao_estadual,
            'endereco': self._normalizar_endereco(dados_pessoa.get('endereco', {}))
        }
    
    def _normalizar_endereco(self, dados_endereco: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados de endereço.
        
        Args:
            dados_endereco: Dados brutos do endereço
            
        Returns:
            Dados normalizados
        """
        return {
            'logradouro': dados_endereco.get('xlgr', '').strip(),
            'numero': dados_endereco.get('nro', '').strip(),
            'bairro': dados_endereco.get('xbairro', '').strip(),
            'municipio': dados_endereco.get('xmun', '').strip().upper(),
            'uf': dados_endereco.get('uf', '').strip().upper(),
            'cep': self._normalizar_cep(dados_endereco.get('cep', ''))
        }
    
    def _normalizar_dados_veiculo(self, dados_cte: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados de veículo.
        
        Args:
            dados_cte: Dados completos do CT-e
            
        Returns:
            Dados normalizados do veículo
        """
        veiculo_data = dados_cte.get('Veiculo', {})
        
        return {
            'placa': self._normalizar_placa(veiculo_data.get('placa', '')),
            'marca': veiculo_data.get('marca', '').strip().upper(),
            'modelo': veiculo_data.get('modelo', '').strip().upper(),
            'ano_fabricacao': veiculo_data.get('ano_fabricacao', ''),
            'posse': 'DESCONHECIDO'  # Valor válido do enum veiculo_posse
        }
    
    def _extrair_dados_carga(self, dados_cte: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados da carga transportada.
        
        Args:
            dados_cte: Dados completos do CT-e
            
        Returns:
            Dados da carga
        """
        carga_data = dados_cte.get('Carga', {})
        
        # Mapear campos conforme estrutura real dos dados extraídos
        return {
            'descricao': carga_data.get('propred', '').strip(),  # produto predominante
            'peso_bruto': 0.0,  # Peso não disponível nos dados atuais
            'peso_liquido': 0.0,  # Peso não disponível nos dados atuais  
            'quantidade': float(carga_data.get('qcarga', 0)),  # quantidade da carga
            'unidade': carga_data.get('unidade', 'UN').strip().upper(),
            'valor_carga': float(carga_data.get('vcarga', 0))  # valor da carga
        }
    
    def _normalizar_documento(self, documento: str) -> str:
        """Normaliza CPF/CNPJ removendo caracteres especiais."""
        if not documento:
            return ''
        return ''.join(c for c in documento if c.isdigit())
    
    def _normalizar_cep(self, cep: str) -> str:
        """Normaliza CEP para formato padrão."""
        if not cep:
            return ''
        cep_digits = ''.join(c for c in cep if c.isdigit())
        if len(cep_digits) == 8:
            return f"{cep_digits[:5]}-{cep_digits[5:]}"
        return cep_digits
    
    def _normalizar_placa(self, placa: str) -> str:
        """Normaliza placa de veículo."""
        if not placa:
            return ''
        return placa.replace('-', '').replace(' ', '').upper()
    
    def _carregar_dados(self, dados: Dict[str, Any]) -> bool:
        """
        Carrega dados transformados no banco de dados.
        
        Args:
            dados: Dados transformados para carregar
            
        Returns:
            True se carregamento foi bem-sucedido
        """
        try:
            # Aqui seria a integração com repositories
            # Por enquanto, simulação básica usando database_manager
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Inserir remetente
                    remetente_id = self._inserir_pessoa_simples(cursor, dados['remetente'])
                    if not remetente_id:
                        return False
                    
                    # Inserir destinatário
                    destinatario_id = self._inserir_pessoa_simples(cursor, dados['destinatario'])
                    if not destinatario_id:
                        return False
                    
                    # Inserir veículo
                    veiculo_id = self._inserir_veiculo_simples(cursor, dados['veiculo'])
                    
                    # Inserir documento COM dados de endereço para buscar municípios
                    documento_id = self._inserir_documento_simples(
                        cursor, dados['documento'], remetente_id, destinatario_id, veiculo_id,
                        dados['remetente'], dados['destinatario']  # Passar dados de endereço
                    )
                    
                    if documento_id:
                        # Inserir dados de carga se existirem
                        self._inserir_carga_simples(cursor, documento_id, dados['carga'])
                        
                        conn.commit()
                        self.stats_manager.incrementar('documentos_inseridos')
                        return True
                    else:
                        conn.rollback()
                        return False
            
        except Exception as e:
            print(f"   ❌ Erro no carregamento: {e}")
            return False
    
    def _inserir_pessoa_simples(self, cursor, dados_pessoa: Dict[str, Any]) -> Optional[int]:
        """
        Inserção/atualização inteligente de pessoa.
        
        Se a pessoa já existe:
        - Atualiza campos vazios com dados novos
        - Mantém campos já preenchidos
        - Log das atualizações
        """
        try:
            documento = dados_pessoa.get('cpf_cnpj', '').strip()
            nome = dados_pessoa.get('nome', '').strip()
            inscricao_estadual = dados_pessoa.get('inscricao_estadual')
            telefone = dados_pessoa.get('telefone')
            email = dados_pessoa.get('email')
            
            # Se não tem documento, não pode verificar duplicação
            if documento:
                # Verificar se existe e buscar dados atuais
                cursor.execute("""
                    SELECT 
                        id_pessoa,
                        nome,
                        inscricao_estadual,
                        telefone,
                        email
                    FROM core.pessoa 
                    WHERE cpf_cnpj = %s
                """, (documento,))
                existing = cursor.fetchone()
                
                if existing:
                    pessoa_id = existing[0]
                    campos_atualizados = []
                    
                    # Preparar valores para atualização (só atualiza se campo atual estiver vazio)
                    updates = []
                    params = []
                    
                    # IE: atualiza se vier preenchida E estiver vazia no banco
                    if inscricao_estadual and (not existing[2] or existing[2].strip() == ''):
                        updates.append("inscricao_estadual = %s")
                        params.append(inscricao_estadual)
                        campos_atualizados.append(f"IE: {inscricao_estadual}")
                    
                    # Telefone: atualiza se vier preenchido E estiver vazio no banco
                    if telefone and (not existing[3] or existing[3].strip() == ''):
                        updates.append("telefone = %s")
                        params.append(telefone)
                        campos_atualizados.append(f"Tel: {telefone}")
                    
                    # Email: atualiza se vier preenchido E estiver vazio no banco
                    if email and (not existing[4] or existing[4].strip() == ''):
                        updates.append("email = %s")
                        params.append(email)
                        campos_atualizados.append(f"Email: {email}")
                    
                    # Executar UPDATE se houver campos para atualizar
                    if updates:
                        updates.append("updated_at = NOW()")
                        params.append(pessoa_id)
                        
                        query = f"""
                            UPDATE core.pessoa 
                            SET {', '.join(updates)}
                            WHERE id_pessoa = %s
                        """
                        cursor.execute(query, params)
                        
                        # Log detalhado
                        print(f"   🔄 Pessoa atualizada: {nome[:40]}")
                        print(f"      Campos: {', '.join(campos_atualizados)}")
                        self.stats_manager.incrementar('pessoas_atualizadas')
                    
                    return pessoa_id
            
            # Inserir nova pessoa - se documento vazio, usar NULL
            doc_final = documento if documento else None
            cursor.execute("""
                INSERT INTO core.pessoa (nome, cpf_cnpj, inscricao_estadual, telefone, email, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_pessoa
            """, (nome, doc_final, inscricao_estadual, telefone, email))
            
            pessoa_id = cursor.fetchone()[0]
            self.stats_manager.incrementar('pessoas_inseridas')
            return pessoa_id
            
        except Exception as e:
            print(f"   ❌ Erro ao inserir pessoa: {e}")
            return None
    
    def _inserir_veiculo_simples(self, cursor, dados_veiculo: Dict[str, Any]) -> Optional[int]:
        """Inserção simplificada de veículo - será movida para repository."""
        try:
            placa = dados_veiculo.get('placa', '')
            
            if not placa:
                return None
            
            # Verificar se existe
            cursor.execute("SELECT id_veiculo FROM core.veiculo WHERE placa = %s", (placa,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            
            # Inserir novo veículo com valor correto do enum
            cursor.execute("""
                INSERT INTO core.veiculo (placa, marca, modelo, posse)
                VALUES (%s, %s, %s, %s)
                RETURNING id_veiculo
            """, (
                placa,
                dados_veiculo.get('marca', ''),
                dados_veiculo.get('modelo', ''),
                'DESCONHECIDO'  # Valor válido do enum
            ))
            
            veiculo_id = cursor.fetchone()[0]
            self.stats_manager.incrementar('veiculos_inseridos')
            return veiculo_id
            
        except Exception as e:
            print(f"   ❌ Erro ao inserir veículo: {e}")
            return None
    
    def _inserir_documento_simples(self, cursor, dados_doc: Dict[str, Any], 
                                  remetente_id: int, destinatario_id: int, 
                                  veiculo_id: Optional[int],
                                  dados_remetente: Dict[str, Any] = None,
                                  dados_destinatario: Dict[str, Any] = None) -> Optional[int]:
        """Inserção simplificada de documento - será movida para repository."""
        try:
            chave = dados_doc.get('chave', '')
            
            # Verificar se existe
            cursor.execute("SELECT id_cte FROM cte.documento WHERE chave = %s", (chave,))
            existing = cursor.fetchone()
            if existing:
                self.stats_manager.incrementar('documentos_duplicados')
                return existing[0]
            
            # Obter IDs dos municípios baseado nos endereços
            id_municipio_origem = None
            id_municipio_destino = None
            
            # Para origem: buscar o município do remetente
            if remetente_id:
                cursor.execute("""
                    SELECT e.id_municipio 
                    FROM core.pessoa p
                    JOIN core.pessoa_endereco pe ON p.id_pessoa = pe.id_pessoa
                    JOIN core.endereco e ON pe.id_endereco = e.id_endereco
                    WHERE p.id_pessoa = %s
                    LIMIT 1
                """, (remetente_id,))
                result = cursor.fetchone()
                if result:
                    id_municipio_origem = result[0]
            
            # Para destino: buscar o município do destinatário
            if destinatario_id:
                cursor.execute("""
                    SELECT e.id_municipio 
                    FROM core.pessoa p
                    JOIN core.pessoa_endereco pe ON p.id_pessoa = pe.id_pessoa
                    JOIN core.endereco e ON pe.id_endereco = e.id_endereco
                    WHERE p.id_pessoa = %s
                    LIMIT 1
                """, (destinatario_id,))
                result = cursor.fetchone()
                if result:
                    id_municipio_destino = result[0]
            
            # Inserir novo documento COM relacionamentos
            cursor.execute("""
                INSERT INTO cte.documento (
                    chave, numero, serie, data_emissao, cfop, 
                    valor_frete, quilometragem, 
                    id_municipio_origem, id_municipio_destino, id_veiculo,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_cte
            """, (
                chave,
                dados_doc.get('numero', ''),
                dados_doc.get('serie', ''),
                dados_doc.get('data_emissao', ''),
                dados_doc.get('cfop', ''),
                dados_doc.get('valor_frete', 0),
                dados_doc.get('quilometragem', 0),
                id_municipio_origem,
                id_municipio_destino,
                veiculo_id
            ))
            
            documento_id = cursor.fetchone()[0]
            
            # Inserir remetente e destinatário na tabela documento_parte
            self._inserir_documento_partes(cursor, documento_id, remetente_id, destinatario_id)
            
            return documento_id
            
        except Exception as e:
            print(f"   ❌ Erro ao inserir documento: {e}")
            return None
    
    def _obter_id_municipio_por_endereco(self, cursor, endereco: Dict[str, Any]) -> Optional[int]:
        """Obtém ID do município baseado nos dados do endereço."""
        try:
            municipio = endereco.get('municipio', '').strip().upper()
            uf = endereco.get('uf', '').strip().upper()
            
            if not municipio or not uf:
                return None
            
            # Busca exata primeiro
            cursor.execute("""
                SELECT m.id_municipio 
                FROM ibge.municipio m
                JOIN ibge.uf u ON m.id_uf = u.id_uf
                WHERE UPPER(m.nome) = %s AND u.sigla = %s
            """, (municipio, uf))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Busca aproximada como fallback
            cursor.execute("""
                SELECT m.id_municipio 
                FROM ibge.municipio m
                JOIN ibge.uf u ON m.id_uf = u.id_uf
                WHERE UPPER(m.nome) LIKE %s AND u.sigla = %s
                LIMIT 1
            """, (f"%{municipio}%", uf))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            print(f"   ⚠️ Erro ao buscar município: {e}")
            return None
    
    def _obter_id_municipio(self, cursor, tipo: str) -> Optional[int]:
        """Obtém ID do município baseado nos dados do endereço."""
        # Por enquanto, retorna um município padrão (Timon/MA como visto nos dados)
        # TODO: Implementar busca real baseada nos dados de endereço
        try:
            cursor.execute("""
                SELECT id_municipio 
                FROM ibge.municipio 
                WHERE nome = 'Timon' 
                AND id_uf = (SELECT id_uf FROM ibge.uf WHERE sigla = 'MA')
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None
    
    def _inserir_documento_partes(self, cursor, documento_id: int, 
                                 remetente_id: int, destinatario_id: int):
        """Insere remetente e destinatário na tabela documento_parte."""
        try:
            # Inserir remetente
            cursor.execute("""
                INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
                VALUES (%s, 'remetente', %s)
                ON CONFLICT (id_cte, tipo) DO NOTHING
            """, (documento_id, remetente_id))
            
            # Inserir destinatário
            cursor.execute("""
                INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
                VALUES (%s, 'destinatario', %s)
                ON CONFLICT (id_cte, tipo) DO NOTHING
            """, (documento_id, destinatario_id))
            
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir partes do documento: {e}")
    
    def _inserir_carga_simples(self, cursor, documento_id: int, dados_carga: Dict[str, Any]) -> bool:
        """Inserção simplificada de carga - será movida para repository."""
        try:
            if not dados_carga or not documento_id:
                return False
            
            # Obter dados da carga
            peso_bruto = dados_carga.get('peso_bruto', 0)
            peso_liquido = dados_carga.get('peso_liquido', 0)
            peso_final = peso_liquido if peso_liquido > 0 else peso_bruto
            
            quantidade = dados_carga.get('quantidade', 1)
            descricao = dados_carga.get('descricao', '').strip()
            unidade = dados_carga.get('unidade', 'UN').strip().upper()
            valor_carga = dados_carga.get('valor_carga', 0)
            
            # Inserir carga mesmo sem peso, pois temos outros dados importantes
            cursor.execute("""
                INSERT INTO cte.carga (
                    id_cte, valor, peso, quantidade, 
                    produto_predominante, unidade_medida
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_cte) DO UPDATE SET
                    valor = EXCLUDED.valor,
                    peso = EXCLUDED.peso,
                    quantidade = EXCLUDED.quantidade,
                    produto_predominante = EXCLUDED.produto_predominante,
                    unidade_medida = EXCLUDED.unidade_medida
            """, (
                documento_id,
                valor_carga,  # Usar valor real da carga
                peso_final,
                quantidade,
                descricao,
                unidade
            ))
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir carga: {e}")
            return False