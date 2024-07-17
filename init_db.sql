CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledgebase (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1024)
);

CREATE INDEX idx_knowledgebase_embedding ON knowledgebase USING ivfflat (embedding vector_l2_ops) WITH (lists = 16);
