-- ============================================================================
-- VIEW: Rentabilidade e Custos - Análise Financeira Completa
-- ============================================================================
-- Objetivo: Medir desempenho financeiro da operação de transporte
-- Criado em: 11/11/2025
-- ============================================================================

-- ============================================================================
-- 1. Receita total de frete por mês
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_receita_mensal AS
WITH receita_base AS (
    SELECT 
        EXTRACT(YEAR FROM data_emissao)::INTEGER as ano,
        EXTRACT(MONTH FROM data_emissao)::INTEGER as mes,
        TO_CHAR(data_emissao, 'YYYY-MM') as ano_mes,
        TO_CHAR(data_emissao, 'TMMonth/YYYY') as mes_nome,
        
        -- Receitas
        COUNT(*) as total_ctes,
        SUM(valor_frete)::NUMERIC(15,2) as receita_total,
        AVG(valor_frete)::NUMERIC(10,2) as receita_media,
        MIN(valor_frete)::NUMERIC(10,2) as receita_minima,
        MAX(valor_frete)::NUMERIC(10,2) as receita_maxima,
        
        -- Quilometragem
        SUM(quilometragem)::NUMERIC(15,2) as km_total,
        AVG(quilometragem)::NUMERIC(10,2) as km_medio,
        
        -- Receita por KM
        CASE 
            WHEN SUM(quilometragem) > 0 
            THEN ROUND((SUM(valor_frete) / SUM(quilometragem))::NUMERIC, 2)
            ELSE 0
        END as receita_por_km
        
    FROM cte.documento
    WHERE data_emissao IS NOT NULL
    GROUP BY 
        EXTRACT(YEAR FROM data_emissao)::INTEGER,
        EXTRACT(MONTH FROM data_emissao)::INTEGER,
        TO_CHAR(data_emissao, 'YYYY-MM'),
        TO_CHAR(data_emissao, 'TMMonth/YYYY')
)
SELECT 
    *,
    LAG(receita_total) OVER (ORDER BY ano, mes) as receita_mes_anterior
FROM receita_base
ORDER BY ano DESC, mes DESC;

COMMENT ON VIEW analytics.vw_receita_mensal IS 
'Receita total de frete por mês com métricas de performance';


-- ============================================================================
-- 2. Ticket médio por viagem
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_ticket_medio AS
SELECT 
    -- Ticket médio geral
    COUNT(*) as total_viagens,
    SUM(valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(valor_frete)::NUMERIC(10,2) as ticket_medio,
    
    -- Estatísticas
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_frete)::NUMERIC(10,2) as ticket_mediano,
    MIN(valor_frete)::NUMERIC(10,2) as ticket_minimo,
    MAX(valor_frete)::NUMERIC(10,2) as ticket_maximo,
    STDDEV(valor_frete)::NUMERIC(10,2) as desvio_padrao,
    
    -- Distribuição por faixas de valor
    SUM(CASE WHEN valor_frete <= 100 THEN 1 ELSE 0 END) as ate_100,
    SUM(CASE WHEN valor_frete > 100 AND valor_frete <= 500 THEN 1 ELSE 0 END) as de_101_a_500,
    SUM(CASE WHEN valor_frete > 500 AND valor_frete <= 1000 THEN 1 ELSE 0 END) as de_501_a_1000,
    SUM(CASE WHEN valor_frete > 1000 AND valor_frete <= 3000 THEN 1 ELSE 0 END) as de_1001_a_3000,
    SUM(CASE WHEN valor_frete > 3000 THEN 1 ELSE 0 END) as acima_3000,
    
    -- Ticket médio por faixa de distância
    AVG(CASE WHEN quilometragem <= 100 THEN valor_frete END)::NUMERIC(10,2) as ticket_medio_ate_100km,
    AVG(CASE WHEN quilometragem > 100 AND quilometragem <= 300 THEN valor_frete END)::NUMERIC(10,2) as ticket_medio_101_300km,
    AVG(CASE WHEN quilometragem > 300 AND quilometragem <= 500 THEN valor_frete END)::NUMERIC(10,2) as ticket_medio_301_500km,
    AVG(CASE WHEN quilometragem > 500 AND quilometragem <= 1000 THEN valor_frete END)::NUMERIC(10,2) as ticket_medio_501_1000km,
    AVG(CASE WHEN quilometragem > 1000 THEN valor_frete END)::NUMERIC(10,2) as ticket_medio_acima_1000km

