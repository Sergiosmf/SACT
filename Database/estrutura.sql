--
-- PostgreSQL database dump
--

\restrict mm0hNvotUBV26UTrobBO2rrcjK6YAucZp8FHZvMkJHJv37IYLfUGfFHw66Me5r6

-- Dumped from database version 15.14 (Homebrew)
-- Dumped by pg_dump version 15.14 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: analytics; Type: SCHEMA; Schema: -; Owner: sergiomendes
--

CREATE SCHEMA analytics;


ALTER SCHEMA analytics OWNER TO sergiomendes;

--
-- Name: core; Type: SCHEMA; Schema: -; Owner: sergiomendes
--

CREATE SCHEMA core;


ALTER SCHEMA core OWNER TO sergiomendes;

--
-- Name: cte; Type: SCHEMA; Schema: -; Owner: sergiomendes
--

CREATE SCHEMA cte;


ALTER SCHEMA cte OWNER TO sergiomendes;

--
-- Name: ibge; Type: SCHEMA; Schema: -; Owner: sergiomendes
--

CREATE SCHEMA ibge;


ALTER SCHEMA ibge OWNER TO sergiomendes;

--
-- Name: staging; Type: SCHEMA; Schema: -; Owner: sergiomendes
--

CREATE SCHEMA staging;


ALTER SCHEMA staging OWNER TO sergiomendes;

--
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: veiculo_posse; Type: TYPE; Schema: core; Owner: sergiomendes
--

CREATE TYPE core.veiculo_posse AS ENUM (
    'EM_POSSE',
    'SEM_POSSE',
    'DESCONHECIDO'
);


ALTER TYPE core.veiculo_posse OWNER TO sergiomendes;

--
-- Name: f_upsert_endereco(text, text, text, text, text, text, text); Type: FUNCTION; Schema: core; Owner: sergiomendes
--

