-- ============================================================================
-- VIEW: Operação de Transporte - Análise Completa
-- ============================================================================
-- Objetivo: Fornecer métricas essenciais sobre o volume e perfil das viagens
-- Criado em: 11/11/2025
-- ============================================================================

-- ============================================================================
-- 1. Total de CT-es emitidos por mês
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_ctes_por_mes AS
SELECT 
    EXTRACT(YEAR FROM data_emissao)::INTEGER as ano,
    EXTRACT(MONTH FROM data_emissao)::INTEGER as mes,
    TO_CHAR(data_emissao, 'YYYY-MM') as ano_mes,
    TO_CHAR(data_emissao, 'TMMonth/YYYY') as mes_nome,
    COUNT(*) as total_ctes,
    SUM(valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(valor_frete)::NUMERIC(10,2) as frete_medio,
    MIN(data_emissao) as primeira_emissao,
    MAX(data_emissao) as ultima_emissao
FROM cte.documento
WHERE data_emissao IS NOT NULL
GROUP BY 
    EXTRACT(YEAR FROM data_emissao)::INTEGER,
    EXTRACT(MONTH FROM data_emissao)::INTEGER,
    TO_CHAR(data_emissao, 'YYYY-MM'),
    TO_CHAR(data_emissao, 'TMMonth/YYYY')
ORDER BY ano DESC, mes DESC;

COMMENT ON VIEW analytics.vw_ctes_por_mes IS 
'Total de CT-es emitidos mensalmente com receita e frete médio';


-- ============================================================================
-- 2. Top 10 Municípios de Origem mais frequentes
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_top_origens AS
SELECT 
    m.nome as municipio,
    uf.sigla as uf,
    CONCAT(m.nome, ' - ', uf.sigla) as origem_completa,
    COUNT(d.id_cte) as total_viagens,
    SUM(d.valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as frete_medio,
    ROUND(AVG(d.quilometragem), 2) as distancia_media_km,
    COUNT(DISTINCT d.id_veiculo) as veiculos_distintos
FROM cte.documento d
INNER JOIN ibge.municipio m ON d.id_municipio_origem = m.id_municipio
INNER JOIN ibge.uf uf ON m.id_uf = uf.id_uf
WHERE d.id_municipio_origem IS NOT NULL
GROUP BY m.nome, uf.sigla
ORDER BY total_viagens DESC
LIMIT 10;

COMMENT ON VIEW analytics.vw_top_origens IS 
'Top 10 municípios de origem com maior volume de viagens';


-- ============================================================================
-- 3. Top 10 Municípios de Destino mais frequentes
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_top_destinos AS
SELECT 
    m.nome as municipio,
    uf.sigla as uf,
    CONCAT(m.nome, ' - ', uf.sigla) as destino_completo,
    COUNT(d.id_cte) as total_viagens,
    SUM(d.valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as frete_medio,
    ROUND(AVG(d.quilometragem), 2) as distancia_media_km,
    COUNT(DISTINCT d.id_veiculo) as veiculos_distintos
FROM cte.documento d
INNER JOIN ibge.municipio m ON d.id_municipio_destino = m.id_municipio
INNER JOIN ibge.uf uf ON m.id_uf = uf.id_uf
WHERE d.id_municipio_destino IS NOT NULL
GROUP BY m.nome, uf.sigla
ORDER BY total_viagens DESC
LIMIT 10;

COMMENT ON VIEW analytics.vw_top_destinos IS 
'Top 10 municípios de destino com maior volume de viagens';


-- ============================================================================
-- 4. Distância média percorrida por viagem
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_distancia_media AS
SELECT 
    COUNT(*) as total_viagens_com_km,
    ROUND(AVG(quilometragem)::NUMERIC, 2) as distancia_media_km,
    ROUND(MIN(quilometragem)::NUMERIC, 2) as distancia_minima_km,
    ROUND(MAX(quilometragem)::NUMERIC, 2) as distancia_maxima_km,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY quilometragem)::NUMERIC, 2) as mediana_km,
    ROUND(STDDEV(quilometragem)::NUMERIC, 2) as desvio_padrao_km,
    -- Classificação por faixas de distância
    SUM(CASE WHEN quilometragem <= 100 THEN 1 ELSE 0 END) as ate_100km,
    SUM(CASE WHEN quilometragem > 100 AND quilometragem <= 300 THEN 1 ELSE 0 END) as de_101_a_300km,
    SUM(CASE WHEN quilometragem > 300 AND quilometragem <= 500 THEN 1 ELSE 0 END) as de_301_a_500km,
    SUM(CASE WHEN quilometragem > 500 AND quilometragem <= 1000 THEN 1 ELSE 0 END) as de_501_a_1000km,
    SUM(CASE WHEN quilometragem > 1000 THEN 1 ELSE 0 END) as acima_1000km
FROM cte.documento
WHERE quilometragem > 0;

COMMENT ON VIEW analytics.vw_distancia_media IS 
'Análise estatística da distância percorrida por viagem';


-- ============================================================================
-- 5. Número de viagens por veículo
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_viagens_por_veiculo AS
SELECT 
    v.placa,
    COUNT(d.id_cte) as total_viagens,
    SUM(d.valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as frete_medio_por_viagem,
    ROUND(AVG(d.quilometragem)::NUMERIC, 2) as km_medio_por_viagem,
    SUM(d.quilometragem)::NUMERIC(12,2) as km_total_percorrido,
    MIN(d.data_emissao) as primeira_viagem,
    MAX(d.data_emissao) as ultima_viagem,
    -- Classificação de performance
    CASE 
        WHEN COUNT(d.id_cte) >= 100 THEN '🔥 MUITO ATIVO'
        WHEN COUNT(d.id_cte) >= 50 THEN '✅ ATIVO'
        WHEN COUNT(d.id_cte) >= 20 THEN '⚠️ MODERADO'
        ELSE '💤 BAIXA ATIVIDADE'
    END as classificacao
FROM core.veiculo v
INNER JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE v.placa IS NOT NULL
GROUP BY v.placa
ORDER BY total_viagens DESC;

COMMENT ON VIEW analytics.vw_viagens_por_veiculo IS 
'Número de viagens e performance de cada veículo';


-- ============================================================================
-- 6. Produto predominante mais transportado
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_produtos_predominantes AS
SELECT 
    COALESCE(c.produto_predominante, 'NÃO INFORMADO') as produto,
    COUNT(DISTINCT d.id_cte) as total_ctes,
    SUM(c.quantidade)::NUMERIC(15,2) as quantidade_total,
    c.unidade_medida,
    SUM(c.peso)::NUMERIC(15,2) as peso_total_kg,
    AVG(c.peso)::NUMERIC(10,2) as peso_medio_kg,
    SUM(d.valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as frete_medio,
    -- Receita por kg (quando disponível)
    CASE 
        WHEN SUM(c.peso) > 0 
        THEN ROUND(SUM(d.valor_frete) / SUM(c.peso), 2)
        ELSE 0 
    END as receita_por_kg,
    -- Classificação
    CASE 
        WHEN COUNT(DISTINCT d.id_cte) >= 100 THEN '⭐ TOP PRODUTO'
        WHEN COUNT(DISTINCT d.id_cte) >= 50 THEN '✅ REGULAR'
        WHEN COUNT(DISTINCT d.id_cte) >= 20 THEN '⚠️ OCASIONAL'
        ELSE '💤 RARO'
    END as classificacao
FROM cte.documento d
LEFT JOIN cte.carga c ON d.id_cte = c.id_cte
GROUP BY c.produto_predominante, c.unidade_medida
HAVING COUNT(DISTINCT d.id_cte) >= 1
ORDER BY total_ctes DESC;

COMMENT ON VIEW analytics.vw_produtos_predominantes IS 
'Produtos predominantes transportados com volume e receita';


-- ============================================================================
-- 7. Taxa média de frete por quilômetro
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_taxa_frete_km AS
SELECT 
    COUNT(*) as total_viagens,
    -- Taxa média geral
    ROUND(AVG(valor_frete / NULLIF(quilometragem, 0))::NUMERIC, 2) as taxa_media_por_km,
    ROUND(MIN(valor_frete / NULLIF(quilometragem, 0))::NUMERIC, 2) as taxa_minima_por_km,
    ROUND(MAX(valor_frete / NULLIF(quilometragem, 0))::NUMERIC, 2) as taxa_maxima_por_km,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_frete / NULLIF(quilometragem, 0))::NUMERIC, 2) as taxa_mediana_por_km,
    -- Por faixa de distância
    ROUND(AVG(CASE WHEN quilometragem <= 100 THEN valor_frete / quilometragem END)::NUMERIC, 2) as taxa_ate_100km,
    ROUND(AVG(CASE WHEN quilometragem > 100 AND quilometragem <= 300 THEN valor_frete / quilometragem END)::NUMERIC, 2) as taxa_101_300km,
    ROUND(AVG(CASE WHEN quilometragem > 300 AND quilometragem <= 500 THEN valor_frete / quilometragem END)::NUMERIC, 2) as taxa_301_500km,
    ROUND(AVG(CASE WHEN quilometragem > 500 AND quilometragem <= 1000 THEN valor_frete / quilometragem END)::NUMERIC, 2) as taxa_501_1000km,
    ROUND(AVG(CASE WHEN quilometragem > 1000 THEN valor_frete / quilometragem END)::NUMERIC, 2) as taxa_acima_1000km
FROM cte.documento
WHERE quilometragem > 0 AND valor_frete > 0;

COMMENT ON VIEW analytics.vw_taxa_frete_km IS 
'Taxa média de frete por quilômetro segmentada por distância';


-- ============================================================================
-- 8. Dashboard Resumo - Todas as métricas principais
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_dashboard_operacao AS
SELECT 
    -- Métricas gerais
    (SELECT COUNT(*) FROM cte.documento) as total_ctes,
    (SELECT COUNT(DISTINCT id_veiculo) FROM cte.documento WHERE id_veiculo IS NOT NULL) as total_veiculos,
    (SELECT COUNT(DISTINCT id_municipio_origem) FROM cte.documento WHERE id_municipio_origem IS NOT NULL) as total_origens,
    (SELECT COUNT(DISTINCT id_municipio_destino) FROM cte.documento WHERE id_municipio_destino IS NOT NULL) as total_destinos,
    
    -- Métricas financeiras
    (SELECT SUM(valor_frete)::NUMERIC(15,2) FROM cte.documento) as receita_total,
    (SELECT AVG(valor_frete)::NUMERIC(10,2) FROM cte.documento) as frete_medio,
    
    -- Métricas de distância
    (SELECT ROUND(AVG(quilometragem)::NUMERIC, 2) FROM cte.documento WHERE quilometragem > 0) as km_medio,
    (SELECT SUM(quilometragem)::NUMERIC(15,2) FROM cte.documento WHERE quilometragem > 0) as km_total,
    
    -- Taxa de frete
    (SELECT ROUND(AVG(valor_frete / NULLIF(quilometragem, 0))::NUMERIC, 2) 
     FROM cte.documento WHERE quilometragem > 0 AND valor_frete > 0) as taxa_media_km,
    
    -- Período
    (SELECT MIN(data_emissao) FROM cte.documento) as primeira_data,
    (SELECT MAX(data_emissao) FROM cte.documento) as ultima_data,
    
    -- Produto mais transportado
    (SELECT produto_predominante 
     FROM cte.carga 
     WHERE produto_predominante IS NOT NULL
     GROUP BY produto_predominante 
     ORDER BY COUNT(*) DESC 
     LIMIT 1) as produto_mais_transportado;

COMMENT ON VIEW analytics.vw_dashboard_operacao IS 
'Dashboard resumo com todas as principais métricas de operação de transporte';