FROM cte.documento
WHERE valor_frete > 0;

COMMENT ON VIEW analytics.vw_ticket_medio IS 
'Análise do ticket médio por viagem com distribuição por faixas';


-- ============================================================================
-- 3. Margem estimada por veículo (receita - custo operacional/km)
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_margem_veiculo AS
SELECT 
    v.placa,
    
    -- Receitas
    COUNT(d.id_cte) as total_viagens,
    SUM(d.valor_frete)::NUMERIC(15,2) as receita_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as receita_media,
    
    -- Quilometragem
    SUM(d.quilometragem)::NUMERIC(15,2) as km_total,
    AVG(d.quilometragem)::NUMERIC(10,2) as km_medio,
    
    -- Custo estimado (R$ 2.50/km como padrão - pode ser ajustado)
    (SUM(d.quilometragem) * 2.50)::NUMERIC(15,2) as custo_estimado,
    
    -- Margem bruta
    (SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50))::NUMERIC(15,2) as margem_bruta,
    
    -- Margem percentual
    CASE 
        WHEN SUM(d.valor_frete) > 0 
        THEN ROUND(((SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50)) / SUM(d.valor_frete) * 100)::NUMERIC, 2)
        ELSE 0
    END as margem_percentual,
    
    -- Receita por KM
    CASE 
        WHEN SUM(d.quilometragem) > 0 
        THEN ROUND((SUM(d.valor_frete) / SUM(d.quilometragem))::NUMERIC, 2)
        ELSE 0
    END as receita_por_km,
    
    -- Classificação de rentabilidade
    CASE 
        WHEN SUM(d.valor_frete) > 0 AND ((SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50)) / SUM(d.valor_frete) * 100) >= 40 THEN '🔥 MUITO LUCRATIVO'
        WHEN SUM(d.valor_frete) > 0 AND ((SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50)) / SUM(d.valor_frete) * 100) >= 25 THEN '✅ LUCRATIVO'
        WHEN SUM(d.valor_frete) > 0 AND ((SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50)) / SUM(d.valor_frete) * 100) >= 10 THEN '⚠️ MARGEM BAIXA'
        WHEN SUM(d.valor_frete) > 0 AND ((SUM(d.valor_frete) - (SUM(d.quilometragem) * 2.50)) / SUM(d.valor_frete) * 100) >= 0 THEN '🔧 POUCO LUCRATIVO'
        ELSE '❌ PREJUÍZO'
    END as classificacao_rentabilidade,
    
    -- Período
    MIN(d.data_emissao) as primeira_viagem,
    MAX(d.data_emissao) as ultima_viagem

FROM core.veiculo v
INNER JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE v.placa IS NOT NULL
GROUP BY v.placa
ORDER BY margem_bruta DESC;

COMMENT ON VIEW analytics.vw_margem_veiculo IS 
'Margem estimada por veículo considerando custo operacional de R$ 2.50/km';


-- ============================================================================
-- 4. Faturamento por cliente (remetente)
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_faturamento_remetente AS
SELECT 
    p.id_pessoa,
    p.nome as cliente,
    p.cpf_cnpj as documento,
    
    -- Métricas de faturamento
    COUNT(DISTINCT d.id_cte) as total_ctes,
    SUM(d.valor_frete)::NUMERIC(15,2) as faturamento_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as ticket_medio,
    MIN(d.valor_frete)::NUMERIC(10,2) as menor_frete,
    MAX(d.valor_frete)::NUMERIC(10,2) as maior_frete,
    
    -- Quilometragem
    SUM(d.quilometragem)::NUMERIC(15,2) as km_total,
    AVG(d.quilometragem)::NUMERIC(10,2) as km_medio,
    
    -- Frequência
    MIN(d.data_emissao) as primeira_transacao,
    MAX(d.data_emissao) as ultima_transacao,
    
    -- Classificação
    CASE 
        WHEN COUNT(DISTINCT d.id_cte) >= 100 THEN '⭐ VIP'
        WHEN COUNT(DISTINCT d.id_cte) >= 50 THEN '🔥 PREMIUM'
        WHEN COUNT(DISTINCT d.id_cte) >= 20 THEN '✅ REGULAR'
        WHEN COUNT(DISTINCT d.id_cte) >= 5 THEN '⚠️ OCASIONAL'
        ELSE '💤 ESPORÁDICO'
    END as classificacao

