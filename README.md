# Overview

The purpose of a SQL database is to enable applications manage data organized as a collection of tables consisting of columns and rows, or records. Data management operations include:

- creating new records by inserting them into tables
- updating records that already exist
- searching for and retrieving the record(s) containing specific data from a single table or across multiple tables
- deleting records

Every database engine is capable of doing these basic operations, but none is equally good at all of them. Since the de-monolithication of the software, applications gravitate to performing a narrow set of business tasks, gravitating toward generating transaction or analytical load. It is then reasonable for a database to focus on optimizing its performance to align with the purpose of the application it serves.

A transactional workload is a workload typically identified by a database receiving large number of small, simple operations by multiple users that create, modify and delete records. One or more such operations executed as a single logical transaction. Typically, online transaction processing, or OLTP, applications drive this type of workloads, and are the system of record, the source of truth in many businesses. A database most suitable for a OLTP application should be capable of serving a lot of requests simultaneous and persist the requested data modification to the physical store as quickly as possible. In other words, OLTP database is a high I/O throughput database, while the CPU and RAM requirements are less important.

On the contrary, analytical workloads are characterized by complex queries running on large data sets. Unlike transactional workloads, they are run less frequently but conduct in-depth data analyses. The applications that leverage this type of database queries are referred to as online analytical processing, or OLAP. A database best suitable for the OLAP is the one that can load and manipulate a vest amount of data in memory. That translates into prioritizing CPU and RAM.

While the above is an overly simplified distinction, it conceptually shows why the organizations endure the infrastructure complexities, and thus cost, associated with multiple databases storing the same data for different purposes, and the pipelines to keep all of them in synch.

CockroachDB was designed for heavy transactional workloads, first and foremost.

1. Every node in the cluster is a gateway node, meaning every node can serve client connections, which maximizes the total number of application transactions can be performemd in parallel.
2. Underlying the SQL structure (tables, rows, indices, etc.) is a continguous key-value space divided into ranges. These ranges are evenly distributed among all the cluster nodes. With the database schema designed with this in mind, the cluster nodes will be evenly engaged by the incoming transactions, maximizing the cluster resources and therefore the throughput and minimizing latency.

However, while the distributed architecture make CRDB the best choice for transactions workloads, it also makes a poor one for the analytics. Or does it? In this article, I'm going to disprove this perception and demonstrate how leveraging multi-region feature of CockroachDB can enable handling both transactiona and analytical workloads loads within the same CRDB cluster.


# Background

Nodes in a CRDB cluster can be grouped in to regions. While the cluster nodes communicate across the region boundaries, CRDB enable defining:

- the replication factor (the number of replicas for each range)
- the number voting (participating in commiting a write) and non-voting replicas
- in which region or regions the voting and non-voting replicas are located

In my experiment I defined two regions, `oltp` and `olap` with `oltp` being the `PRIMARY REGION`, and set all the tables to `LOCALITY REGIONAL BY TABLE`:

There are two tables in the database:

```sql
root@localhost:26259/oltaptest> show create stations;                                                                                            
  table_name |                  create_statement
-------------+-----------------------------------------------------
  stations   | CREATE TABLE public.stations (
             |     id UUID NOT NULL DEFAULT gen_random_uuid(),
             |     region STRING NOT NULL,
             |     CONSTRAINT stations_pkey PRIMARY KEY (id ASC),
             |     INDEX index_region (region ASC)
             | ) LOCALITY REGIONAL BY TABLE IN PRIMARY REGION
(1 row)
```

