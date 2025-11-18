-- Script para remover todas as views analíticas do banco de dados
-- Executar este script para limpar todas as views antes da reestruturação

-- Dropar views do schema public
DROP VIEW IF EXISTS public.vw_dashboard_executivo CASCADE;

-- Dropar views do schema core
DROP VIEW IF EXISTS core.vw_cte_resumo CASCADE;
DROP VIEW IF EXISTS core.vw_analise_rotas CASCADE;
DROP VIEW IF EXISTS core.vw_ranking_produtos CASCADE;
DROP VIEW IF EXISTS core.vw_eficiencia_logistica CASCADE;
DROP VIEW IF EXISTS core.vw_rendimento_caminhoes_mensal CASCADE;

-- Mensagem de confirmação
SELECT 'Todas as views analíticas foram removidas com sucesso!' as resultado;
