# azure-kusto-load-test
[![Docker Build Status](https://img.shields.io/docker/cloud/build/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/builds/) [![MicroBadger Size](https://img.shields.io/microbadger/image-size/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/tags/) [![Docker Pulls](https://img.shields.io/docker/pulls/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/)

This tool enables containerized load testing of Azure Data Explorer (ADX) clusters by executing [KQL](https://docs.microsoft.com/en-us/azure/kusto/query/) queries from Docker containers. The KQL query is kept outside and is exposed to the tool as an online Python script (configured by `QUERY_SCRIPT_URL`). The script must contain a function `get_query()` which returns the KQL query. Having a function allows us to randomize aspects of the query. [Here](https://gist.githubusercontent.com/syedhassaanahmed/0635ac90721ac714d7d8bc5fe2fb0913/raw/00f229177895e8775713bf422b1c39f738300e48/kusto_query.py) is an example Python script.

For reporting query performance, ADX's built-in management command [.show queries](https://docs.microsoft.com/en-us/azure/kusto/management/queries) can be used. In order to measure E2E query latency, an optional [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview) instrumentation can also be provided via `APPINSIGHTS_INSTRUMENTATIONKEY`.

## Authentication
The tool requires Azure AD for Authentication. Please follow [this document](https://docs.microsoft.com/en-us/azure/kusto/management/access-control/how-to-provision-aad-app#application-authentication-use-cases) on how to provision an AAD application and assign it relevant permissions on the ADX cluster.

## Configuration
```
CLUSTER_QUERY_URL=https://<ADX_CLUSTER>.<REGION>.kusto.windows.net
CLIENT_ID=<AAD_CLIENT_ID>
CLIENT_SECRET=<AAD_SECRET>
TENANT_ID=<AAD_TENANT>
DATABASE_NAME=adx_db
QUERY_SCRIPT_URL=https://.../query.py
TEST_ID=my_stressful_test
QUERY_CONSISTENCY=weakconsistency
APPINSIGHTS_INSTRUMENTATIONKEY=<APPINSIGHTS_INSTRUMENTATIONKEY>
QUERIES_TOTAL=100
```

- If `TEST_ID` is not provided, a guid will be generated.
- Default `QUERY_CONSISTENCY` value is `weakconsistency`. [This document](https://docs.microsoft.com/en-us/azure/kusto/concepts/queryconsistency) describes Query consistency in detail.
- Application Insights instrumentation will be ignored if `APPINSIGHTS_INSTRUMENTATIONKEY` is not provided.
- The tool will run indefinitely if `QUERIES_TOTAL` is not provided.

## Run Test
### Single Instance
Create a `.env` file with above configuration, then run;
```
docker run -it --rm --env-file .env syedhassaanahmed/azure-kusto-load-test
```

### Concurrent
Generating concurrent load requires a Kubernetes (k8s) cluster. Here are some of the options to create a cluster;
- Use the [in-built Kubernetes](https://docs.docker.com/docker-for-windows/kubernetes/) in Docker Desktop for Windows.
- Install [Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/).
- Create an [AKS](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough) cluster in Azure.

Once the k8s cluster is up and running, modify the above environment variables in `deployment.yaml` file and run the following;
```
kubectl apply -f deployment.yaml
```

Logs from a successfully running deployment can be viewed by;
```
kubectl logs -l app=adx-load-test
```

To stop the load tests;
```
kubectl delete deployment adx-load-test
```

## Query Performance
For a given test run `my_stressful_test`;

### Application Insights
E2E duration of all completed queries.
```sql
customMetrics
| where name == "query_time" and customDimensions.test_id == "my_stressful_test"
| summarize percentiles(value, 5, 50, 95) by bin(timestamp, 1m)
| render timechart
```

### ADX Engine
Duration of all completed queries as measured by the ADX query engine.
```sql
.show queries 
| where Database == "<DATABASE_NAME>" 
    and State == "Completed"
    and Text endswith "TEST_ID=my_stressful_test"
| extend Duration = Duration / time(1s)
| summarize percentiles(Duration, 5, 50, 95) by bin(StartedOn, 1m)
| render timechart
```

Number of queries/second issued during a test run.
```sql
.show queries 
| where Database == "<DATABASE_NAME>" and Text endswith "TEST_ID=my_stressful_test"
| summarize TotalQueriesSec=count() by bin(StartedOn, 1s)  
| render timechart
```

Correlation between average query duration and disk misses
```sql
.show queries
| where Database == "<DATABASE_NAME>"
    and State == "Completed"
    and Text endswith "TEST_ID=my_stressful_test"
| summarize DiskMisses = avg(toint(CacheStatistics.Disk.Misses)), 
    Duration = avg(Duration / 1s) 
    by bin(StartedOn, 1m)
| render timechart
```

Find Test IDs for tests executed in last 7 days
```sql
.show queries 
| where Database == "<DATABASE_NAME>" and StartedOn > ago(7d)
| parse Text with * "TEST_ID=" TestId
| where isnotempty(TestId)
| distinct TestId
```
