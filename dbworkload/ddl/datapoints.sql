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
);

CREATE INDEX IF NOT EXISTS datapoints_station_storing_rec_idx
    ON oltaptest.public.datapoints (station) STORING (param0, param1, param2, param3, param4); 

CREATE INDEX IF NOT EXISTS datapoints_at ON oltaptest.public.datapoints USING btree (at ASC);
CREATE INDEX IF NOT EXISTS datapoints_param0_rec_idx ON oltaptest.public.datapoints (param0);