FROM core.pessoa p
INNER JOIN cte.documento_parte dp ON p.id_pessoa = dp.id_pessoa
INNER JOIN cte.documento d ON dp.id_cte = d.id_cte
WHERE dp.tipo = 'remetente'
GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj
HAVING COUNT(DISTINCT d.id_cte) >= 1
ORDER BY faturamento_total DESC;

COMMENT ON VIEW analytics.vw_faturamento_remetente IS 
'Faturamento por cliente remetente com classificação';


-- ============================================================================
-- 5. Faturamento por cliente (destinatário)
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_faturamento_destinatario AS
SELECT 
    p.id_pessoa,
    p.nome as cliente,
    p.cpf_cnpj as documento,
    
    -- Métricas de faturamento
    COUNT(DISTINCT d.id_cte) as total_ctes,
    SUM(d.valor_frete)::NUMERIC(15,2) as faturamento_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as ticket_medio,
    MIN(d.valor_frete)::NUMERIC(10,2) as menor_frete,
    MAX(d.valor_frete)::NUMERIC(10,2) as maior_frete,
    
    -- Quilometragem
    SUM(d.quilometragem)::NUMERIC(15,2) as km_total,
    AVG(d.quilometragem)::NUMERIC(10,2) as km_medio,
    
    -- Frequência
    MIN(d.data_emissao) as primeira_transacao,
    MAX(d.data_emissao) as ultima_transacao,
    
    -- Classificação
    CASE 
        WHEN COUNT(DISTINCT d.id_cte) >= 100 THEN '⭐ VIP'
        WHEN COUNT(DISTINCT d.id_cte) >= 50 THEN '🔥 PREMIUM'
        WHEN COUNT(DISTINCT d.id_cte) >= 20 THEN '✅ REGULAR'
        WHEN COUNT(DISTINCT d.id_cte) >= 5 THEN '⚠️ OCASIONAL'
        ELSE '💤 ESPORÁDICO'
    END as classificacao

FROM core.pessoa p
INNER JOIN cte.documento_parte dp ON p.id_pessoa = dp.id_pessoa
INNER JOIN cte.documento d ON dp.id_cte = d.id_cte
WHERE dp.tipo = 'destinatario'
GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj
HAVING COUNT(DISTINCT d.id_cte) >= 1
ORDER BY faturamento_total DESC;

COMMENT ON VIEW analytics.vw_faturamento_destinatario IS 
'Faturamento por cliente destinatário com classificação';


-- ============================================================================
-- 6. Ranking dos principais clientes (top 20 remetentes)
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_ranking_clientes AS
SELECT 
    p.id_pessoa,
    p.nome as cliente,
    p.cpf_cnpj as documento,
    dp.tipo as tipo_cliente,
    
    -- Métricas
    COUNT(DISTINCT d.id_cte) as total_ctes,
    SUM(d.valor_frete)::NUMERIC(15,2) as faturamento_total,
    AVG(d.valor_frete)::NUMERIC(10,2) as ticket_medio,
    
    -- Participação no faturamento total
    ROUND((SUM(d.valor_frete) / (SELECT SUM(valor_frete) FROM cte.documento) * 100)::NUMERIC, 2) as participacao_percentual,
    
    -- Quilometragem
    SUM(d.quilometragem)::NUMERIC(15,2) as km_total,
    
    -- Período
    MIN(d.data_emissao) as primeira_transacao,
    MAX(d.data_emissao) as ultima_transacao,
    
    -- Classificação
    CASE 
        WHEN COUNT(DISTINCT d.id_cte) >= 100 THEN '⭐ VIP'
        WHEN COUNT(DISTINCT d.id_cte) >= 50 THEN '🔥 PREMIUM'
        WHEN COUNT(DISTINCT d.id_cte) >= 20 THEN '✅ REGULAR'
        WHEN COUNT(DISTINCT d.id_cte) >= 5 THEN '⚠️ OCASIONAL'
        ELSE '💤 ESPORÁDICO'
    END as classificacao,
    
    -- Ranking
    ROW_NUMBER() OVER (ORDER BY SUM(d.valor_frete) DESC) as ranking

