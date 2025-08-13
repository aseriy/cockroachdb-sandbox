# CockroachDB Upgrade Demo

Deploy a Docker Swarm stack:

```bash
docker stack deploy -c upgradable.yml upgradable
```

This will deploy a CRDB cluster with 8 nodes. The initial version is hardcoded to v23.1.30.

## Auto-Finalization vs. Manual Upgrade Finalization

By default, after all nodes are running the new version, the upgrade process will be auto-finalized. To disable auto-finalization:

```sql
SET CLUSTER SETTING cluster.preserve_downgrade_option = '23.1';
```

You can confime the setting:

```sql
SHOW CLUSTER SETTING cluster.preserve_downgrade_option;
```

## Upgrade to v23.2.27

https://www.cockroachlabs.com/docs/v23.2/upgrade-cockroach-version

For every node or group of nodes, change the Docker image version in the `upgradable.yml` from

```yaml
  roach0:
    container_name: roach0
    image: cockroachdb/cockroach:v23.1.30
```

to

```yaml
  roach0:
    container_name: roach0
    image: cockroachdb/cockroach:v23.2.27
```

Then re-run

```bash
docker stack deploy -c upgradable.yml upgradable
```

Looking at the Web console, you'll notice the following message:

Multiple versions of CockroachDB are running on this cluster.
Listed versions: 3 nodes on v23.2.27, 5 nodes on v23.1.30. You can see a list of all nodes and their versions below. This may be part of a normal rolling upgrade process, but should be investigated if unexpected.

Cluster setting cluster.preserve_downgrade_option has been set for 0.0 hours
You can see a list of all nodes and their versions below. Once all cluster nodes have been upgraded, and you have validated the stability and performance of your workload on the new version, you must reset the cluster.preserve_downgrade_option cluster setting with the following command: RESET CLUSTER SETTING cluster.preserve_downgrade_option;

You should also be able to identify the nodes that run the initial and the target versions of CRDB.

Repeat the above for the remaining cluster nodes.

Once all the nodes are at `v23.2.27`, roll back them all to `v23.1.30`.

### Finalizing the Upgrade

Re-enable auto-finalization:

```sql
RESET CLUSTER SETTING cluster.preserve_downgrade_option;
```

To confirm that finalization has completed, check the cluster version:

```sql
SHOW CLUSTER SETTING version;
```

## Repeat for Later Versions

- v24.1.22
- v24.3.11
- v25.1.10
- v25.3.0


See the recommended upgrade path at https://www.cockroachlabs.com/docs/stable/upgrade-cockroach-version

Regalar vs. Innovation Release discussion