```sql
root@localhost:26259/oltaptest> show create datapoints;                                                                                          
  table_name |                   create_statement
-------------+-----------------------------------------------------
  datapoints | CREATE TABLE public.datapoints (
             |     at TIMESTAMP NOT NULL,
             |     station UUID NOT NULL,
             |     param0 INT8 NULL,
             |     param1 INT8 NULL,
             |     param2 FLOAT8 NULL,
             |     param3 FLOAT8 NULL,
             |     param4 STRING NULL,
             |     CONSTRAINT "primary" PRIMARY KEY (at ASC, station ASC),
             |     CONSTRAINT datapoints_station_fkey
             |     FOREIGN KEY (station) REFERENCES public.stations(id)
             |     ON DELETE CASCADE NOT VALID,
             |     INDEX datapoints_at (at ASC),
             |     INDEX datapoints_param0_rec_idx (param0 ASC),
             |     INDEX datapoints_station_storing_rec_idx (station ASC)
             |     STORING (param0, param1, param2, param3, param4)
             | ) LOCALITY REGIONAL BY TABLE IN PRIMARY REGION
(1 row)
```


```sql
ALTER DATABASE oltaptest SET PRIMARY REGION "oltp";
ALTER DATABASE oltaptest ADD region 'olap';
ALTER TABLE stations SET LOCALITY REGIONAL BY TABLE;
ALTER TABLE datapoints SET LOCALITY REGIONAL BY TABLE;
```

I then further tweaked the `ZONE CONFIGURATION` for my database to:

```sql
root@localhost:26259/oltaptest> SHOW ZONE CONFIGURATION FROM DATABASE oltaptest;                                                                 
        target       |                     raw_config_sql
---------------------+----------------------------------------------------------
  DATABASE oltaptest | ALTER DATABASE oltaptest CONFIGURE ZONE USING
                     |     range_min_bytes = 134217728,
                     |     range_max_bytes = 536870912,
                     |     gc.ttlseconds = 14400,
                     |     num_replicas = 4,
                     |     num_voters = 3,
                     |     constraints = '{+region=olap: 1, +region=oltp: 1}',
                     |     voter_constraints = '[+region=oltp]',
                     |     lease_preferences = '[[+region=oltp]]'
(1 row)
```

There are total of four replicas, of which three are voting and must be in the `oltp` region, including the lease holder. This means that if writes are done via a gate node in the `oltp` region, committing such write will be completed within the `oltp` region. The fourth replicas will be placed in the `olap` region, and will be receiving all the updates as a follower.

As the name suggests, the intention is to run the transactional load against the `oltp` region and the analytical load against the `olap` region. I am using two load balancers to separate and direct the transaction and analytical queries to the appropriate regions.

For this experiement, there is only a single node in the `olap` region that will have a replica of every range for all the tables in my database. This accomplishes two goals:

1. Loading a large result set into memory doesn't need to involve communication between multiple nodes.
2. It is more economical to allocate plenty of CPU cores and RAM to just a single node.

We can inspect the ranges for the `datapoints` table as following:

```sql
SHOW RANGES FROM TABLE datapoints;
```

>[!NOTE]
> The output was reformatted to include only the output columns of interest

