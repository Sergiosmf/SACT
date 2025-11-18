-- ============================================================================
-- ATUALIZAÇÃO DA FUNÇÃO f_ingest_cte_json PARA INCLUIR ENDEREÇOS
-- ============================================================================
-- Data: 2025-11-13
-- Autor: Sistema SACT
-- Descrição: Adiciona inserção de endereços para remetente e destinatário
-- ============================================================================

CREATE OR REPLACE FUNCTION cte.f_ingest_cte_json(_payload jsonb)
RETURNS bigint
LANGUAGE plpgsql
AS $function$
DECLARE
  _id_cte BIGINT;
  _id_veiculo BIGINT;
  _id_mun_origem INTEGER;
  _id_mun_destino INTEGER;
  _data_emissao TIMESTAMPTZ;
  -- Partes
  _rem BIGINT; _dest BIGINT; _exp BIGINT; _rec BIGINT;
  -- Endereços das partes
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

  -- ========================================================================
  -- PARTES COM ENDEREÇOS
  -- ========================================================================
  
  -- Remetente
  _rem := core.f_upsert_pessoa(
           _payload #>> '{remetente,nome}',
           _payload #>> '{remetente,documento}',
           NULL,
           NULL,
           NULL);
  
  IF _rem IS NOT NULL THEN
    -- Inserir endereço se houver dados
    IF _payload #> '{remetente,endereco}' IS NOT NULL THEN
      _rem_end := core.f_upsert_endereco(
        _payload #>> '{remetente,endereco,xlgr}',
        _payload #>> '{remetente,endereco,nro}',
        NULL,  -- complemento
        _payload #>> '{remetente,endereco,xbairro}',
        _payload #>> '{remetente,endereco,cep}',
        _payload #>> '{remetente,endereco,xmun}',
        _payload #>> '{remetente,endereco,uf}'
      );
      
      -- Vincular pessoa ao endereço
      IF _rem_end IS NOT NULL THEN
        INSERT INTO core.pessoa_endereco (id_pessoa, id_endereco, tipo)
        VALUES (_rem, _rem_end, 'principal')
        ON CONFLICT (id_pessoa, id_endereco) DO NOTHING;
      END IF;
    END IF;
    
    -- Vincular remetente ao documento
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
    -- Inserir endereço se houver dados
    IF _payload #> '{destinatario,endereco}' IS NOT NULL THEN
      _dest_end := core.f_upsert_endereco(
        _payload #>> '{destinatario,endereco,xlgr}',
        _payload #>> '{destinatario,endereco,nro}',
        NULL,  -- complemento
        _payload #>> '{destinatario,endereco,xbairro}',
        _payload #>> '{destinatario,endereco,cep}',
        _payload #>> '{destinatario,endereco,xmun}',
        _payload #>> '{destinatario,endereco,uf}'
      );
      
      -- Vincular pessoa ao endereço
      IF _dest_end IS NOT NULL THEN
        INSERT INTO core.pessoa_endereco (id_pessoa, id_endereco, tipo)
        VALUES (_dest, _dest_end, 'principal')
        ON CONFLICT (id_pessoa, id_endereco) DO NOTHING;
      END IF;
    END IF;
    
    -- Vincular destinatário ao documento
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
    -- Inserir endereço se houver dados
    IF _payload #> '{expedidor,endereco}' IS NOT NULL THEN
      _exp_end := core.f_upsert_endereco(
        _payload #>> '{expedidor,endereco,xlgr}',
        _payload #>> '{expedidor,endereco,nro}',
        NULL,  -- complemento
        _payload #>> '{expedidor,endereco,xbairro}',
        _payload #>> '{expedidor,endereco,cep}',
        _payload #>> '{expedidor,endereco,xmun}',
        _payload #>> '{expedidor,endereco,uf}'
      );
      
      -- Vincular pessoa ao endereço
      IF _exp_end IS NOT NULL THEN
        INSERT INTO core.pessoa_endereco (id_pessoa, id_endereco, tipo)
        VALUES (_exp, _exp_end, 'principal')
        ON CONFLICT (id_pessoa, id_endereco) DO NOTHING;
      END IF;
    END IF;
    
    -- Vincular expedidor ao documento
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
    -- Inserir endereço se houver dados
    IF _payload #> '{recebedor,endereco}' IS NOT NULL THEN
      _rec_end := core.f_upsert_endereco(
        _payload #>> '{recebedor,endereco,xlgr}',
        _payload #>> '{recebedor,endereco,nro}',
        NULL,  -- complemento
        _payload #>> '{recebedor,endereco,xbairro}',
        _payload #>> '{recebedor,endereco,cep}',
        _payload #>> '{recebedor,endereco,xmun}',
        _payload #>> '{recebedor,endereco,uf}'
      );
      
      -- Vincular pessoa ao endereço
      IF _rec_end IS NOT NULL THEN
        INSERT INTO core.pessoa_endereco (id_pessoa, id_endereco, tipo)
        VALUES (_rec, _rec_end, 'principal')
        ON CONFLICT (id_pessoa, id_endereco) DO NOTHING;
      END IF;
    END IF;
    
    -- Vincular recebedor ao documento
    INSERT INTO cte.documento_parte (id_cte, tipo, id_pessoa)
    VALUES (_id_cte, 'recebedor', _rec)
    ON CONFLICT (id_cte, tipo) DO UPDATE SET id_pessoa = EXCLUDED.id_pessoa;
  END IF;

  RETURN _id_cte;
END $function$;

-- ============================================================================
-- COMENTÁRIO DA FUNÇÃO
-- ============================================================================
COMMENT ON FUNCTION cte.f_ingest_cte_json(jsonb) IS
'Insere ou atualiza CT-e completo a partir de JSON incluindo:
- Documento principal
- Carga
- Pessoas (remetente, destinatário, expedidor, recebedor)
- Endereços das pessoas
- Vínculos pessoa-endereco e documento-parte

Atualizado em 2025-11-13 para incluir inserção de endereços.';
