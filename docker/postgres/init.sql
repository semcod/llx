-- PostgreSQL initialization script for llx

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS llx;
CREATE SCHEMA IF NOT EXISTS logs;

-- Set default permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA llx GRANT ALL ON TABLES TO llx;
ALTER DEFAULT PRIVILEGES IN SCHEMA logs GRANT ALL ON TABLES TO llx;

-- Create tables for llx (if using PostgreSQL for storage)
-- This is optional - llx can work without a database

-- Example: API usage tracking
CREATE TABLE IF NOT EXISTS llx.api_usage (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),
    model_id VARCHAR(255),
    provider VARCHAR(100),
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10, 6),
    request_time_ms INTEGER,
    status VARCHAR(50),
    metadata JSONB
);

-- Example: Model performance metrics
CREATE TABLE IF NOT EXISTS llx.model_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_id VARCHAR(255),
    provider VARCHAR(100),
    avg_response_time_ms INTEGER,
    success_rate DECIMAL(5, 4),
    error_count INTEGER,
    total_requests INTEGER,
    cost_per_1k_tokens DECIMAL(10, 6)
);

-- Example: Project analysis cache
CREATE TABLE IF NOT EXISTS llx.project_analysis (
    id SERIAL PRIMARY KEY,
    project_path VARCHAR(500),
    file_hash VARCHAR(64),
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metrics JSONB,
    selected_model VARCHAR(255),
    selection_reasons JSONB,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Example: User preferences
CREATE TABLE IF NOT EXISTS llx.user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE,
    preferred_tier VARCHAR(50),
    budget_limit_usd DECIMAL(10, 2),
    preferred_providers TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON llx.api_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON llx.api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_model_id ON llx.api_usage(model_id);

CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON llx.model_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON llx.model_metrics(model_id);

CREATE INDEX IF NOT EXISTS idx_project_analysis_path ON llx.project_analysis(project_path);
CREATE INDEX IF NOT EXISTS idx_project_analysis_hash ON llx.project_analysis(file_hash);
CREATE INDEX IF NOT EXISTS idx_project_analysis_expires ON llx.project_analysis(expires_at);

-- Create trigger to update updated_at column
CREATE OR REPLACE FUNCTION llx.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON llx.user_preferences 
    FOR EACH ROW EXECUTE FUNCTION llx.update_updated_at_column();

-- Create view for usage statistics
CREATE OR REPLACE VIEW llx.usage_stats AS
SELECT 
    DATE(timestamp) as date,
    model_id,
    provider,
    COUNT(*) as total_requests,
    SUM(tokens_input) as total_input_tokens,
    SUM(tokens_output) as total_output_tokens,
    SUM(cost_usd) as total_cost,
    AVG(request_time_ms) as avg_response_time
FROM llx.api_usage
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp), model_id, provider
ORDER BY date DESC, total_requests DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA llx TO llx;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA llx TO llx;
GRANT SELECT ON llx.usage_stats TO llx;

-- Insert some default data if needed
-- This is optional and can be removed in production

COMMIT;
