-- SQL script to create the ai_config table
CREATE TABLE IF NOT EXISTS ai_config (
  id SERIAL PRIMARY KEY,
  provider VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Function to update the updated_at timestamp on row update
drop function if exists update_timestamp;
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function before updating
DROP TRIGGER IF EXISTS set_ai_config_updated_at ON ai_config;
CREATE TRIGGER set_ai_config_updated_at
BEFORE UPDATE ON ai_config
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();