FROM core.pessoa p
INNER JOIN cte.documento_parte dp ON p.id_pessoa = dp.id_pessoa
INNER JOIN cte.documento d ON dp.id_cte = d.id_cte
WHERE dp.tipo = 'remetente'  -- Foco nos remetentes
GROUP BY p.id_pessoa, p.nome, p.cpf_cnpj, dp.tipo
HAVING COUNT(DISTINCT d.id_cte) >= 1
ORDER BY faturamento_total DESC
LIMIT 20;

COMMENT ON VIEW analytics.vw_ranking_clientes IS 
'Ranking dos top 20 clientes por faturamento total';


-- ============================================================================
-- 7. Dashboard Resumo Financeiro
-- ============================================================================
CREATE OR REPLACE VIEW analytics.vw_dashboard_financeiro AS
SELECT 
    -- Receitas
    (SELECT SUM(valor_frete)::NUMERIC(15,2) FROM cte.documento) as receita_total,
    (SELECT AVG(valor_frete)::NUMERIC(10,2) FROM cte.documento) as ticket_medio,
    (SELECT COUNT(*) FROM cte.documento) as total_ctes,
    
    -- Custos estimados (R$ 2.50/km)
    (SELECT SUM(quilometragem)::NUMERIC(15,2) * 2.50 FROM cte.documento WHERE quilometragem > 0) as custo_estimado_total,
    
    -- Margem bruta
    (SELECT (SUM(valor_frete) - (SUM(quilometragem) * 2.50))::NUMERIC(15,2) 
     FROM cte.documento WHERE quilometragem > 0) as margem_bruta_total,
    
    -- Margem percentual
    (SELECT ROUND(((SUM(valor_frete) - (SUM(quilometragem) * 2.50)) / NULLIF(SUM(valor_frete), 0) * 100)::NUMERIC, 2)
     FROM cte.documento WHERE quilometragem > 0 AND valor_frete > 0) as margem_percentual,
    
    -- Clientes
    (SELECT COUNT(DISTINCT id_pessoa) 
     FROM cte.documento_parte 
     WHERE tipo = 'remetente') as total_clientes_remetentes,
     
    (SELECT COUNT(DISTINCT id_pessoa) 
     FROM cte.documento_parte 
     WHERE tipo = 'destinatario') as total_clientes_destinatarios,
    
    -- Receita média mensal
    (SELECT AVG(receita_mensal)::NUMERIC(15,2)
     FROM (
         SELECT SUM(valor_frete) as receita_mensal
         FROM cte.documento
         WHERE data_emissao IS NOT NULL
         GROUP BY EXTRACT(YEAR FROM data_emissao), EXTRACT(MONTH FROM data_emissao)
     ) sub) as receita_media_mensal,
    
    -- Melhor mês
    (SELECT TO_CHAR(data_emissao, 'TMMonth/YYYY')
     FROM cte.documento
     WHERE data_emissao IS NOT NULL
     GROUP BY EXTRACT(YEAR FROM data_emissao), EXTRACT(MONTH FROM data_emissao), TO_CHAR(data_emissao, 'TMMonth/YYYY')
     ORDER BY SUM(valor_frete) DESC
     LIMIT 1) as melhor_mes;

COMMENT ON VIEW analytics.vw_dashboard_financeiro IS 
'Dashboard resumo com principais indicadores financeiros';