CREATE FUNCTION core.f_upsert_endereco(_logradouro text, _numero text, _complemento text, _bairro text, _cep text, _cidade_nome text, _uf_sigla text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  _id BIGINT;
  _id_mun INTEGER := ibge.f_resolve_municipio(_cidade_nome, _uf_sigla);
  _id_uf SMALLINT;
BEGIN
  IF _uf_sigla IS NOT NULL THEN
    SELECT id_uf INTO _id_uf FROM ibge.uf WHERE sigla = upper(trim(_uf_sigla));
  END IF;

  -- Deduping básico usando (logradouro, numero, cep, id_municipio)
  SELECT id_endereco INTO _id
    FROM core.endereco
   WHERE COALESCE(logradouro,'') = COALESCE(_logradouro,'')
     AND COALESCE(numero,'') = COALESCE(_numero,'')
     AND COALESCE(cep,'') = COALESCE(_cep,'')
     AND COALESCE(id_municipio, -1) = COALESCE(_id_mun, -1)
   LIMIT 1;

  IF _id IS NULL THEN
    INSERT INTO core.endereco (logradouro, numero, complemento, bairro, cep, id_municipio, id_uf)
    VALUES (_logradouro, _numero, _complemento, _bairro, _cep, _id_mun, _id_uf)
    RETURNING id_endereco INTO _id;
  ELSE
    UPDATE core.endereco
       SET complemento = COALESCE(_complemento, complemento),
           bairro = COALESCE(_bairro, bairro),
           id_uf = COALESCE(_id_uf, id_uf)
     WHERE id_endereco = _id;
  END IF;

  RETURN _id;
END $$;


ALTER FUNCTION core.f_upsert_endereco(_logradouro text, _numero text, _complemento text, _bairro text, _cep text, _cidade_nome text, _uf_sigla text) OWNER TO sergiomendes;

--
-- Name: f_upsert_pessoa(text, text, text, text, text); Type: FUNCTION; Schema: core; Owner: sergiomendes
--

CREATE FUNCTION core.f_upsert_pessoa(_nome text, _cpf_cnpj text, _ie text, _telefone text, _email text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  _id BIGINT;
  _doc TEXT := CASE WHEN _cpf_cnpj IS NULL THEN NULL ELSE regexp_replace(_cpf_cnpj, '[^0-9]', '', 'g') END;
BEGIN
  SELECT id_pessoa INTO _id FROM core.pessoa WHERE (_doc IS NOT NULL AND cpf_cnpj = _doc) OR (cpf_cnpj IS NULL AND nome = _nome) LIMIT 1;
  IF _id IS NULL THEN
    INSERT INTO core.pessoa (nome, cpf_cnpj, inscricao_estadual, telefone, email)
    VALUES (_nome, _doc, _ie, _telefone, _email)
    RETURNING id_pessoa INTO _id;
  ELSE
    UPDATE core.pessoa
       SET nome = COALESCE(_nome, nome),
           inscricao_estadual = COALESCE(_ie, inscricao_estadual),
           telefone = COALESCE(_telefone, telefone),
           email = COALESCE(_email, email)
     WHERE id_pessoa = _id;
  END IF;
  RETURN _id;
END $$;


ALTER FUNCTION core.f_upsert_pessoa(_nome text, _cpf_cnpj text, _ie text, _telefone text, _email text) OWNER TO sergiomendes;

--
-- Name: f_upsert_veiculo(text, text, text, text); Type: FUNCTION; Schema: core; Owner: sergiomendes
--

CREATE FUNCTION core.f_upsert_veiculo(_placa text, _renavam text, _proprietario text, _uf_lic text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  _id BIGINT;
  _id_uf SMALLINT;
  _placa_norm TEXT;
BEGIN
  IF _placa IS NULL THEN
    RETURN NULL;
  END IF;
  
  -- Normalizar placa: remover caracteres especiais
  _placa_norm := regexp_replace(upper(trim(_placa)), '[^A-Z0-9]', '', 'g');
  
  IF _uf_lic IS NOT NULL THEN
    SELECT id_uf INTO _id_uf FROM ibge.uf WHERE sigla = upper(trim(_uf_lic));
  END IF;

  -- Buscar por placa normalizada
  SELECT id_veiculo INTO _id 
  FROM core.veiculo 
  WHERE regexp_replace(upper(placa), '[^A-Z0-9]', '', 'g') = _placa_norm;
  
  IF _id IS NULL THEN
    -- Inserir com placa normalizada
    INSERT INTO core.veiculo (placa, renavam, proprietario, id_uf_licenciamento)
    VALUES (_placa_norm, _renavam, _proprietario, _id_uf)
    RETURNING id_veiculo INTO _id;
  ELSE
    -- Atualizar apenas se os novos valores não forem nulos
    UPDATE core.veiculo
       SET renavam = COALESCE(_renavam, renavam),
           proprietario = COALESCE(_proprietario, proprietario),
           id_uf_licenciamento = COALESCE(_id_uf, id_uf_licenciamento)
     WHERE id_veiculo = _id;
  END IF;

  RETURN _id;
END;
$$;


ALTER FUNCTION core.f_upsert_veiculo(_placa text, _renavam text, _proprietario text, _uf_lic text) OWNER TO sergiomendes;

--
-- Name: f_ingest_cte_json(jsonb); Type: FUNCTION; Schema: cte; Owner: sergiomendes
--

CREATE FUNCTION cte.f_ingest_cte_json(_payload jsonb) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  _id_cte BIGINT;
  _id_veiculo BIGINT;
  _id_mun_origem INTEGER;
  _id_mun_destino INTEGER;
  _data_emissao TIMESTAMPTZ;
  -- Partes
  _rem BIGINT; _dest BIGINT; _exp BIGINT; _rec BIGINT;
  -- Helpers para endereços das partes (formato livre do extrator)
  _rem_end BIGINT; _dest_end BIGINT; _exp_end BIGINT; _rec_end BIGINT;
  -- Campos do JSON
  _chave TEXT := _payload->>'chave';
  _numero TEXT := _payload->>'numero';
  _serie  TEXT := _payload->>'serie';
  _cfop   TEXT := _payload->>'cfop';
  _valor_frete NUMERIC := NULLIF(_payload->>'valor_frete','')::NUMERIC;
  _origem_cidade TEXT := _payload->>'origem_cidade';
  _origem_uf     TEXT := _payload->>'origem_uf';
  _destino_cidade TEXT := _payload->>'destino_cidade';
  _destino_uf     TEXT := _payload->>'destino_uf';
  _placa          TEXT := _payload->>'placa';
  _versao_schema  TEXT := _payload->>'versao_schema';
BEGIN
  IF _payload ? 'data_emissao' THEN
    -- Tenta parsear ISO-8601 'YYYY-MM-DDTHH:MI:SS' (o extrator já entrega assim)
    BEGIN
      _data_emissao := (_payload->>'data_emissao')::timestamptz;
    EXCEPTION WHEN others THEN
      _data_emissao := NULL;
    END;
  END IF;

  -- Resolve municípios via IBGE (por nome + UF)
  _id_mun_origem := ibge.f_resolve_municipio(_origem_cidade, _origem_uf);
  _id_mun_destino := ibge.f_resolve_municipio(_destino_cidade, _destino_uf);

  -- Veículo
  _id_veiculo := core.f_upsert_veiculo(_placa, NULL, NULL, _origem_uf);

  -- CT-e (upsert por chave)
  SELECT id_cte INTO _id_cte FROM cte.documento WHERE chave = _chave;
  IF _id_cte IS NULL THEN
    INSERT INTO cte.documento (chave, numero, serie, data_emissao, cfop, valor_frete,
                               versao_schema, id_municipio_origem, id_municipio_destino, id_veiculo)
    VALUES (_chave, _numero, _serie, _data_emissao, _cfop, _valor_frete,
            _versao_schema, _id_mun_origem, _id_mun_destino, _id_veiculo)
    RETURNING id_cte INTO _id_cte;
  ELSE
    UPDATE cte.documento
       SET numero = COALESCE(_numero, numero),
           serie  = COALESCE(_serie, serie),
           data_emissao = COALESCE(_data_emissao, data_emissao),
           cfop   = COALESCE(_cfop, cfop),
           valor_frete = COALESCE(_valor_frete, valor_frete),
           versao_schema = COALESCE(_versao_schema, versao_schema),
           id_municipio_origem = COALESCE(_id_mun_origem, id_municipio_origem),
           id_municipio_destino = COALESCE(_id_mun_destino, id_municipio_destino),
           id_veiculo = COALESCE(_id_veiculo, id_veiculo)
     WHERE id_cte = _id_cte;
  END IF;

  -- Carga
  INSERT INTO cte.carga (id_cte, valor, peso, quantidade, produto_predominante, unidade_medida)
  VALUES (
    _id_cte,
    NULLIF(_payload #>> '{carga,valor}', '')::NUMERIC,
    NULLIF(_payload #>> '{carga,peso}', '')::NUMERIC,
    NULLIF(_payload #>> '{carga,quantidade}', '')::NUMERIC,
    NULLIF(_payload #>> '{carga,produto_predominante}', ''),
    NULLIF(_payload #>> '{carga,unidade_medida}', '')
  )
  ON CONFLICT (id_cte) DO UPDATE SET
      valor = EXCLUDED.valor,
      peso = EXCLUDED.peso,
      quantidade = EXCLUDED.quantidade,
      produto_predominante = EXCLUDED.produto_predominante,
      unidade_medida = EXCLUDED.unidade_medida;

  -- Partes (pessoa + endereço + vínculo)
  PERFORM 1;
  -- Remetente
  _rem := core.f_upsert_pessoa(
           _payload #>> '{remetente,nome}',
           _payload #>> '{remetente,documento}',
           NULL,
           NULL,
           NULL);
  IF _rem IS NOT NULL THEN
    INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
    VALUES (_id_cte, 'remetente', _rem)
    ON CONFLICT (id_cte, tipo) DO UPDATE SET id_pessoa = EXCLUDED.id_pessoa;
  END IF;

  -- Destinatário
  _dest := core.f_upsert_pessoa(
           _payload #>> '{destinatario,nome}',
           _payload #>> '{destinatario,documento}',
           NULL,
           NULL,
           NULL);
  IF _dest IS NOT NULL THEN
    INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
    VALUES (_id_cte, 'destinatario', _dest)
    ON CONFLICT (id_cte, tipo) DO UPDATE SET id_pessoa = EXCLUDED.id_pessoa;
  END IF;

  -- Expedidor
  _exp := core.f_upsert_pessoa(
           _payload #>> '{expedidor,nome}',
           _payload #>> '{expedidor,documento}',
           NULL,
           NULL,
           NULL);
  IF _exp IS NOT NULL THEN
    INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
    VALUES (_id_cte, 'expedidor', _exp)
    ON CONFLICT (id_cte, tipo) DO UPDATE SET id_pessoa = EXCLUDED.id_pessoa;
  END IF;

  -- Recebedor
  _rec := core.f_upsert_pessoa(
           _payload #>> '{recebedor,nome}',
           _payload #>> '{recebedor,documento}',
           NULL,
           NULL,
           NULL);
  IF _rec IS NOT NULL THEN
    INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
    VALUES (_id_cte, 'recebedor', _rec)
    ON CONFLICT (id_cte, tipo) DO UPDATE SET id_pessoa = EXCLUDED.id_pessoa;
  END IF;

  RETURN _id_cte;
END $$;


ALTER FUNCTION cte.f_ingest_cte_json(_payload jsonb) OWNER TO sergiomendes;

--
-- Name: f_normaliza_texto(text); Type: FUNCTION; Schema: ibge; Owner: sergiomendes
--

CREATE FUNCTION ibge.f_normaliza_texto(txt text) RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $_$
              SELECT NULLIF(upper(trim(unaccent($1))), '');
            $_$;


ALTER FUNCTION ibge.f_normaliza_texto(txt text) OWNER TO sergiomendes;

--
-- Name: f_resolve_municipio(text, text); Type: FUNCTION; Schema: ibge; Owner: sergiomendes
--

CREATE FUNCTION ibge.f_resolve_municipio(_nome text, _sigla_uf text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
  _id_uf SMALLINT;
  _id_mun INTEGER;
  _nome_norm TEXT;
BEGIN
  IF _nome IS NULL OR _sigla_uf IS NULL THEN
    RETURN NULL;
  END IF;

  SELECT id_uf INTO _id_uf FROM ibge.uf WHERE sigla = upper(trim(_sigla_uf));
  IF _id_uf IS NULL THEN
    RETURN NULL;
  END IF;

  _nome_norm := ibge.f_normaliza_texto(_nome);
  SELECT id_municipio INTO _id_mun
    FROM ibge.municipio
   WHERE id_uf = _id_uf
     AND (nome_normalizado = _nome_norm OR ibge.f_normaliza_texto(nome) = _nome_norm)
   LIMIT 1;

  RETURN _id_mun;
END $$;


ALTER FUNCTION ibge.f_resolve_municipio(_nome text, _sigla_uf text) OWNER TO sergiomendes;

--
-- Name: trigger_set_updated_at(); Type: FUNCTION; Schema: ibge; Owner: sergiomendes
--

CREATE FUNCTION ibge.trigger_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;


ALTER FUNCTION ibge.trigger_set_updated_at() OWNER TO sergiomendes;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: documento; Type: TABLE; Schema: cte; Owner: sergiomendes
--

CREATE TABLE cte.documento (
    id_cte bigint NOT NULL,
    chave text,
    numero text,
    serie text,
    data_emissao timestamp with time zone,
    cfop text,
    valor_frete numeric(18,2),
    versao_schema text,
    id_municipio_origem integer,
    id_municipio_destino integer,
    id_veiculo bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    quilometragem integer DEFAULT 0 NOT NULL
);


ALTER TABLE cte.documento OWNER TO sergiomendes;

--
-- Name: vw_ctes_por_mes; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_ctes_por_mes AS
 SELECT (EXTRACT(year FROM documento.data_emissao))::integer AS ano,
    (EXTRACT(month FROM documento.data_emissao))::integer AS mes,
    to_char(documento.data_emissao, 'YYYY-MM'::text) AS ano_mes,
    to_char(documento.data_emissao, 'TMMonth/YYYY'::text) AS mes_nome,
    count(*) AS total_ctes,
    (sum(documento.valor_frete))::numeric(15,2) AS receita_total,
    (avg(documento.valor_frete))::numeric(10,2) AS frete_medio,
    min(documento.data_emissao) AS primeira_emissao,
    max(documento.data_emissao) AS ultima_emissao
   FROM cte.documento
  WHERE (documento.data_emissao IS NOT NULL)
  GROUP BY ((EXTRACT(year FROM documento.data_emissao))::integer), ((EXTRACT(month FROM documento.data_emissao))::integer), (to_char(documento.data_emissao, 'YYYY-MM'::text)), (to_char(documento.data_emissao, 'TMMonth/YYYY'::text))
  ORDER BY ((EXTRACT(year FROM documento.data_emissao))::integer) DESC, ((EXTRACT(month FROM documento.data_emissao))::integer) DESC;


ALTER TABLE analytics.vw_ctes_por_mes OWNER TO sergiomendes;

--
-- Name: documento_parte; Type: TABLE; Schema: cte; Owner: sergiomendes
--

CREATE TABLE cte.documento_parte (
    id_cte bigint NOT NULL,
    tipo text NOT NULL,
    id_pessoa bigint NOT NULL,
    CONSTRAINT documento_parte_tipo_check CHECK ((tipo = ANY (ARRAY['remetente'::text, 'destinatario'::text, 'expedidor'::text, 'recebedor'::text])))
);


ALTER TABLE cte.documento_parte OWNER TO sergiomendes;

--
-- Name: vw_dashboard_financeiro; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_dashboard_financeiro AS
 SELECT ( SELECT (sum(documento.valor_frete))::numeric(15,2) AS sum
           FROM cte.documento) AS receita_total,
    ( SELECT (avg(documento.valor_frete))::numeric(10,2) AS avg
           FROM cte.documento) AS ticket_medio,
    ( SELECT count(*) AS count
           FROM cte.documento) AS total_ctes,
    ( SELECT ((sum(documento.quilometragem))::numeric(15,2) * 2.50)
           FROM cte.documento
          WHERE (documento.quilometragem > 0)) AS custo_estimado_total,
    ( SELECT ((sum(documento.valor_frete) - ((sum(documento.quilometragem))::numeric * 2.50)))::numeric(15,2) AS "numeric"
           FROM cte.documento
          WHERE (documento.quilometragem > 0)) AS margem_bruta_total,
    ( SELECT round((((sum(documento.valor_frete) - ((sum(documento.quilometragem))::numeric * 2.50)) / NULLIF(sum(documento.valor_frete), (0)::numeric)) * (100)::numeric), 2) AS round
           FROM cte.documento
          WHERE ((documento.quilometragem > 0) AND (documento.valor_frete > (0)::numeric))) AS margem_percentual,
    ( SELECT count(DISTINCT documento_parte.id_pessoa) AS count
           FROM cte.documento_parte
          WHERE (documento_parte.tipo = 'remetente'::text)) AS total_clientes_remetentes,
    ( SELECT count(DISTINCT documento_parte.id_pessoa) AS count
           FROM cte.documento_parte
          WHERE (documento_parte.tipo = 'destinatario'::text)) AS total_clientes_destinatarios,
    ( SELECT (avg(sub.receita_mensal))::numeric(15,2) AS avg
           FROM ( SELECT sum(documento.valor_frete) AS receita_mensal
                   FROM cte.documento
                  WHERE (documento.data_emissao IS NOT NULL)
                  GROUP BY (EXTRACT(year FROM documento.data_emissao)), (EXTRACT(month FROM documento.data_emissao))) sub) AS receita_media_mensal,
    ( SELECT to_char(documento.data_emissao, 'TMMonth/YYYY'::text) AS to_char
           FROM cte.documento
          WHERE (documento.data_emissao IS NOT NULL)
          GROUP BY (EXTRACT(year FROM documento.data_emissao)), (EXTRACT(month FROM documento.data_emissao)), (to_char(documento.data_emissao, 'TMMonth/YYYY'::text))
          ORDER BY (sum(documento.valor_frete)) DESC
         LIMIT 1) AS melhor_mes;


ALTER TABLE analytics.vw_dashboard_financeiro OWNER TO sergiomendes;

--
-- Name: veiculo; Type: TABLE; Schema: core; Owner: sergiomendes
--

CREATE TABLE core.veiculo (
    id_veiculo bigint NOT NULL,
    placa text,
    renavam text,
    proprietario text,
    id_uf_licenciamento smallint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    posse core.veiculo_posse DEFAULT 'DESCONHECIDO'::core.veiculo_posse NOT NULL,
    observacoes text,
    ano_modelo text,
    ano_fabricacao text,
    marca text,
    modelo text,
    chassi text,
    cor text,
    CONSTRAINT ck_veiculo_ano_fabricacao CHECK (((ano_fabricacao IS NULL) OR (ano_fabricacao ~ '^[0-9]{4}$'::text))),
    CONSTRAINT ck_veiculo_ano_modelo CHECK (((ano_modelo IS NULL) OR (ano_modelo ~ '^[0-9]{4}$'::text))),
    CONSTRAINT ck_veiculo_chassi_len CHECK (((chassi IS NULL) OR (chassi ~ '^[A-HJ-NPR-Z0-9]{17}$'::text))),
    CONSTRAINT ck_veiculo_placa_format CHECK ((regexp_replace(upper(placa), '[^A-Z0-9]'::text, ''::text, 'g'::text) ~ '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'::text)),
    CONSTRAINT ck_veiculo_renavam_digits CHECK (((renavam IS NULL) OR (renavam ~ '^[0-9]{9,11}$'::text)))
);


ALTER TABLE core.veiculo OWNER TO sergiomendes;

--
-- Name: vw_dashboard_frota; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_dashboard_frota AS
 SELECT count(DISTINCT v.placa) AS total_veiculos,
    count(DISTINCT d.id_cte) AS total_viagens,
    COALESCE(sum(d.quilometragem), (0)::bigint) AS km_total_frota,
    COALESCE(sum(d.valor_frete), (0)::numeric) AS faturamento_total
   FROM (core.veiculo v
     LEFT JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (d.quilometragem > 0);


ALTER TABLE analytics.vw_dashboard_frota OWNER TO sergiomendes;

--
-- Name: carga; Type: TABLE; Schema: cte; Owner: sergiomendes
--

CREATE TABLE cte.carga (
    id_cte bigint NOT NULL,
    valor numeric(18,2),
    peso numeric(18,3),
    quantidade numeric(18,3),
    produto_predominante text,
    unidade_medida text
);


ALTER TABLE cte.carga OWNER TO sergiomendes;

--
-- Name: vw_dashboard_operacao; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_dashboard_operacao AS
 SELECT ( SELECT count(*) AS count
           FROM cte.documento) AS total_ctes,
    ( SELECT count(DISTINCT documento.id_veiculo) AS count
           FROM cte.documento
          WHERE (documento.id_veiculo IS NOT NULL)) AS total_veiculos,
    ( SELECT count(DISTINCT documento.id_municipio_origem) AS count
           FROM cte.documento
          WHERE (documento.id_municipio_origem IS NOT NULL)) AS total_origens,
    ( SELECT count(DISTINCT documento.id_municipio_destino) AS count
           FROM cte.documento
          WHERE (documento.id_municipio_destino IS NOT NULL)) AS total_destinos,
    ( SELECT (sum(documento.valor_frete))::numeric(15,2) AS sum
           FROM cte.documento) AS receita_total,
    ( SELECT (avg(documento.valor_frete))::numeric(10,2) AS avg
           FROM cte.documento) AS frete_medio,
    ( SELECT round(avg(documento.quilometragem), 2) AS round
           FROM cte.documento
          WHERE (documento.quilometragem > 0)) AS km_medio,
    ( SELECT (sum(documento.quilometragem))::numeric(15,2) AS sum
           FROM cte.documento
          WHERE (documento.quilometragem > 0)) AS km_total,
    ( SELECT round(avg((documento.valor_frete / (NULLIF(documento.quilometragem, 0))::numeric)), 2) AS round
           FROM cte.documento
          WHERE ((documento.quilometragem > 0) AND (documento.valor_frete > (0)::numeric))) AS taxa_media_km,
    ( SELECT min(documento.data_emissao) AS min
           FROM cte.documento) AS primeira_data,
    ( SELECT max(documento.data_emissao) AS max
           FROM cte.documento) AS ultima_data,
    ( SELECT carga.produto_predominante
           FROM cte.carga
          WHERE (carga.produto_predominante IS NOT NULL)
          GROUP BY carga.produto_predominante
          ORDER BY (count(*)) DESC
         LIMIT 1) AS produto_mais_transportado;


ALTER TABLE analytics.vw_dashboard_operacao OWNER TO sergiomendes;

--
-- Name: vw_distancia_media; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_distancia_media AS
 SELECT count(*) AS total_viagens_com_km,
    round(avg(documento.quilometragem), 2) AS distancia_media_km,
    round((min(documento.quilometragem))::numeric, 2) AS distancia_minima_km,
    round((max(documento.quilometragem))::numeric, 2) AS distancia_maxima_km,
    round((percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY ((documento.quilometragem)::double precision)))::numeric, 2) AS mediana_km,
    round(stddev(documento.quilometragem), 2) AS desvio_padrao_km,
    sum(
        CASE
            WHEN (documento.quilometragem <= 100) THEN 1
            ELSE 0
        END) AS ate_100km,
    sum(
        CASE
            WHEN ((documento.quilometragem > 100) AND (documento.quilometragem <= 300)) THEN 1
            ELSE 0
        END) AS de_101_a_300km,
    sum(
        CASE
            WHEN ((documento.quilometragem > 300) AND (documento.quilometragem <= 500)) THEN 1
            ELSE 0
        END) AS de_301_a_500km,
    sum(
        CASE
            WHEN ((documento.quilometragem > 500) AND (documento.quilometragem <= 1000)) THEN 1
            ELSE 0
        END) AS de_501_a_1000km,
    sum(
        CASE
            WHEN (documento.quilometragem > 1000) THEN 1
            ELSE 0
        END) AS acima_1000km
   FROM cte.documento
  WHERE (documento.quilometragem > 0);


ALTER TABLE analytics.vw_distancia_media OWNER TO sergiomendes;

--
-- Name: vw_distribuicao_viagens; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_distribuicao_viagens AS
 SELECT v.placa,
    v.modelo AS tipo,
    to_char(d.data_emissao, 'YYYY-MM'::text) AS mes_ano,
    count(d.id_cte) AS total_viagens,
    COALESCE(sum(d.quilometragem), (0)::bigint) AS km_mes
   FROM (core.veiculo v
     JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (d.quilometragem > 0)
  GROUP BY v.placa, v.modelo, (to_char(d.data_emissao, 'YYYY-MM'::text))
  ORDER BY v.placa, (to_char(d.data_emissao, 'YYYY-MM'::text)) DESC;


ALTER TABLE analytics.vw_distribuicao_viagens OWNER TO sergiomendes;

--
-- Name: pessoa; Type: TABLE; Schema: core; Owner: sergiomendes
--

CREATE TABLE core.pessoa (
    id_pessoa bigint NOT NULL,
    nome text,
    cpf_cnpj text,
    inscricao_estadual text,
    telefone text,
    email text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE core.pessoa OWNER TO sergiomendes;

--
-- Name: vw_faturamento_destinatario; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_faturamento_destinatario AS
 SELECT p.id_pessoa,
    p.nome AS cliente,
    p.cpf_cnpj AS documento,
    count(DISTINCT d.id_cte) AS total_ctes,
    (sum(d.valor_frete))::numeric(15,2) AS faturamento_total,
    (avg(d.valor_frete))::numeric(10,2) AS ticket_medio,
    (min(d.valor_frete))::numeric(10,2) AS menor_frete,
    (max(d.valor_frete))::numeric(10,2) AS maior_frete,
    (sum(d.quilometragem))::numeric(15,2) AS km_total,
    (avg(d.quilometragem))::numeric(10,2) AS km_medio,
    min(d.data_emissao) AS primeira_transacao,
    max(d.data_emissao) AS ultima_transacao,
        CASE
            WHEN (count(DISTINCT d.id_cte) >= 100) THEN '⭐ VIP'::text
            WHEN (count(DISTINCT d.id_cte) >= 50) THEN '🔥 PREMIUM'::text
            WHEN (count(DISTINCT d.id_cte) >= 20) THEN '✅ REGULAR'::text
            WHEN (count(DISTINCT d.id_cte) >= 5) THEN '⚠️ OCASIONAL'::text
            ELSE '💤 ESPORÁDICO'::text
        END AS classificacao
   FROM ((core.pessoa p
     JOIN cte.documento_parte dp ON ((p.id_pessoa = dp.id_pessoa)))
     JOIN cte.documento d ON ((dp.id_cte = d.id_cte)))
  WHERE (dp.tipo = 'destinatario'::text)
  GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj
 HAVING (count(DISTINCT d.id_cte) >= 1)
  ORDER BY ((sum(d.valor_frete))::numeric(15,2)) DESC;


ALTER TABLE analytics.vw_faturamento_destinatario OWNER TO sergiomendes;

--
-- Name: vw_faturamento_remetente; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_faturamento_remetente AS
 SELECT p.id_pessoa,
    p.nome AS cliente,
    p.cpf_cnpj AS documento,
    count(DISTINCT d.id_cte) AS total_ctes,
    (sum(d.valor_frete))::numeric(15,2) AS faturamento_total,
    (avg(d.valor_frete))::numeric(10,2) AS ticket_medio,
    (min(d.valor_frete))::numeric(10,2) AS menor_frete,
    (max(d.valor_frete))::numeric(10,2) AS maior_frete,
    (sum(d.quilometragem))::numeric(15,2) AS km_total,
    (avg(d.quilometragem))::numeric(10,2) AS km_medio,
    min(d.data_emissao) AS primeira_transacao,
    max(d.data_emissao) AS ultima_transacao,
        CASE
            WHEN (count(DISTINCT d.id_cte) >= 100) THEN '⭐ VIP'::text
            WHEN (count(DISTINCT d.id_cte) >= 50) THEN '🔥 PREMIUM'::text
            WHEN (count(DISTINCT d.id_cte) >= 20) THEN '✅ REGULAR'::text
            WHEN (count(DISTINCT d.id_cte) >= 5) THEN '⚠️ OCASIONAL'::text
            ELSE '💤 ESPORÁDICO'::text
        END AS classificacao
   FROM ((core.pessoa p
     JOIN cte.documento_parte dp ON ((p.id_pessoa = dp.id_pessoa)))
     JOIN cte.documento d ON ((dp.id_cte = d.id_cte)))
  WHERE (dp.tipo = 'remetente'::text)
  GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj
 HAVING (count(DISTINCT d.id_cte) >= 1)
  ORDER BY ((sum(d.valor_frete))::numeric(15,2)) DESC;


ALTER TABLE analytics.vw_faturamento_remetente OWNER TO sergiomendes;

--
-- Name: vw_idade_frota; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_idade_frota AS
 SELECT v.modelo AS tipo,
    count(DISTINCT v.placa) AS total_veiculos,
    round(avg((EXTRACT(year FROM CURRENT_DATE) - ((v.ano_fabricacao)::integer)::numeric)), 1) AS idade_media_anos
   FROM core.veiculo v
  WHERE (v.ano_fabricacao IS NOT NULL)
  GROUP BY v.modelo
  ORDER BY (count(DISTINCT v.placa)) DESC;


ALTER TABLE analytics.vw_idade_frota OWNER TO sergiomendes;

--
-- Name: vw_margem_veiculo; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_margem_veiculo AS
 SELECT v.placa,
    count(d.id_cte) AS total_viagens,
    (sum(d.valor_frete))::numeric(15,2) AS receita_total,
    (avg(d.valor_frete))::numeric(10,2) AS receita_media,
    (sum(d.quilometragem))::numeric(15,2) AS km_total,
    (avg(d.quilometragem))::numeric(10,2) AS km_medio,
    (((sum(d.quilometragem))::numeric * 2.50))::numeric(15,2) AS custo_estimado,
    ((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)))::numeric(15,2) AS margem_bruta,
        CASE
            WHEN (sum(d.valor_frete) > (0)::numeric) THEN round((((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)) / sum(d.valor_frete)) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS margem_percentual,
        CASE
            WHEN (sum(d.quilometragem) > 0) THEN round((sum(d.valor_frete) / (sum(d.quilometragem))::numeric), 2)
            ELSE (0)::numeric
        END AS receita_por_km,
        CASE
            WHEN ((sum(d.valor_frete) > (0)::numeric) AND ((((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)) / sum(d.valor_frete)) * (100)::numeric) >= (40)::numeric)) THEN '🔥 MUITO LUCRATIVO'::text
            WHEN ((sum(d.valor_frete) > (0)::numeric) AND ((((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)) / sum(d.valor_frete)) * (100)::numeric) >= (25)::numeric)) THEN '✅ LUCRATIVO'::text
            WHEN ((sum(d.valor_frete) > (0)::numeric) AND ((((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)) / sum(d.valor_frete)) * (100)::numeric) >= (10)::numeric)) THEN '⚠️ MARGEM BAIXA'::text
            WHEN ((sum(d.valor_frete) > (0)::numeric) AND ((((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)) / sum(d.valor_frete)) * (100)::numeric) >= (0)::numeric)) THEN '🔧 POUCO LUCRATIVO'::text
            ELSE '❌ PREJUÍZO'::text
        END AS classificacao_rentabilidade,
    min(d.data_emissao) AS primeira_viagem,
    max(d.data_emissao) AS ultima_viagem
   FROM (core.veiculo v
     JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (v.placa IS NOT NULL)
  GROUP BY v.placa
  ORDER BY (((sum(d.valor_frete) - ((sum(d.quilometragem))::numeric * 2.50)))::numeric(15,2)) DESC;


ALTER TABLE analytics.vw_margem_veiculo OWNER TO sergiomendes;

--
-- Name: vw_performance_frota; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_performance_frota AS
 SELECT v.placa,
    v.modelo AS tipo,
    (v.ano_fabricacao)::integer AS ano_fabricacao,
    count(d.id_cte) AS total_viagens,
    COALESCE(sum(d.quilometragem), (0)::bigint) AS km_total,
    COALESCE(sum(d.valor_frete), (0)::numeric) AS faturamento_total,
    round(COALESCE((sum(d.valor_frete) / (NULLIF(sum(d.quilometragem), 0))::numeric), (0)::numeric), 2) AS receita_por_km
   FROM (core.veiculo v
     LEFT JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (d.quilometragem > 0)
  GROUP BY v.placa, v.modelo, v.ano_fabricacao
  ORDER BY COALESCE(sum(d.valor_frete), (0)::numeric) DESC;


ALTER TABLE analytics.vw_performance_frota OWNER TO sergiomendes;

--
-- Name: vw_produtos_predominantes; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_produtos_predominantes AS
 SELECT COALESCE(c.produto_predominante, 'NÃO INFORMADO'::text) AS produto,
    count(DISTINCT d.id_cte) AS total_ctes,
    (sum(c.quantidade))::numeric(15,2) AS quantidade_total,
    c.unidade_medida,
    (sum(c.peso))::numeric(15,2) AS peso_total_kg,
    (avg(c.peso))::numeric(10,2) AS peso_medio_kg,
    (sum(d.valor_frete))::numeric(15,2) AS receita_total,
    (avg(d.valor_frete))::numeric(10,2) AS frete_medio,
        CASE
            WHEN (sum(c.peso) > (0)::numeric) THEN round((sum(d.valor_frete) / sum(c.peso)), 2)
            ELSE (0)::numeric
        END AS receita_por_kg,
        CASE
            WHEN (count(DISTINCT d.id_cte) >= 100) THEN '⭐ TOP PRODUTO'::text
            WHEN (count(DISTINCT d.id_cte) >= 50) THEN '✅ REGULAR'::text
            WHEN (count(DISTINCT d.id_cte) >= 20) THEN '⚠️ OCASIONAL'::text
            ELSE '💤 RARO'::text
        END AS classificacao
   FROM (cte.documento d
     LEFT JOIN cte.carga c ON ((d.id_cte = c.id_cte)))
  GROUP BY c.produto_predominante, c.unidade_medida
 HAVING (count(DISTINCT d.id_cte) >= 1)
  ORDER BY (count(DISTINCT d.id_cte)) DESC;


ALTER TABLE analytics.vw_produtos_predominantes OWNER TO sergiomendes;

--
-- Name: vw_ranking_clientes; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_ranking_clientes AS
 SELECT p.id_pessoa,
    p.nome AS cliente,
    p.cpf_cnpj AS documento,
    dp.tipo AS tipo_cliente,
    count(DISTINCT d.id_cte) AS total_ctes,
    (sum(d.valor_frete))::numeric(15,2) AS faturamento_total,
    (avg(d.valor_frete))::numeric(10,2) AS ticket_medio,
    round(((sum(d.valor_frete) / ( SELECT sum(documento.valor_frete) AS sum
           FROM cte.documento)) * (100)::numeric), 2) AS participacao_percentual,
    (sum(d.quilometragem))::numeric(15,2) AS km_total,
    min(d.data_emissao) AS primeira_transacao,
    max(d.data_emissao) AS ultima_transacao,
        CASE
            WHEN (count(DISTINCT d.id_cte) >= 100) THEN '⭐ VIP'::text
            WHEN (count(DISTINCT d.id_cte) >= 50) THEN '🔥 PREMIUM'::text
            WHEN (count(DISTINCT d.id_cte) >= 20) THEN '✅ REGULAR'::text
            WHEN (count(DISTINCT d.id_cte) >= 5) THEN '⚠️ OCASIONAL'::text
            ELSE '💤 ESPORÁDICO'::text
        END AS classificacao,
    row_number() OVER (ORDER BY (sum(d.valor_frete)) DESC) AS ranking
   FROM ((core.pessoa p
     JOIN cte.documento_parte dp ON ((p.id_pessoa = dp.id_pessoa)))
     JOIN cte.documento d ON ((dp.id_cte = d.id_cte)))
  WHERE (dp.tipo = 'remetente'::text)
  GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj, dp.tipo
 HAVING (count(DISTINCT d.id_cte) >= 1)
  ORDER BY ((sum(d.valor_frete))::numeric(15,2)) DESC
 LIMIT 20;


ALTER TABLE analytics.vw_ranking_clientes OWNER TO sergiomendes;

--
-- Name: vw_receita_mensal; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_receita_mensal AS
 WITH receita_base AS (
         SELECT (EXTRACT(year FROM documento.data_emissao))::integer AS ano,
            (EXTRACT(month FROM documento.data_emissao))::integer AS mes,
            to_char(documento.data_emissao, 'YYYY-MM'::text) AS ano_mes,
            to_char(documento.data_emissao, 'TMMonth/YYYY'::text) AS mes_nome,
            count(*) AS total_ctes,
            (sum(documento.valor_frete))::numeric(15,2) AS receita_total,
            (avg(documento.valor_frete))::numeric(10,2) AS receita_media,
            (min(documento.valor_frete))::numeric(10,2) AS receita_minima,
            (max(documento.valor_frete))::numeric(10,2) AS receita_maxima,
            (sum(documento.quilometragem))::numeric(15,2) AS km_total,
            (avg(documento.quilometragem))::numeric(10,2) AS km_medio,
                CASE
                    WHEN (sum(documento.quilometragem) > 0) THEN round((sum(documento.valor_frete) / (sum(documento.quilometragem))::numeric), 2)
                    ELSE (0)::numeric
                END AS receita_por_km
           FROM cte.documento
          WHERE (documento.data_emissao IS NOT NULL)
          GROUP BY ((EXTRACT(year FROM documento.data_emissao))::integer), ((EXTRACT(month FROM documento.data_emissao))::integer), (to_char(documento.data_emissao, 'YYYY-MM'::text)), (to_char(documento.data_emissao, 'TMMonth/YYYY'::text))
        )
 SELECT receita_base.ano,
    receita_base.mes,
    receita_base.ano_mes,
    receita_base.mes_nome,
    receita_base.total_ctes,
    receita_base.receita_total,
    receita_base.receita_media,
    receita_base.receita_minima,
    receita_base.receita_maxima,
    receita_base.km_total,
    receita_base.km_medio,
    receita_base.receita_por_km,
    lag(receita_base.receita_total) OVER (ORDER BY receita_base.ano, receita_base.mes) AS receita_mes_anterior
   FROM receita_base
  ORDER BY receita_base.ano DESC, receita_base.mes DESC;


ALTER TABLE analytics.vw_receita_mensal OWNER TO sergiomendes;

--
-- Name: VIEW vw_receita_mensal; Type: COMMENT; Schema: analytics; Owner: sergiomendes
--

COMMENT ON VIEW analytics.vw_receita_mensal IS 'Receita total de frete por mês com métricas de performance';


--
-- Name: vw_rodagem_total; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_rodagem_total AS
 SELECT v.placa,
    v.modelo AS tipo,
    (v.ano_fabricacao)::integer AS ano_fabricacao,
    count(d.id_cte) AS total_viagens,
    COALESCE(sum(d.quilometragem), (0)::bigint) AS km_total,
    round(COALESCE(avg(d.quilometragem), (0)::numeric), 2) AS km_medio_viagem
   FROM (core.veiculo v
     LEFT JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (d.quilometragem > 0)
  GROUP BY v.placa, v.modelo, v.ano_fabricacao
  ORDER BY COALESCE(sum(d.quilometragem), (0)::bigint) DESC;


ALTER TABLE analytics.vw_rodagem_total OWNER TO sergiomendes;

--
-- Name: vw_taxa_frete_km; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_taxa_frete_km AS
 SELECT count(*) AS total_viagens,
    round(avg((documento.valor_frete / (NULLIF(documento.quilometragem, 0))::numeric)), 2) AS taxa_media_por_km,
    round(min((documento.valor_frete / (NULLIF(documento.quilometragem, 0))::numeric)), 2) AS taxa_minima_por_km,
    round(max((documento.valor_frete / (NULLIF(documento.quilometragem, 0))::numeric)), 2) AS taxa_maxima_por_km,
    round((percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY (((documento.valor_frete / (NULLIF(documento.quilometragem, 0))::numeric))::double precision)))::numeric, 2) AS taxa_mediana_por_km,
    round(avg(
        CASE
            WHEN (documento.quilometragem <= 100) THEN (documento.valor_frete / (documento.quilometragem)::numeric)
            ELSE NULL::numeric
        END), 2) AS taxa_ate_100km,
    round(avg(
        CASE
            WHEN ((documento.quilometragem > 100) AND (documento.quilometragem <= 300)) THEN (documento.valor_frete / (documento.quilometragem)::numeric)
            ELSE NULL::numeric
        END), 2) AS taxa_101_300km,
    round(avg(
        CASE
            WHEN ((documento.quilometragem > 300) AND (documento.quilometragem <= 500)) THEN (documento.valor_frete / (documento.quilometragem)::numeric)
            ELSE NULL::numeric
        END), 2) AS taxa_301_500km,
    round(avg(
        CASE
            WHEN ((documento.quilometragem > 500) AND (documento.quilometragem <= 1000)) THEN (documento.valor_frete / (documento.quilometragem)::numeric)
            ELSE NULL::numeric
        END), 2) AS taxa_501_1000km,
    round(avg(
        CASE
            WHEN (documento.quilometragem > 1000) THEN (documento.valor_frete / (documento.quilometragem)::numeric)
            ELSE NULL::numeric
        END), 2) AS taxa_acima_1000km
   FROM cte.documento
  WHERE ((documento.quilometragem > 0) AND (documento.valor_frete > (0)::numeric));


ALTER TABLE analytics.vw_taxa_frete_km OWNER TO sergiomendes;

--
-- Name: vw_tempo_parada; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_tempo_parada AS
 WITH viagens_ordenadas AS (
         SELECT v.placa,
            v.modelo AS tipo,
            d.data_emissao,
            lag(d.data_emissao) OVER (PARTITION BY v.placa ORDER BY d.data_emissao) AS data_anterior
           FROM (core.veiculo v
             JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
          WHERE (d.quilometragem > 0)
        )
 SELECT viagens_ordenadas.placa,
    viagens_ordenadas.tipo,
    count(*) AS total_intervalos,
    round(avg(EXTRACT(days FROM (viagens_ordenadas.data_emissao - viagens_ordenadas.data_anterior))), 1) AS dias_parada_media
   FROM viagens_ordenadas
  WHERE (viagens_ordenadas.data_anterior IS NOT NULL)
  GROUP BY viagens_ordenadas.placa, viagens_ordenadas.tipo
  ORDER BY (round(avg(EXTRACT(days FROM (viagens_ordenadas.data_emissao - viagens_ordenadas.data_anterior))), 1));


ALTER TABLE analytics.vw_tempo_parada OWNER TO sergiomendes;

--
-- Name: vw_ticket_medio; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_ticket_medio AS
 SELECT count(*) AS total_viagens,
    (sum(documento.valor_frete))::numeric(15,2) AS receita_total,
    (avg(documento.valor_frete))::numeric(10,2) AS ticket_medio,
    (percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY ((documento.valor_frete)::double precision)))::numeric(10,2) AS ticket_mediano,
    (min(documento.valor_frete))::numeric(10,2) AS ticket_minimo,
    (max(documento.valor_frete))::numeric(10,2) AS ticket_maximo,
    (stddev(documento.valor_frete))::numeric(10,2) AS desvio_padrao,
    sum(
        CASE
            WHEN (documento.valor_frete <= (100)::numeric) THEN 1
            ELSE 0
        END) AS ate_100,
    sum(
        CASE
            WHEN ((documento.valor_frete > (100)::numeric) AND (documento.valor_frete <= (500)::numeric)) THEN 1
            ELSE 0
        END) AS de_101_a_500,
    sum(
        CASE
            WHEN ((documento.valor_frete > (500)::numeric) AND (documento.valor_frete <= (1000)::numeric)) THEN 1
            ELSE 0
        END) AS de_501_a_1000,
    sum(
        CASE
            WHEN ((documento.valor_frete > (1000)::numeric) AND (documento.valor_frete <= (3000)::numeric)) THEN 1
            ELSE 0
        END) AS de_1001_a_3000,
    sum(
        CASE
            WHEN (documento.valor_frete > (3000)::numeric) THEN 1
            ELSE 0
        END) AS acima_3000,
    (avg(
        CASE
            WHEN (documento.quilometragem <= 100) THEN documento.valor_frete
            ELSE NULL::numeric
        END))::numeric(10,2) AS ticket_medio_ate_100km,
    (avg(
        CASE
            WHEN ((documento.quilometragem > 100) AND (documento.quilometragem <= 300)) THEN documento.valor_frete
            ELSE NULL::numeric
        END))::numeric(10,2) AS ticket_medio_101_300km,
    (avg(
        CASE
            WHEN ((documento.quilometragem > 300) AND (documento.quilometragem <= 500)) THEN documento.valor_frete
            ELSE NULL::numeric
        END))::numeric(10,2) AS ticket_medio_301_500km,
    (avg(
        CASE
            WHEN ((documento.quilometragem > 500) AND (documento.quilometragem <= 1000)) THEN documento.valor_frete
            ELSE NULL::numeric
        END))::numeric(10,2) AS ticket_medio_501_1000km,
    (avg(
        CASE
            WHEN (documento.quilometragem > 1000) THEN documento.valor_frete
            ELSE NULL::numeric
        END))::numeric(10,2) AS ticket_medio_acima_1000km
   FROM cte.documento
  WHERE (documento.valor_frete > (0)::numeric);


ALTER TABLE analytics.vw_ticket_medio OWNER TO sergiomendes;

--
-- Name: municipio; Type: TABLE; Schema: ibge; Owner: sergiomendes
--

CREATE TABLE ibge.municipio (
    id_municipio integer NOT NULL,
    nome text NOT NULL,
    id_uf smallint NOT NULL,
    nome_normalizado text,
    latitude numeric(9,6),
    longitude numeric(9,6),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE ibge.municipio OWNER TO sergiomendes;

--
-- Name: uf; Type: TABLE; Schema: ibge; Owner: sergiomendes
--

CREATE TABLE ibge.uf (
    id_uf smallint NOT NULL,
    sigla character(2) NOT NULL,
    nome text NOT NULL,
    regiao text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE ibge.uf OWNER TO sergiomendes;

--
-- Name: vw_top_destinos; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_top_destinos AS
 SELECT m.nome AS municipio,
    uf.sigla AS uf,
    concat(m.nome, ' - ', uf.sigla) AS destino_completo,
    count(d.id_cte) AS total_viagens,
    (sum(d.valor_frete))::numeric(15,2) AS receita_total,
    (avg(d.valor_frete))::numeric(10,2) AS frete_medio,
    round(avg(d.quilometragem), 2) AS distancia_media_km,
    count(DISTINCT d.id_veiculo) AS veiculos_distintos
   FROM ((cte.documento d
     JOIN ibge.municipio m ON ((d.id_municipio_destino = m.id_municipio)))
     JOIN ibge.uf uf ON ((m.id_uf = uf.id_uf)))
  WHERE (d.id_municipio_destino IS NOT NULL)
  GROUP BY m.nome, uf.sigla
  ORDER BY (count(d.id_cte)) DESC
 LIMIT 10;


ALTER TABLE analytics.vw_top_destinos OWNER TO sergiomendes;

--
-- Name: vw_top_origens; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_top_origens AS
 SELECT m.nome AS municipio,
    uf.sigla AS uf,
    concat(m.nome, ' - ', uf.sigla) AS origem_completa,
    count(d.id_cte) AS total_viagens,
    (sum(d.valor_frete))::numeric(15,2) AS receita_total,
    (avg(d.valor_frete))::numeric(10,2) AS frete_medio,
    round(avg(d.quilometragem), 2) AS distancia_media_km,
    count(DISTINCT d.id_veiculo) AS veiculos_distintos
   FROM ((cte.documento d
     JOIN ibge.municipio m ON ((d.id_municipio_origem = m.id_municipio)))
     JOIN ibge.uf uf ON ((m.id_uf = uf.id_uf)))
  WHERE (d.id_municipio_origem IS NOT NULL)
  GROUP BY m.nome, uf.sigla
  ORDER BY (count(d.id_cte)) DESC
 LIMIT 10;


ALTER TABLE analytics.vw_top_origens OWNER TO sergiomendes;

--
-- Name: vw_veiculos_uso_extremo; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_veiculos_uso_extremo AS
 WITH uso_veiculos AS (
         SELECT v.placa,
            v.modelo AS tipo,
            (v.ano_fabricacao)::integer AS ano_fabricacao,
            count(d.id_cte) AS total_viagens,
            COALESCE(sum(d.quilometragem), (0)::bigint) AS km_total,
            row_number() OVER (ORDER BY (sum(d.quilometragem)) DESC) AS rank_maior,
            row_number() OVER (ORDER BY (sum(d.quilometragem))) AS rank_menor
           FROM (core.veiculo v
             JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
          WHERE (d.quilometragem > 0)
          GROUP BY v.placa, v.modelo, v.ano_fabricacao
        )
 SELECT uso_veiculos.placa,
    uso_veiculos.tipo,
    uso_veiculos.ano_fabricacao,
    uso_veiculos.total_viagens,
    uso_veiculos.km_total,
    uso_veiculos.rank_maior,
    uso_veiculos.rank_menor
   FROM uso_veiculos
  WHERE ((uso_veiculos.rank_maior <= 10) OR (uso_veiculos.rank_menor <= 10))
  ORDER BY uso_veiculos.km_total DESC;


ALTER TABLE analytics.vw_veiculos_uso_extremo OWNER TO sergiomendes;

--
-- Name: vw_viagens_por_veiculo; Type: VIEW; Schema: analytics; Owner: sergiomendes
--

CREATE VIEW analytics.vw_viagens_por_veiculo AS
 SELECT v.placa,
    count(d.id_cte) AS total_viagens,
    (sum(d.valor_frete))::numeric(15,2) AS receita_total,
    (avg(d.valor_frete))::numeric(10,2) AS frete_medio_por_viagem,
    round(avg(d.quilometragem), 2) AS km_medio_por_viagem,
    (sum(d.quilometragem))::numeric(12,2) AS km_total_percorrido,
    min(d.data_emissao) AS primeira_viagem,
    max(d.data_emissao) AS ultima_viagem,
        CASE
            WHEN (count(d.id_cte) >= 100) THEN '🔥 MUITO ATIVO'::text
            WHEN (count(d.id_cte) >= 50) THEN '✅ ATIVO'::text
            WHEN (count(d.id_cte) >= 20) THEN '⚠️ MODERADO'::text
            ELSE '💤 BAIXA ATIVIDADE'::text
        END AS classificacao
   FROM (core.veiculo v
     JOIN cte.documento d ON ((v.id_veiculo = d.id_veiculo)))
  WHERE (v.placa IS NOT NULL)
  GROUP BY v.placa
  ORDER BY (count(d.id_cte)) DESC;


ALTER TABLE analytics.vw_viagens_por_veiculo OWNER TO sergiomendes;

--
-- Name: endereco; Type: TABLE; Schema: core; Owner: sergiomendes
--

CREATE TABLE core.endereco (
    id_endereco bigint NOT NULL,
    logradouro text,
    numero text,
    complemento text,
    bairro text,
    cep text,
    id_municipio integer,
    id_uf smallint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE core.endereco OWNER TO sergiomendes;

--
-- Name: endereco_id_endereco_seq; Type: SEQUENCE; Schema: core; Owner: sergiomendes
--

CREATE SEQUENCE core.endereco_id_endereco_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE core.endereco_id_endereco_seq OWNER TO sergiomendes;

--
-- Name: endereco_id_endereco_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: sergiomendes
--

ALTER SEQUENCE core.endereco_id_endereco_seq OWNED BY core.endereco.id_endereco;


--
-- Name: pessoa_endereco; Type: TABLE; Schema: core; Owner: sergiomendes
--

CREATE TABLE core.pessoa_endereco (
    id_pessoa bigint NOT NULL,
    id_endereco bigint NOT NULL,
    tipo text DEFAULT 'principal'::text NOT NULL
);


ALTER TABLE core.pessoa_endereco OWNER TO sergiomendes;

--
-- Name: pessoa_id_pessoa_seq; Type: SEQUENCE; Schema: core; Owner: sergiomendes
--

CREATE SEQUENCE core.pessoa_id_pessoa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE core.pessoa_id_pessoa_seq OWNER TO sergiomendes;

--
-- Name: pessoa_id_pessoa_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: sergiomendes
--

ALTER SEQUENCE core.pessoa_id_pessoa_seq OWNED BY core.pessoa.id_pessoa;


--
-- Name: veiculo_id_veiculo_seq; Type: SEQUENCE; Schema: core; Owner: sergiomendes
--

CREATE SEQUENCE core.veiculo_id_veiculo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE core.veiculo_id_veiculo_seq OWNER TO sergiomendes;

--
-- Name: veiculo_id_veiculo_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: sergiomendes
--

ALTER SEQUENCE core.veiculo_id_veiculo_seq OWNED BY core.veiculo.id_veiculo;


--
-- Name: vw_cte_resumo; Type: VIEW; Schema: core; Owner: sergiomendes
--

CREATE VIEW core.vw_cte_resumo AS
 SELECT d.id_cte,
    d.chave,
    d.numero AS numero_cte,
    d.serie,
    d.data_emissao,
    d.cfop,
    round(d.valor_frete, 2) AS valor_frete,
    pr.nome AS remetente_nome,
    pr.cpf_cnpj AS remetente_documento,
    pd.nome AS destinatario_nome,
    pd.cpf_cnpj AS destinatario_documento,
    v.placa,
    mo.nome AS municipio_origem,
    uf_o.sigla AS uf_origem,
    md.nome AS municipio_destino,
    uf_d.sigla AS uf_destino,
    c.valor AS carga_valor,
    c.peso AS carga_peso,
    c.quantidade AS carga_quantidade
   FROM ((((((((((cte.documento d
     LEFT JOIN cte.documento_parte dp_rem ON (((d.id_cte = dp_rem.id_cte) AND (dp_rem.tipo = 'remetente'::text))))
     LEFT JOIN core.pessoa pr ON ((dp_rem.id_pessoa = pr.id_pessoa)))
     LEFT JOIN cte.documento_parte dp_dest ON (((d.id_cte = dp_dest.id_cte) AND (dp_dest.tipo = 'destinatario'::text))))
     LEFT JOIN core.pessoa pd ON ((dp_dest.id_pessoa = pd.id_pessoa)))
     LEFT JOIN core.veiculo v ON ((d.id_veiculo = v.id_veiculo)))
     LEFT JOIN ibge.municipio mo ON ((d.id_municipio_origem = mo.id_municipio)))
     LEFT JOIN ibge.uf uf_o ON ((mo.id_uf = uf_o.id_uf)))
     LEFT JOIN ibge.municipio md ON ((d.id_municipio_destino = md.id_municipio)))
     LEFT JOIN ibge.uf uf_d ON ((md.id_uf = uf_d.id_uf)))
     LEFT JOIN cte.carga c ON ((d.id_cte = c.id_cte)))
  ORDER BY d.data_emissao DESC;


ALTER TABLE core.vw_cte_resumo OWNER TO sergiomendes;

--
-- Name: documento_id_cte_seq; Type: SEQUENCE; Schema: cte; Owner: sergiomendes
--

CREATE SEQUENCE cte.documento_id_cte_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cte.documento_id_cte_seq OWNER TO sergiomendes;

--
-- Name: documento_id_cte_seq; Type: SEQUENCE OWNED BY; Schema: cte; Owner: sergiomendes
--

ALTER SEQUENCE cte.documento_id_cte_seq OWNED BY cte.documento.id_cte;


--
-- Name: vw_cte_resumo; Type: VIEW; Schema: cte; Owner: sergiomendes
--

CREATE VIEW cte.vw_cte_resumo AS
 SELECT d.numero AS numero_cte,
    mo.nome AS cidade_origem,
    ufo.sigla AS uf_origem,
    md.nome AS cidade_destino,
    ufd.sigla AS uf_destino,
    v.placa,
    d.valor_frete,
    d.quilometragem
   FROM (((((cte.documento d
     JOIN ibge.municipio mo ON ((mo.id_municipio = d.id_municipio_origem)))
     JOIN ibge.uf ufo ON ((ufo.id_uf = mo.id_uf)))
     JOIN ibge.municipio md ON ((md.id_municipio = d.id_municipio_destino)))
     JOIN ibge.uf ufd ON ((ufd.id_uf = md.id_uf)))
     JOIN core.veiculo v ON ((v.id_veiculo = d.id_veiculo)));


ALTER TABLE cte.vw_cte_resumo OWNER TO sergiomendes;

--
-- Name: vw_dashboard_executivo; Type: VIEW; Schema: public; Owner: sergiomendes
--

CREATE VIEW public.vw_dashboard_executivo AS
 SELECT 'Resumo Geral'::text AS categoria,
    ( SELECT count(*) AS count
           FROM cte.documento) AS total_ctes,
    ( SELECT (sum(documento.valor_frete))::numeric(15,2) AS sum
           FROM cte.documento) AS valor_total_frete,
    ( SELECT (sum(carga.valor))::numeric(15,2) AS sum
           FROM cte.carga) AS valor_total_carga,
    ( SELECT count(DISTINCT documento.id_municipio_origem) AS count
           FROM cte.documento
          WHERE (documento.id_municipio_origem IS NOT NULL)) AS cidades_origem,
    ( SELECT count(DISTINCT documento.id_municipio_destino) AS count
           FROM cte.documento
          WHERE (documento.id_municipio_destino IS NOT NULL)) AS cidades_destino,
    ( SELECT count(DISTINCT carga.produto_predominante) AS count
           FROM cte.carga) AS tipos_produtos,
    ( SELECT (avg(documento.quilometragem))::numeric(10,2) AS avg
           FROM cte.documento
          WHERE (documento.quilometragem > 0)) AS media_quilometragem;


ALTER TABLE public.vw_dashboard_executivo OWNER TO sergiomendes;

--
-- Name: raw_cte_json; Type: TABLE; Schema: staging; Owner: sergiomendes
--

CREATE TABLE staging.raw_cte_json (
    id_raw bigint NOT NULL,
    recebido_em timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb NOT NULL
);


ALTER TABLE staging.raw_cte_json OWNER TO sergiomendes;

--
-- Name: raw_cte_json_id_raw_seq; Type: SEQUENCE; Schema: staging; Owner: sergiomendes
--

CREATE SEQUENCE staging.raw_cte_json_id_raw_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE staging.raw_cte_json_id_raw_seq OWNER TO sergiomendes;

--
-- Name: raw_cte_json_id_raw_seq; Type: SEQUENCE OWNED BY; Schema: staging; Owner: sergiomendes
--

ALTER SEQUENCE staging.raw_cte_json_id_raw_seq OWNED BY staging.raw_cte_json.id_raw;


--
-- Name: endereco id_endereco; Type: DEFAULT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.endereco ALTER COLUMN id_endereco SET DEFAULT nextval('core.endereco_id_endereco_seq'::regclass);


--
-- Name: pessoa id_pessoa; Type: DEFAULT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa ALTER COLUMN id_pessoa SET DEFAULT nextval('core.pessoa_id_pessoa_seq'::regclass);


--
-- Name: veiculo id_veiculo; Type: DEFAULT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.veiculo ALTER COLUMN id_veiculo SET DEFAULT nextval('core.veiculo_id_veiculo_seq'::regclass);


--
-- Name: documento id_cte; Type: DEFAULT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento ALTER COLUMN id_cte SET DEFAULT nextval('cte.documento_id_cte_seq'::regclass);


--
-- Name: raw_cte_json id_raw; Type: DEFAULT; Schema: staging; Owner: sergiomendes
--

ALTER TABLE ONLY staging.raw_cte_json ALTER COLUMN id_raw SET DEFAULT nextval('staging.raw_cte_json_id_raw_seq'::regclass);


--
-- Name: endereco endereco_pkey; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.endereco
    ADD CONSTRAINT endereco_pkey PRIMARY KEY (id_endereco);


--
-- Name: pessoa pessoa_cpf_cnpj_key; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa
    ADD CONSTRAINT pessoa_cpf_cnpj_key UNIQUE (cpf_cnpj);


--
-- Name: pessoa_endereco pessoa_endereco_pkey; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa_endereco
    ADD CONSTRAINT pessoa_endereco_pkey PRIMARY KEY (id_pessoa, id_endereco);


--
-- Name: pessoa pessoa_pkey; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa
    ADD CONSTRAINT pessoa_pkey PRIMARY KEY (id_pessoa);


--
-- Name: veiculo veiculo_chassi_key; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.veiculo
    ADD CONSTRAINT veiculo_chassi_key UNIQUE (chassi);


--
-- Name: veiculo veiculo_pkey; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.veiculo
    ADD CONSTRAINT veiculo_pkey PRIMARY KEY (id_veiculo);


--
-- Name: veiculo veiculo_placa_key; Type: CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.veiculo
    ADD CONSTRAINT veiculo_placa_key UNIQUE (placa);


--
-- Name: carga carga_pkey; Type: CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.carga
    ADD CONSTRAINT carga_pkey PRIMARY KEY (id_cte);


--
-- Name: documento documento_chave_key; Type: CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento
    ADD CONSTRAINT documento_chave_key UNIQUE (chave);


--
-- Name: documento_parte documento_parte_pkey; Type: CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento_parte
    ADD CONSTRAINT documento_parte_pkey PRIMARY KEY (id_cte, tipo);


--
-- Name: documento documento_pkey; Type: CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento
    ADD CONSTRAINT documento_pkey PRIMARY KEY (id_cte);


--
-- Name: municipio municipio_nome_id_uf_key; Type: CONSTRAINT; Schema: ibge; Owner: sergiomendes
--

ALTER TABLE ONLY ibge.municipio
    ADD CONSTRAINT municipio_nome_id_uf_key UNIQUE (nome, id_uf);


--
-- Name: municipio municipio_pkey; Type: CONSTRAINT; Schema: ibge; Owner: sergiomendes
--

ALTER TABLE ONLY ibge.municipio
    ADD CONSTRAINT municipio_pkey PRIMARY KEY (id_municipio);


--
-- Name: uf uf_pkey; Type: CONSTRAINT; Schema: ibge; Owner: sergiomendes
--

ALTER TABLE ONLY ibge.uf
    ADD CONSTRAINT uf_pkey PRIMARY KEY (id_uf);


--
-- Name: uf uf_sigla_key; Type: CONSTRAINT; Schema: ibge; Owner: sergiomendes
--

ALTER TABLE ONLY ibge.uf
    ADD CONSTRAINT uf_sigla_key UNIQUE (sigla);


--
-- Name: raw_cte_json raw_cte_json_pkey; Type: CONSTRAINT; Schema: staging; Owner: sergiomendes
--

ALTER TABLE ONLY staging.raw_cte_json
    ADD CONSTRAINT raw_cte_json_pkey PRIMARY KEY (id_raw);


--
-- Name: uq_veiculo_placa_norm; Type: INDEX; Schema: core; Owner: sergiomendes
--

CREATE UNIQUE INDEX uq_veiculo_placa_norm ON core.veiculo USING btree (regexp_replace(upper(placa), '[^A-Z0-9]'::text, ''::text, 'g'::text));


--
-- Name: idx_cte_documento_cfop; Type: INDEX; Schema: cte; Owner: sergiomendes
--

CREATE INDEX idx_cte_documento_cfop ON cte.documento USING btree (cfop);


--
-- Name: idx_cte_documento_data_emissao; Type: INDEX; Schema: cte; Owner: sergiomendes
--

CREATE INDEX idx_cte_documento_data_emissao ON cte.documento USING btree (data_emissao);


--
-- Name: idx_cte_documento_destino; Type: INDEX; Schema: cte; Owner: sergiomendes
--

CREATE INDEX idx_cte_documento_destino ON cte.documento USING btree (id_municipio_destino);


--
-- Name: idx_cte_documento_origem; Type: INDEX; Schema: cte; Owner: sergiomendes
--

CREATE INDEX idx_cte_documento_origem ON cte.documento USING btree (id_municipio_origem);


--
-- Name: idx_cte_parte_pessoa; Type: INDEX; Schema: cte; Owner: sergiomendes
--

CREATE INDEX idx_cte_parte_pessoa ON cte.documento_parte USING btree (id_pessoa);


--
-- Name: idx_municipio_nome_norm; Type: INDEX; Schema: ibge; Owner: sergiomendes
--

CREATE INDEX idx_municipio_nome_norm ON ibge.municipio USING btree (nome_normalizado);


--
-- Name: endereco tgr_endereco_updated_at; Type: TRIGGER; Schema: core; Owner: sergiomendes
--

CREATE TRIGGER tgr_endereco_updated_at BEFORE UPDATE ON core.endereco FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: pessoa tgr_pessoa_updated_at; Type: TRIGGER; Schema: core; Owner: sergiomendes
--

CREATE TRIGGER tgr_pessoa_updated_at BEFORE UPDATE ON core.pessoa FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: veiculo tgr_veiculo_updated_at; Type: TRIGGER; Schema: core; Owner: sergiomendes
--

CREATE TRIGGER tgr_veiculo_updated_at BEFORE UPDATE ON core.veiculo FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: documento tgr_cte_documento_updated_at; Type: TRIGGER; Schema: cte; Owner: sergiomendes
--

CREATE TRIGGER tgr_cte_documento_updated_at BEFORE UPDATE ON cte.documento FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: municipio tgr_municipio_updated_at; Type: TRIGGER; Schema: ibge; Owner: sergiomendes
--

CREATE TRIGGER tgr_municipio_updated_at BEFORE UPDATE ON ibge.municipio FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: uf tgr_uf_updated_at; Type: TRIGGER; Schema: ibge; Owner: sergiomendes
--

CREATE TRIGGER tgr_uf_updated_at BEFORE UPDATE ON ibge.uf FOR EACH ROW EXECUTE FUNCTION ibge.trigger_set_updated_at();


--
-- Name: endereco endereco_id_municipio_fkey; Type: FK CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.endereco
    ADD CONSTRAINT endereco_id_municipio_fkey FOREIGN KEY (id_municipio) REFERENCES ibge.municipio(id_municipio) ON UPDATE CASCADE;


--
-- Name: endereco endereco_id_uf_fkey; Type: FK CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.endereco
    ADD CONSTRAINT endereco_id_uf_fkey FOREIGN KEY (id_uf) REFERENCES ibge.uf(id_uf) ON UPDATE CASCADE;


--
-- Name: pessoa_endereco pessoa_endereco_id_endereco_fkey; Type: FK CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa_endereco
    ADD CONSTRAINT pessoa_endereco_id_endereco_fkey FOREIGN KEY (id_endereco) REFERENCES core.endereco(id_endereco) ON DELETE CASCADE;


--
-- Name: pessoa_endereco pessoa_endereco_id_pessoa_fkey; Type: FK CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.pessoa_endereco
    ADD CONSTRAINT pessoa_endereco_id_pessoa_fkey FOREIGN KEY (id_pessoa) REFERENCES core.pessoa(id_pessoa) ON DELETE CASCADE;


--
-- Name: veiculo veiculo_id_uf_licenciamento_fkey; Type: FK CONSTRAINT; Schema: core; Owner: sergiomendes
--

ALTER TABLE ONLY core.veiculo
    ADD CONSTRAINT veiculo_id_uf_licenciamento_fkey FOREIGN KEY (id_uf_licenciamento) REFERENCES ibge.uf(id_uf);


--
-- Name: carga carga_id_cte_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.carga
    ADD CONSTRAINT carga_id_cte_fkey FOREIGN KEY (id_cte) REFERENCES cte.documento(id_cte) ON DELETE CASCADE;


--
-- Name: documento documento_id_municipio_destino_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento
    ADD CONSTRAINT documento_id_municipio_destino_fkey FOREIGN KEY (id_municipio_destino) REFERENCES ibge.municipio(id_municipio);


--
-- Name: documento documento_id_municipio_origem_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento
    ADD CONSTRAINT documento_id_municipio_origem_fkey FOREIGN KEY (id_municipio_origem) REFERENCES ibge.municipio(id_municipio);


--
-- Name: documento documento_id_veiculo_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento
    ADD CONSTRAINT documento_id_veiculo_fkey FOREIGN KEY (id_veiculo) REFERENCES core.veiculo(id_veiculo);


--
-- Name: documento_parte documento_parte_id_cte_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento_parte
    ADD CONSTRAINT documento_parte_id_cte_fkey FOREIGN KEY (id_cte) REFERENCES cte.documento(id_cte) ON DELETE CASCADE;


--
-- Name: documento_parte documento_parte_id_pessoa_fkey; Type: FK CONSTRAINT; Schema: cte; Owner: sergiomendes
--

ALTER TABLE ONLY cte.documento_parte
    ADD CONSTRAINT documento_parte_id_pessoa_fkey FOREIGN KEY (id_pessoa) REFERENCES core.pessoa(id_pessoa);


--
-- Name: municipio municipio_id_uf_fkey; Type: FK CONSTRAINT; Schema: ibge; Owner: sergiomendes
--

ALTER TABLE ONLY ibge.municipio
    ADD CONSTRAINT municipio_id_uf_fkey FOREIGN KEY (id_uf) REFERENCES ibge.uf(id_uf) ON UPDATE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict mm0hNvotUBV26UTrobBO2rrcjK6YAucZp8FHZvMkJHJv37IYLfUGfFHw66Me5r6

