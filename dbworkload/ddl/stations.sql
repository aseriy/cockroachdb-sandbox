-- file: stations.sql

CREATE TABLE IF NOT EXISTS stations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region STRING NOT NULL,
    INDEX index_region (region)
);
