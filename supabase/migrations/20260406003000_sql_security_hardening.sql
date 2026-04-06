-- 20260406003000_sql_security_hardening.sql
-- Security hardening for SimHPC PostgreSQL functions and views

-- Harden update_updated_at_column
CREATE OR REPLACE FUNCTION public.update_updated_at_column() 
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$ 
BEGIN 
  NEW.updated_at = NOW(); 
  RETURN NEW; 
END; 
$$;

-- Harden update_notebook_entry_updated_at
CREATE OR REPLACE FUNCTION public.update_notebook_entry_updated_at()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- Secure Views: Respect RLS of querying user
CREATE OR REPLACE VIEW public.certificate_verification_view 
WITH (security_invoker = true) AS
SELECT c.id AS certificate_id, c.simulation_id, c.verification_hash, c.storage_url, c.created_at,
       s.hallucination_score, s.audit_result, s.status AS simulation_status
FROM certificates c JOIN simulations s ON s.id = c.simulation_id;

CREATE OR REPLACE VIEW public.simulation_history 
WITH (security_invoker = true) AS
SELECT id, user_id, job_id, scenario_name, status, result_summary, report_url, created_at FROM simulations;
