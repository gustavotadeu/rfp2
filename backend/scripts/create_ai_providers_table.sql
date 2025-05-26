-- SQL script to create ai_providers table
CREATE TABLE IF NOT EXISTS ai_providers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  api_key VARCHAR(255) NOT NULL,
  is_selected BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Function to update the updated_at timestamp on row update
drop function if exists update_updated_at;
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function before updating
drop trigger if exists trigger_update_ai_providers_updated_at on ai_providers;
CREATE TRIGGER trigger_update_ai_providers_updated_at
BEFORE UPDATE ON ai_providers
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at();
