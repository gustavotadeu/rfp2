-- SQL script to support multiple files per RFP
CREATE TABLE IF NOT EXISTS rfp_files (
    id SERIAL PRIMARY KEY,
    rfp_id INTEGER NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger function to update updated_at
CREATE OR REPLACE FUNCTION update_rfp_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call function on update
DROP TRIGGER IF EXISTS trigger_update_rfp_files_updated_at ON rfp_files;
CREATE TRIGGER trigger_update_rfp_files_updated_at
BEFORE UPDATE ON rfp_files
FOR EACH ROW
EXECUTE PROCEDURE update_rfp_files_updated_at();
