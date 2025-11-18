-- Teste: Criando apenas uma view simples primeiro
CREATE OR REPLACE VIEW analytics.vw_rodagem_total AS
SELECT 
    v.placa,
    v.modelo AS tipo,
    CAST(v.ano_fabricacao AS INTEGER) AS ano_fabricacao,
    COUNT(d.id_cte) AS total_viagens,
    COALESCE(SUM(d.quilometragem), 0) AS km_total
FROM 
    core.veiculo v
    LEFT JOIN cte.documento d ON v.id_veiculo = d.id_veiculo
WHERE 
    d.quilometragem IS NOT NULL
    AND d.quilometragem > 0
GROUP BY 
    v.placa, v.modelo, v.ano_fabricacao
ORDER BY 
    km_total DESC;
