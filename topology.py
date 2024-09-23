from diagrams import Diagram, Cluster, Edge

from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

from diagrams.onprem.database import CockroachDB

with Diagram("World Wide Cluster: Data Writes on Island", show=False):

    island = Cluster("Roach Island Region")
    with island:
        primary_az = Cluster("Primary Data Center")
        with primary_az:
          lease_holder = CockroachDB("Lease Holder")
          follower_1 = CockroachDB("Follower")
 
        secondary_az = Cluster("Secondary Data Center")
        with secondary_az:
          follower_2 = CockroachDB("Follower")
          node1 = CockroachDB("Node")
  
        follower_1 << lease_holder >> follower_2

    us_east = Cluster("US East Region")
    with us_east:
        node_use1 = CockroachDB("Non-voting replica")
        node_use2 = CockroachDB("Node")

    eu_central = Cluster("EU Central Region")
    with eu_central:
        node_euc1 = CockroachDB("Non-voting replica")
        node_euc2 = CockroachDB("Node")


    node_use1 << Edge(label="Satellite Link") << lease_holder
    node_euc1 << Edge(label="Satellite Link") << lease_holder


with Diagram("World Wide Cluster: Data Writes on Mainland", show=False):

    island = Cluster("Roach Island Region")
    with island:
        primary_az = Cluster("Primary Data Center")
        with primary_az:
          p_node1 = CockroachDB("Non-voting replica")
          p_node2 = CockroachDB("Node")
 
        secondary_az = Cluster("Secondary Data Center")
        with secondary_az:
          s_node1 = CockroachDB("Non-voting replica")
          s_node2 = CockroachDB("Node")
  

    us_east = Cluster("US East Region")
    with us_east:
        use_lease_holder = CockroachDB("Lease Holder")
        use_follower_1 = CockroachDB("Follower")
        use_follower_2 = CockroachDB("Follower")

    use_follower_1 << use_lease_holder >> use_follower_2

    eu_central = Cluster("EU Central Region")
    with eu_central:
        euc_lease_holder = CockroachDB("Lease Holder")
        euc_follower_1 = CockroachDB("Follower")
        euc_follower_2 = CockroachDB("Follower")
        node_euc1 = CockroachDB("Non-voting replica")
        node_euc2 = CockroachDB("Node")

    euc_follower_1 << euc_lease_holder >> euc_follower_2

    p_node1 << Edge(label="Satellite Link") << use_lease_holder
    s_node1 << Edge(label="Satellite Link") << use_lease_holder
    p_node1 << Edge(label="Satellite Link") << euc_lease_holder
    s_node1 << Edge(label="Satellite Link") << euc_lease_holder

