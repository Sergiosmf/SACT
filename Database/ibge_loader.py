#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IBGE Loader for PostgreSQL (UF & Município)
-------------------------------------------
- Fetches official data from IBGE's public API.
- Upserts into the schema created by schema_cte_ibge_postgres.sql.
- Safe to re-run (idempotent).

Requirements:
    pip install requests psycopg2-binary

Environment variables for DB connection (default in parentheses):
    PGHOST (localhost)
    PGPORT (5432)
    PGDATABASE (postgres)
    PGUSER (postgres)
    PGPASSWORD (postgres)

Usage:
    python ibge_loader.py
"""
import os
import sys
import time
import csv
import io
from typing import List, Dict, Any

import requests
import psycopg2
from psycopg2.extras import execute_values

IBGE_ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=id"
IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id"
MUNICIPIOS_COORDENADAS_URL = "https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/municipios.csv"

def getenv(name: str, default: str) -> str:
    v = os.getenv(name, default)
    return v

def get_conn():
    dsn = {
        "host": getenv("PGHOST", "localhost"),
        "port": getenv("PGPORT", "5432"),
        "dbname": getenv("PGDATABASE", "postgres"),
        "user": getenv("PGUSER", "postgres"),
        "password": getenv("PGPASSWORD", "postgres"),
    }
    conn = psycopg2.connect(**dsn)
    conn.autocommit = False
    return conn

def fetch_json(url: str) -> Any:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()

def load_ufs(conn, estados: List[Dict[str, Any]]) -> int:
    rows = []
    for e in estados:
        id_uf = int(e["id"])
        sigla = e["sigla"]
        nome = e["nome"]
        regiao_nome = e.get("regiao", {}).get("nome")
        rows.append((id_uf, sigla, nome, regiao_nome))

    sql = """
        INSERT INTO ibge.uf (id_uf, sigla, nome, regiao)
        VALUES %s
        ON CONFLICT (id_uf) DO UPDATE
           SET sigla = EXCLUDED.sigla,
               nome = EXCLUDED.nome,
               regiao = EXCLUDED.regiao;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=100)
    return len(rows)

# Robust extractor for UF id from the IBGE municipios payload (handles API variations)
def _extract_uf_id_from_municipio(m: Dict[str, Any]):
    # Path 1: microrregiao -> mesorregiao -> UF -> id (classic structure)
    mic = m.get("microrregiao") or {}
    meso = mic.get("mesorregiao") or {}
    uf = meso.get("UF") or {}
    uf_id = uf.get("id")
    if uf_id is not None:
        try:
            return int(uf_id)
        except Exception:
            pass

    # Path 2: regiao-imediata -> regiao-intermediaria -> UF -> id (newer structure)
    ri = m.get("regiao-imediata") or m.get("regiao_imediata") or {}
    if isinstance(ri, dict):
        rint = ri.get("regiao-intermediaria") or ri.get("regiao_intermediaria") or {}
        uf2 = rint.get("UF") or {}
        uf2_id = uf2.get("id")
        if uf2_id is not None:
            try:
                return int(uf2_id)
            except Exception:
                pass

    # Not found
    return None

def load_municipios(conn, municipios: List[Dict[str, Any]], coordenadas: Dict[int, tuple]) -> int:
    rows = []
    for m in municipios:
        id_mun = int(m["id"])
        nome = m["nome"]
        # Resolve UF id with robust extractor (handles multiple API shapes)
        id_uf = _extract_uf_id_from_municipio(m)
        if id_uf is None:
            # Skip malformed/edge records, but continue loading the rest
            # (example: special territories that may not provide microrregiao)
            continue
        
        # Buscar coordenadas do dicionário
        lat, lon = coordenadas.get(id_mun, (None, None))
        rows.append((id_mun, nome, id_uf, nome, lat, lon))

    sql = """
        INSERT INTO ibge.municipio (id_municipio, nome, id_uf, nome_normalizado, latitude, longitude)
        VALUES %s
        ON CONFLICT (id_municipio) DO UPDATE
           SET nome = EXCLUDED.nome,
               id_uf = EXCLUDED.id_uf,
               nome_normalizado = EXCLUDED.nome_normalizado,
               latitude = EXCLUDED.latitude,
               longitude = EXCLUDED.longitude;
    """
    # Notar que para definir nome_normalizado chamamos a função no lado SQL.
    # O execute_values permite usar um template customizado para cada linha.
    template = "(%s, %s, %s, ibge.f_normaliza_texto(%s), %s, %s)"
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, template=template, page_size=500)
    return len(rows)

def ensure_prereqs(conn):
    # Garante extensão unaccent (usada na ibge.f_normaliza_texto) e schemas básicos (caso alguém rode isolado).
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        cur.execute("CREATE SCHEMA IF NOT EXISTS ibge;")
        # Best effort: cria função se não existir (caso o DDL principal não tenha sido rodado ainda).
        cur.execute(
            """
            CREATE OR REPLACE FUNCTION ibge.f_normaliza_texto(txt TEXT)
            RETURNS TEXT
            LANGUAGE sql
            IMMUTABLE
            AS $fn$
              SELECT NULLIF(upper(trim(unaccent($1))), '');
            $fn$;
            """
        )
    conn.commit()

def fetch_coordenadas() -> Dict[int, tuple]:
    """
    Busca coordenadas geográficas dos municípios brasileiros.
    Retorna um dicionário {codigo_ibge: (latitude, longitude)}
    """
    print("Fetching coordenadas from GitHub dataset ...")
    try:
        resp = requests.get(MUNICIPIOS_COORDENADAS_URL, timeout=60)
        resp.raise_for_status()
        
        coordenadas = {}
        csv_reader = csv.DictReader(io.StringIO(resp.text))
        
        for row in csv_reader:
            try:
                codigo_ibge = int(row['codigo_ibge'])
                latitude = float(row['latitude']) if row['latitude'] else None
                longitude = float(row['longitude']) if row['longitude'] else None
                coordenadas[codigo_ibge] = (latitude, longitude)
            except (ValueError, KeyError) as e:
                # Skip malformed rows
                continue
        
        print(f"Loaded coordinates for {len(coordenadas)} municipalities")
        return coordenadas
    except Exception as e:
        print(f"Warning: Could not fetch coordinates: {e}")
        print("Continuing without coordinates...")
        return {}

def main():
    t0 = time.time()
    print("== IBGE Loader ==")
    try:
        conn = get_conn()
    except Exception as e:
        print("Failed to connect to PostgreSQL:", e)
        sys.exit(1)

    try:
        ensure_prereqs(conn)

        print("Fetching UFs from IBGE ...")
        estados = fetch_json(IBGE_ESTADOS_URL)
        print(f"Fetched {len(estados)} UFs")

        print("Upserting UFs ...")
        n_ufs = load_ufs(conn, estados)
        print(f"Upserted UFs: {n_ufs}")

        print("Fetching Municípios from IBGE ... (this can take a few seconds)")
        municipios = fetch_json(IBGE_MUNICIPIOS_URL)
        print(f"Fetched {len(municipios)} Municípios")

        # Buscar coordenadas geográficas
        coordenadas = fetch_coordenadas()

        print("Upserting Municípios with coordinates ...")
        n_mun = load_municipios(conn, municipios, coordenadas)
        print(f"Upserted Municípios: {n_mun}")

        # Quick sanity checks
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ibge.uf;")
            u_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ibge.municipio;")
            m_count = cur.fetchone()[0]
        conn.commit()

        dt = time.time() - t0
        print(f"Done in {dt:.1f}s. Totals -> UF: {u_count}, Município: {m_count}")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
