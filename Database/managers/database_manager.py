# -*- coding: utf-8 -*-
"""
Database Manager - Gerenciamento de conexões e operações de banco
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, Optional


class CTEDatabaseManager:
    """
    Manager para gerenciamento de conexões e operações básicas do banco.
    Implementa Context Manager pattern para controle de conexões.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Inicializa o manager com configurações de banco.
        
        Args:
            db_config: Configurações de conexão PostgreSQL
        """
        self.db_config = db_config
        self._test_connection()
    
    def _test_connection(self) -> None:
        """
        Testa a conexão com o banco de dados.
        
        Raises:
            Exception: Se não conseguir conectar
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as e:
            raise Exception(f"Erro ao conectar com banco: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexão com banco.
        Garante que conexões sejam sempre fechadas.
        
        Yields:
            connection: Conexão PostgreSQL
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """
        Context manager para cursor.
        
        Args:
            dict_cursor: Se True, retorna DictCursor
            
        Yields:
            cursor: Cursor PostgreSQL
        """
        with self.get_connection() as conn:
            cursor_class = RealDictCursor if dict_cursor else None
            with conn.cursor(cursor_factory=cursor_class) as cursor:
                try:
                    yield cursor, conn
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise e
    
    def execute_query(self, query: str, params: tuple = None, 
                     fetch_one: bool = False, dict_cursor: bool = False):
        """
        Executa query e retorna resultados.
        
        Args:
            query: SQL query
            params: Parâmetros da query
            fetch_one: Se True, retorna apenas primeiro resultado
            dict_cursor: Se True, usa DictCursor
            
        Returns:
            Resultados da query
        """
        with self.get_cursor(dict_cursor=dict_cursor) as (cursor, conn):
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """
        Executa INSERT e retorna ID gerado.
        
        Args:
            query: SQL INSERT com RETURNING
            params: Parâmetros da query
            
        Returns:
            ID do registro inserido ou None
        """
        try:
            with self.get_cursor() as (cursor, conn):
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"❌ Erro no INSERT: {e}")
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Executa UPDATE e retorna linhas afetadas.
        
        Args:
            query: SQL UPDATE
            params: Parâmetros da query
            
        Returns:
            Número de linhas afetadas
        """
        try:
            with self.get_cursor() as (cursor, conn):
                cursor.execute(query, params or ())
                return cursor.rowcount
        except Exception as e:
            print(f"❌ Erro no UPDATE: {e}")
            return 0
    
    def check_record_exists(self, table: str, where_clause: str, 
                           params: tuple = None) -> bool:
        """
        Verifica se registro existe na tabela.
        
        Args:
            table: Nome da tabela
            where_clause: Cláusula WHERE (sem WHERE)
            params: Parâmetros da query
            
        Returns:
            True se registro existe
        """
        query = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
        result = self.execute_query(query, params, fetch_one=True)
        return result is not None
    
    def get_table_info(self, schema: str, table: str) -> Dict[str, Any]:
        """
        Obtém informações sobre uma tabela.
        
        Args:
            schema: Nome do schema
            table: Nome da tabela
            
        Returns:
            Informações da tabela
        """
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """
        
        results = self.execute_query(query, (schema, table), dict_cursor=True)
        return {row['column_name']: dict(row) for row in results}