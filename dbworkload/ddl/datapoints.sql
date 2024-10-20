-- file: datapoint.sql

CREATE TABLE IF NOT EXISTS datapoints (
    at TIMESTAMP,
    station UUID NOT NULL REFERENCES stations (id) ON DELETE CASCADE,
    param0 INT,
    param1 INT,
    param2 FLOAT,
    param3 FLOAT,
    param4 STRING,
    CONSTRAINT "primary" PRIMARY KEY (at ASC, station ASC)
)