| range_id | replicas | replica_localities | voting_replicas | non_voting_replicas |
|:---------|:--------:|:------------------:|:---------------:|:-------------------:|
| 75 | {1,4,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {1,7,4} | {9} |
| 6004 | {1,4,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {1,7,4} | {9} |
| 6059 | {2,5,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {5,2,10} | {9} |
| 5920 | {4,5,6,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {4,5,6} | {9} |
| 5435 | {2,5,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {7,5,2} | {9} |
| 6003 | {4,7,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {4,7,10} | {9} |
| 6006 | {1,3,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {1,7,3} | {9} |
| 5482 | {1,3,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {3,7,1} | {9} |
| 5475 | {4,5,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {4,7,5} | {9} |
| 5342 | {3,7,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {10,3,7} | {9} |
| 5430 | {1,5,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {5,1,7} | {9} |
| 6031 | {1,2,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {2,1,10} | {9} |
| 6104 | {2,5,6,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {5,2,6} | {9} |
| 6042 | {4,7,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {7,4,10} | {9} |
| 5974 | {4,7,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {7,4,10} | {9} |
| 5698 | {2,5,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {2,5,7} | {9} |
| 6062 | {3,6,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {3,6,10} | {9} |
| 5948 | {3,4,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {10,3,4} | {9} |
| 5945 | {2,4,7,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {7,4,2} | {9} |
| 5493 | {1,3,6,9} | {region=oltp,region=oltp,region=oltp,region=olap} | {1,3,6} | {9} |
| 6005 | {1,5,9,10} | {region=oltp,region=oltp,region=olap,region=oltp} | {10,1,5} | {9} |

Every range has 4 replicas: 3 voting in the `oltp` region and one non-voting in the `olap`. While in the `oltp` region, three replicas for each range are distributed amongs eight nodes, node 9 in the `olap` regions has a replica of every single range.


## Deployment

I deploy the cluster to AWS using Docker Swarm (DS). I provisioned four DS nodes, one Manager and three Workers. The Manager is used to manage the DS stacks, run Prometheus and Graphana, and DBWorkload which will be discussed in a minute. The CRDB cluster is deployed to the three DS nodes.

| Swarm Node | Type       | Function | CPU / RAM | CRDB Region |
|------------|------------|----------|:---------:|:-----------:|
| Manager    | m4.4xlarge | Deploy staks ||
|            |            | HAProxy for OLTP ||
|            |            | HAProxy for OLAP ||
|            |            | DBWorkload ||
|            |            | Grafana, Prometheus ||
| Workder    | m4.4xlarge | CRDB Node 1| 4 / 16 | OLTP |
|            |            | CRDB Node 2| 4 / 16 | OLTP |
|            |            | CRDB Node 3| 4 / 16 | OLTP |
|            |            | CRDB Node 4| 4 / 16 | OLTP |
| Workder    | m4.4xlarge | CRDB Node 5| 4 / 16 | OLTP |
|            |            | CRDB Node 6| 4 / 16 | OLTP |
|            |            | CRDB Node 7| 4 / 16 | OLTP |
|            |            | CRDB Node 8| 4 / 16 | OLTP |
| Workder    | m4.4xlarge | CRDB Node 9| 16 / 64 | OLAP |


Each CRDB node runs in its own container. The above shows that the Node 9 is allocated 4 times the CPU of the nodes in the OLTP region, as well as 4 times the amount of memory.

To direct OLTP and OLAP workloads to the appropriate cluster regions, I used two HAProxy intstances running in separate containers.

## Workloads

I used [`dbworkload`](https://github.com/fabiog1901/dbworkload) to initially populate the tables and to simluate the workloads, both OLTP and OLAP.

The `stations` and `datapoints` tables were populated with 1,000 and 10 million rows respectively prior to applyting the workloads.

### Trasactional Workload

Each workload cycle consists of the following sequence of transactions:

1. For a random `station` idenitified by a UUID, `INSERT` a `datapoint` row identified by a `station` UUID and a random timestamp.
2. `UPDATE` the `datapoint` that was just `INSERT`ed 10 times. Every `UPDATE` is individually `COMMIT`ted.
3. Repeat (1) and (2) for another random `station`.
4. Repeat (1) twice.
4. `UPDATE` a random `datapoint`.
5. `DELETE` a random `datapoint`.             
6. Repeat (1) and (2) once.



### Analytical Workload



# Mount EFS on EC2

```bash
apt-get install nfs-common
```

```bash
systemctl status nfs-utils
systemctl restart nfs-utils
```

```bash
mount -t nfs4 172.31.27.106:/ /mnt/volumes
```


Docker local registry:

```bash
docker service create --name registry --publish published=5000,target=5000 --constraint node.labels.region==centcomm registry:2.7
```

Docker Swarm visualizer:

```bash
docker run -it -d -p 8000:8080 -v /var/run/docker.sock:/var/run/docker.sock dockersamples/visualizer
```


>[!NOTE]
> Need to setup a separate Docker Swarm Stack for monitoring (Prometheus, Grafana, etc.)

Grafana (should be run as a docker service)

```bash
docker run -d -p 3000:3000 --volume /mnt/volumes/grafana:/var/lib/grafana grafana/grafana-enterprise
```


Prometheus

```bash
docker run -d -p 9090:9090 -v ./grafana:/etc/prometheus -v /mnt/volumes/prometheus:/prometheus prom/prometheus
```



Create data storage structure:

```bash
for i in {0..7}; do mkdir -p heterogeneous/roach${i}/data; done
```

```bash
for i in {0..7}; do mkdir -p homogeneous/roach${i}/data; done
```


Database setup

```bash
CREATE DATABASE oltaptest;
```

```bash
root@localhost:26258/oltaptest> \i dbworkload/ddl/stations.sql
root@localhost:26258/oltaptest> \i dbworkload/ddl/datapoints.sql 
```

Confirm there are two regions in the cluster:

```sql
SHOW REGIONS FROM CLUSTER;
```

>[!NOTE]
> A license is needed for the multi-region database.

With the license key, run the following in the SQL shell:

```sql
SET CLUSTER SETTING cluster.organization = 'EXACT-NAME';
SET CLUSTER SETTING enterprise.license = 'LICENSE-KEY';
```


For demos, if it's important to shorten time until a node's declarled `DEAD`:

```sql
SHOW CLUSTER SETTING server.time_until_store_dead;
SET CLUSTER SETTING server.time_until_store_dead = '15m0s';
RESET CLUSTER SETTING server.time_until_store_dead;
```


Then set `oltp` as the primary region for the subject DB and add `olap` region as well:

```sql
ALTER DATABASE oltaptest SET PRIMARY REGION "oltp";
ALTER DATABASE oltaptest ADD region 'olap';
```

Set tables' locality:

```sql
ALTER TABLE stations SET LOCALITY REGIONAL BY TABLE;
ALTER TABLE datapoints SET LOCALITY REGIONAL BY TABLE;
```

Populate the `stations` table:

```bash
python3 -m http.server 8000
```


```sql
IMPORT INTO stations CSV DATA ('http://172.31.24.53:3000/stations.0_0_0.tsv') WITH delimiter = e'\t';
```


```sql
SHOW ZONE CONFIGURATION FROM DATABASE oltaptest;
```

```sql
SHOW RANGES FROM TABLE datapoints;
```


```sql
ALTER RANGE default CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER DATABASE system  CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.lease CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER RANGE meta CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER RANGE system CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER RANGE liveness CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.replication_constraint_stats CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.replication_stats CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.statement_statistics CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.transaction_statistics CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.tenant_usage CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.span_stats_tenant_boundaries CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.statement_activity CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
ALTER TABLE system.public.transaction_activity CONFIGURE ZONE USING num_replicas = 3, constraints = '[+region=oltp, -region=olap]';
```

How to extract the useful data from the `.csv` log files generated by `dbworkload`.

```bash
head -1 Datapointoltp.20241119_174730.csv > homogeneous-oltp.csv
awk -F, '{ if($3 == "__cycle__" && $4 == 500) print $0}' Datapointoltp.20241119_174730.csv >> homogeneous-oltp.csv

head -1 Datapointolap.20241119_174730.csv > homogeneous-olap.csv
awk -F, '{ if($3 == "__cycle__" && $4 == 5) print $0}' Datapointolap.20241119_174730.csv >> homogeneous-olap.csv

head -1 Datapointoltp.20241119_174730.csv > heterogeneous-oltp.csv
awk -F, '{ if($3 == "__cycle__" && $4 == 500) print $0}' Datapointoltp.20241119_174730.csv >> heterogeneous-oltp.csv

head -1 Datapointolap.20241119_174730.csv > heterogeneous-olap.csv
awk -F, '{ if($3 == "__cycle__" && $4 == 5) print $0}' Datapointolap.20241119_174730.csv >> heterogeneous-olap.csv
```


```sql
CREATE MATERIALIZED VIEW fulldump AS
SELECT
  d.at, s.id, s.region,
  d.param0, d.param1, d.param2, d.param3, d.param4
  FROM stations as s JOIN datapoints as d
  ON s.id=d.station;
```

```sql
SHOW ZONE CONFIGURATION FROM TABLE fulldump;
```


```sql
SET override_multi_region_zone_config = true;
ALTER TABLE fulldump CONFIGURE ZONE USING
  gc.ttlseconds = 300,
  num_replicas = 1,
  num_voters = 1,
  constraints = '[+region=olap]',
  voter_constraints = '[]',
  lease_preferences = '[]'; 
```

```sql
ALTER TABLE fulldump CONFIGURE ZONE USING
  gc.ttlseconds = 300,
  num_replicas = 3,
  num_voters = 3,
  constraints = '{+region=olap: 1, +region=oltp: 2}',
  voter_constraints = '[]',
  lease_preferences = '[[+region=olap]]';
```


```sql
SHOW RANGES FROM TABLE fulldump;
```

```sql
CREATE INDEX ON fulldump(param0);
CREATE INDEX ON fulldump(at,id);
CREATE INDEX ON fulldump(param4);
CREATE INDEX ON fulldump(length(param4));
CREATE INDEX ON fulldump(length(param4), param4);
```


```sql
SELECT at,id,param4 FROM fulldump WHERE length(param4)=23 LIMIT 100;
SELECT COUNT(*) FROM fulldump WHERE length(param4)=23;
SELECT COUNT(*) FROM fulldump;
```

```sql
CREATE INDEX IF NOT EXISTS fulldump_at_id_storing_rec_idx ON oltaptest.public.fulldump (at, id) STORING (region, param0, param1, param2, param3, param4);
```


```sql
SET CLUSTER SETTING kv.rangefeed.enabled = true;
```


```sql
ALTER TABLE datapoints CONFIGURE ZONE USING
  range_min_bytes = 134217728,
  range_max_bytes = 536870912,
  gc.ttlseconds = 14400,
  num_replicas = 5,
  num_voters = 5,
  constraints = '{+region=one: 1, +region=three: 2, +region=two: 1}',
  voter_constraints = '{+region=one: 2}',
  lease_preferences = '[[+region=one]]';
  ```

```sql
ALTER TABLE datapoints CONFIGURE ZONE USING
  num_replicas = 5,
  num_voters = 5,
  constraints = '{+region=one: 2, +region=two: 1, +region=three: 2}',
  voter_constraints = '{+region=one: 2, +region=two: 1, +region=three: 2}',
  lease_preferences = '[[+region=one]]';
```


## Generate Certificates

Generate the CA (Certificate Authority):

```bash
cockroach cert create-ca --certs-dir=volumes/certs --ca-key=volumes/certs/ca.key
```

Generate the node certificate (may need to delete the existing files as `cockroach certs` can't incrementally update):

```bash
cockroach cert create-node  \
  roach0 roach1 roach2 roach3 roach4 roach5 roach6 roach7 \
  tasks.roach0 tasks.roach1 tasks.roach2 tasks.roach3 tasks.roach4 tasks.roach5 tasks.roach6 tasks.roach7 \
  roach-one-0 roach-one-1 roach-one-2 \
  roach-two-0 roach-two-1 roach-two-2 \
  roach-three-0 roach-three-1 roach-three-2 \
  tasks.roach-one-0 tasks.roach-one-1 tasks.roach-one-2 \
  tasks.roach-two-0 tasks.roach-two-1 tasks.roach-two-2 \
  tasks.roach-three-0 tasks.roach-three-1 tasks.roach-three-2 \
  ec2-3-17-142-130.us-east-2.compute.amazonaws.com \
  --certs-dir=volumes/certs --ca-key=volumes/certs/ca.key
```

Generate the client certificate for user `root`:

```bash
cockroach cert create-client root --certs-dir=volumes/certs --ca-key=volumes/certs/ca.key
```

Log in a `root` to set up a user role:

```bash
cockroach sql --certs-dir=volumes/certs --host=ec2-3-17-142-130.us-east-2.compute.amazonaws.com --port PORT --user=root
```

Create an admin user:

```sql
CREATE USER user WITH PASSWORD 'password';
GRANT ADMIN TO user;
```

Create a non-admin user and grant privileges to a specific database:

```sql

```
