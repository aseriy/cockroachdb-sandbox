HOMOGENEOUS

dbworkload run -w dbworkload/DatapointOLTP.py --uri postgresql://root@localhost:26257/oltaptest?sslmode=disable -c 10 -d 600

┌───────────┬──────────────────────┬───────────┬───────────┬─────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│   elapsed │ id                   │   threads │   tot_ops │   tot_ops/s │   mean(ms) │   p50(ms) │   p90(ms) │   p95(ms) │   p99(ms) │   max(ms) │
├───────────┼──────────────────────┼───────────┼───────────┼─────────────┼────────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│       600 │ __cycle__            │        10 │    74,393 │         123 │      80.61 │     52.01 │    168.50 │    191.50 │    235.97 │  1,831.97 │
│       600 │ sql_insert_datapoint │        10 │    74,393 │         123 │      80.60 │     52.01 │    168.50 │    191.51 │    235.95 │  1,831.97 │
└───────────┴──────────────────────┴───────────┴───────────┴─────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘

dbworkload run -w dbworkload/DatapointOLAP.py --uri postgresql://root@localhost:26257/oltaptest?sslmode=disable -c 10 -d 600

┌───────────┬────────────────────────┬───────────┬───────────┬─────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│   elapsed │ id                     │   threads │   tot_ops │   tot_ops/s │   mean(ms) │   p50(ms) │   p90(ms) │   p95(ms) │   p99(ms) │   max(ms) │
├───────────┼────────────────────────┼───────────┼───────────┼─────────────┼────────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│       602 │ __cycle__              │        10 │     4,256 │           7 │   1,404.28 │  1,358.19 │  1,789.29 │  1,954.18 │  2,423.19 │  3,464.74 │
│       602 │ sql_count_datapoints   │        10 │     4,266 │           7 │      24.98 │     18.94 │     52.49 │     64.84 │     83.94 │    217.09 │
│       602 │ sql_datapoints_by_hour │        10 │     4,256 │           7 │   1,266.47 │  1,221.38 │  1,640.04 │  1,800.69 │  2,277.35 │  3,304.59 │
│       602 │ sql_stats_by_region    │        10 │     4,256 │           7 │     112.79 │    106.52 │    157.49 │    179.77 │    232.70 │    344.93 │
└───────────┴────────────────────────┴───────────┴───────────┴─────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘



HETERGENEOUS

dbworkload run -w dbworkload/DatapointOLTP.py --uri postgresql://root@localhost:26258/oltaptest?sslmode=disable -c 10 -d 600

┌───────────┬──────────────────────┬───────────┬───────────┬─────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│   elapsed │ id                   │   threads │   tot_ops │   tot_ops/s │   mean(ms) │   p50(ms) │   p90(ms) │   p95(ms) │   p99(ms) │   max(ms) │
├───────────┼──────────────────────┼───────────┼───────────┼─────────────┼────────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│       600 │ __cycle__            │        10 │   191,774 │         319 │      31.25 │     30.30 │     37.99 │     41.35 │     51.47 │    160.50 │
│       600 │ sql_insert_datapoint │        10 │   191,774 │         319 │      31.24 │     30.24 │     38.01 │     41.28 │     51.43 │    160.49 │
└───────────┴──────────────────────┴───────────┴───────────┴─────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘



dbworkload run -w dbworkload/DatapointOLAP.py --uri postgresql://root@localhost:26259/oltaptest?sslmode=disable -c 10 -d 600

┌───────────┬────────────────────────┬───────────┬───────────┬─────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│   elapsed │ id                     │   threads │   tot_ops │   tot_ops/s │   mean(ms) │   p50(ms) │   p90(ms) │   p95(ms) │   p99(ms) │   max(ms) │
├───────────┼────────────────────────┼───────────┼───────────┼─────────────┼────────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│       603 │ __cycle__              │        10 │     2,202 │           3 │   2,718.94 │  2,423.66 │  4,501.64 │  4,793.63 │  5,219.28 │  5,705.64 │
│       603 │ sql_count_datapoints   │        10 │     2,212 │           3 │      64.18 │     64.18 │     94.40 │    103.24 │    120.48 │    141.01 │
│       603 │ sql_datapoints_by_hour │        10 │     2,202 │           3 │   2,465.20 │  2,187.48 │  4,159.59 │  4,437.17 │  4,822.86 │  5,379.52 │
│       603 │ sql_stats_by_region    │        10 │     2,202 │           3 │     189.31 │    177.89 │    283.56 │    304.63 │    366.62 │    669.93 │
└───────────┴────────────────────────┴───────────┴───────────┴─────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
