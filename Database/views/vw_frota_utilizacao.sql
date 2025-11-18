
-- Views de Frota e Utilização - CORRIGIDAS
CREATE SCHEMA IF NOT EXISTS analytics;

-- 1. Rodagem Total
CREATE OR REPLACE VIEW analytics.vw_rodagem_total AS
SELECT 
    v.placa,
    v.modelo AS tipo,
    CAST(v.ano_fabricacao AS INTEGER) AS ano_fabricacao,
    COUNT(d.id_cte) AS total_viagens,
    COALESCE(SUM(d.quilometragem), 0) AS km_total,
    ROUND(COALESCE(AVG(d.quilometragem), 0), 2) AS km_medio_viagem
FROM core.veiculo v
LEFT JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE d.quilometragem > 0
GROUP BY v.placa, v.modelo, v.ano_fabricacao
ORDER BY km_total DESC;

-- 2. Distribuição de Viagens  
CREATE OR REPLACE VIEW analytics.vw_distribuicao_viagens AS
SELECT 
    v.placa,
    v.modelo AS tipo,
    TO_CHAR(d.data_emissao, 'YYYY-MM') AS mes_ano,
    COUNT(d.id_cte) AS total_viagens,
    COALESCE(SUM(d.quilometragem), 0) AS km_mes
FROM core.veiculo v
INNER JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE d.quilometragem > 0
GROUP BY v.placa, v.modelo, TO_CHAR(d.data_emissao, 'YYYY-MM')
ORDER BY v.placa, mes_ano DESC;

-- 3. Idade da Frota
CREATE OR REPLACE VIEW analytics.vw_idade_frota AS
SELECT 
    v.modelo AS tipo,
    COUNT(DISTINCT v.placa) AS total_veiculos,
    ROUND(AVG(EXTRACT(YEAR FROM CURRENT_DATE) - CAST(v.ano_fabricacao AS INTEGER)), 1) AS idade_media_anos
FROM core.veiculo v
WHERE v.ano_fabricacao IS NOT NULL
GROUP BY v.modelo
ORDER BY total_veiculos DESC;

-- 4. Tempo de Parada
CREATE OR REPLACE VIEW analytics.vw_tempo_parada AS
WITH viagens_ordenadas AS (
    SELECT 
        v.placa,
        v.modelo AS tipo,
        d.data_emissao,
        LAG(d.data_emissao) OVER (PARTITION BY v.placa ORDER BY d.data_emissao) AS data_anterior
    FROM core.veiculo v
    INNER JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
    WHERE d.quilometragem > 0
)
SELECT 
    placa,
    tipo,
    COUNT(*) AS total_intervalos,
    ROUND(AVG(EXTRACT(DAYS FROM (data_emissao - data_anterior))), 1) AS dias_parada_media
FROM viagens_ordenadas
WHERE data_anterior IS NOT NULL
GROUP BY placa, tipo
ORDER BY dias_parada_media;

-- 5. Veículos Uso Extremo
CREATE OR REPLACE VIEW analytics.vw_veiculos_uso_extremo AS
WITH uso_veiculos AS (
    SELECT 
        v.placa,
        v.modelo AS tipo,
        CAST(v.ano_fabricacao AS INTEGER) AS ano_fabricacao,
        COUNT(d.id_cte) AS total_viagens,
        COALESCE(SUM(d.quilometragem), 0) AS km_total,
        ROW_NUMBER() OVER (ORDER BY SUM(d.quilometragem) DESC) AS rank_maior,
        ROW_NUMBER() OVER (ORDER BY SUM(d.quilometragem) ASC) AS rank_menor
    FROM core.veiculo v
    INNER JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
    WHERE d.quilometragem > 0
    GROUP BY v.placa, v.modelo, v.ano_fabricacao
)
SELECT * FROM uso_veiculos
WHERE rank_maior <= 10 OR rank_menor <= 10
ORDER BY km_total DESC;

-- 6. Performance da Frota
CREATE OR REPLACE VIEW analytics.vw_performance_frota AS
SELECT 
    v.placa,
    v.modelo AS tipo,
    CAST(v.ano_fabricacao AS INTEGER) AS ano_fabricacao,
    COUNT(d.id_cte) AS total_viagens,
    COALESCE(SUM(d.quilometragem), 0) AS km_total,
    COALESCE(SUM(d.valor_frete), 0) AS faturamento_total,
    ROUND(COALESCE(SUM(d.valor_frete) / NULLIF(SUM(d.quilometragem), 0), 0), 2) AS receita_por_km
FROM core.veiculo v
LEFT JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE d.quilometragem > 0
GROUP BY v.placa, v.modelo, v.ano_fabricacao
ORDER BY faturamento_total DESC;

-- 7. Dashboard Frota
CREATE OR REPLACE VIEW analytics.vw_dashboard_frota AS
SELECT 
    COUNT(DISTINCT v.placa) AS total_veiculos,
    COUNT(DISTINCT d.id_cte) AS total_viagens,
    COALESCE(SUM(d.quilometragem), 0) AS km_total_frota,
    COALESCE(SUM(d.valor_frete), 0) AS faturamento_total
FROM core.veiculo v
LEFT JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE d.quilometragem > 0;
