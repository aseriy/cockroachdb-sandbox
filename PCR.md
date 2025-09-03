## CockroachDB PCR Demo

## Setup

Deploy a Docker Swarm stacks:

```bash
docker stack deploy -c homogeneous.yml homogeneous
docker stack deploy -c async-cluster.yml async-cluster
```

`homogenous` will our primary cluster, and `async-cluster` is the standby.

## Primary Cluster

Login as `root`:

```bash
cockroach sql  --url "postgresql://root@ec2-3-17-142-130.us-east-2.compute.amazonaws.com:26257?options=-ccluster=system&sslmode=verify-full" --certs-dir=volumes/certs
```

Create a tenant/virtual cluster and start its SQL service.

```sql
-- 1) Create the virtual cluster (tenant) named 'main'
CREATE TENANT main;

-- 2) Start its SQL service so it can accept connections
ALTER TENANT main START SERVICE SHARED;

-- 3) Verify
SHOW VIRTUAL CLUSTERS;
```

Create a replication user and password:

```sql
CREATE USER replicator WITH PASSWORD 'R3plikatR';
```

Grant the REPLICATIONSOURCE privilege to your user:

```sql
GRANT SYSTEM REPLICATIONSOURCE TO replicator;
```


## Stanby Cluster

Login as `root`:

```bash
cockroach sql  --url "postgresql://root@ec2-3-17-142-130.us-east-2.compute.amazonaws.com:26290?options=-ccluster=system&sslmode=verify-full" --certs-dir=volumes/certs
```

```sql
SET CLUSTER SETTING kv.rangefeed.enabled = true;
```

```sql
SHOW VIRTUAL CLUSTERS;
```

Create a replication user and password:

```sql
CREATE USER replicator WITH PASSWORD 'R3pli1katR';
```

To observe the replication activity, your user will need admin privileges:

```sql
GRANT SYSTEM REPLICATIONDEST, MANAGEVIRTUALCLUSTER TO replicator;
```

## Start Replication

From the standby cluster:

```bash
cockroach encode-uri   "postgresql://replicator:R3pli1katR@ec2-3-17-142-130.us-east-2.compute.amazonaws.com:26257/defaultdb?options=-ccluster%3Dsystem&sslmode=verify-full"   --ca-cert volumes/certs/homogeneous/ca.crt   --inline
```

```sql
CREATE VIRTUAL CLUSTER main
FROM REPLICATION OF main
ON 'postgresql://replicator:R3pli1katR@ec2-3-17-142-130.us-east-2.compute.amazonaws.com:26257/defaultdb?options=-ccluster%3Dsystem&crdb_route=gateway&sslinline=true&sslmode=verify-full&sslrootcert=-----BEGIN+CERTIFICATE-----%0AMIIDJTCCAg2gAwIBAgIQHMXCE3k4XIl%2FBhDtScLaDzANBgkqhkiG9w0BAQsFADAr%0AMRIwEAYDVQQKEwlDb2Nrcm9hY2gxFTATBgNVBAMTDENvY2tyb2FjaCBDQTAeFw0y%0ANTA4MTAwMTQ3NThaFw0zNTA4MTkwMTQ3NThaMCsxEjAQBgNVBAoTCUNvY2tyb2Fj%0AaDEVMBMGA1UEAxMMQ29ja3JvYWNoIENBMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A%0AMIIBCgKCAQEAnQK36rcaLX2PbAosqPq4csxLR%2FpXHkxWFmnu2BM4PRnQgrk5PPra%0AF%2By8ueSO13FxhkeTNgLsTEWBXZm%2F66ibDsM3cLTh7mPKw%2FvEe47qX8QmlimFy3uE%0A07zTFU6GfF9RuuVb4KViCD%2FYnfDzUkV%2BTwEOsVFGwtykGnui4yWAC41WmIi0sWn7%0Aq3nHU1ImfpFIdHj4USJL%2F3dvwhGr8Z2mXBcD7LSD%2FugkKSCr9w9ZfawmL2GvmYDQ%0ABrlnNP84PAneRoebKlpiuXymBbxn6BjwtIxVJiHgwSR7BKbobiCz0o1Ent6cRkjc%0AJt3U9KmSieMGY33kVXgweiEA61evKhk81wIDAQABo0UwQzAOBgNVHQ8BAf8EBAMC%0AAuQwEgYDVR0TAQH%2FBAgwBgEB%2FwIBATAdBgNVHQ4EFgQUZQj89zragSipDofCP1uN%0A27Ns3BEwDQYJKoZIhvcNAQELBQADggEBAGJWwsyPPOVanT92l%2B369Za%2BHOF3CBND%0AjK4hpQcpi7W6l8Fg0pRj%2B6N%2BeQLOvM1UvgyxxNwctN2SnOF14MPsmOCL7EeIT2z7%0AfZQDNFu1sZQum4EKGHO5rOPsM6lmnFWhaaXRmrUvPkfZ8FzFFKDA30ZgPfmkdOwo%0A8XQOm51%2FcKX9ZW84fYroZj69L3dOdvw4BhHn%2BW4K%2BgOgxMMotT6rZg4Q1%2FilI6Zi%0A9E4kCX2gFCbBp1B4hHWw%2Fnc3zU0rWBUg8upm%2B%2BwXD2F22wwlxyownI82kRPiHqfi%0AsS3%2FWr9RkAqwku25KOpILPwQMbUiZt0GzY1TehjR1HX2Ek4xZr6%2B0IQ%3D%0A-----END+CERTIFICATE-----%0A';
```

To view all virtual clusters on the standby, run:

```sql
SHOW VIRTUAL CLUSTERS;
```

```sql
SHOW VIRTUAL CLUSTER main WITH REPLICATION STATUS; 
```

```sql
CREATE VIRTUAL CLUSTER main FROM REPLICATION OF main                                         
ON 'postgresql://replicator:R3pli1katR@ec2-3-17-142-130.us-east-2.compute.amazonaws.com:26257/defaultdb?options=-ccluster%3Dsystem&sslmode=verify-full&sslrootcert=/cockroach/certs/homogeneous/ca.crt&crdb_route=gateway';
```