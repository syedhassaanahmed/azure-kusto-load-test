# azure-kusto-load-test
[![Docker Build Status](https://img.shields.io/docker/build/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/builds/) [![MicroBadger Size](https://img.shields.io/microbadger/image-size/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/tags/) [![Docker Pulls](https://img.shields.io/docker/pulls/syedhassaanahmed/azure-kusto-load-test.svg?logo=docker)](https://hub.docker.com/r/syedhassaanahmed/azure-kusto-load-test/)

This tool enables containerized load testing of Azure Data Explorer (ADX). The ADX query that needs to be executed, must be exposed as an online Python script (`QUERY_SCRIPT_URL`). The script should contain a function `get_query()` returning the ADX query. [Here](https://gist.githubusercontent.com/syedhassaanahmed/0635ac90721ac714d7d8bc5fe2fb0913/raw/979e022f4fcc74ce27a6ee27e884ac259dd56309/kusto_query.py) is an example script.

## Authentication
Authentication is done using Azure AD. Please follow [this document](https://docs.microsoft.com/en-us/azure/kusto/management/access-control/how-to-provision-aad-app#application-authentication-use-cases) on how to provision an AAD application and assign it relevant permissions on the ADX cluster.

## Configuration
The tool requires following environment variables.
```
CLUSTER_QUERY_URL=https://<ADX_CLUSTER>.<REGION>.kusto.windows.net
CLIENT_ID=<AAD_CLIENT_ID>
CLIENT_SECRET=<AAD_SECRET>
TENANT_ID=<AAD_TENANT>
DATABASE_NAME=adx_db
QUERY_SCRIPT_URL=https://.../adx_query.py
TEST_ID=my_stressful_test
QUERIES_TOTAL=100
```

- If `TEST_ID` is not provided, a guid will be generated.
- If `QUERIES_TOTAL` is not provided, the tool will run indefinitely.

## Run Test
### Single Instance
Create a `.env` file with above configuration, then run;
```
docker run -it --rm --env-file .env syedhassaanahmed/azure-kusto-load-test
```

### Concurrent
Generating concurrent load requires a Kubernetes cluster. Follow [this guideline](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough) to create an AKS cluster in Azure. Given a k8s cluster is up and running, modify above environment variables in `deployment.yaml` file and run the following;
```
kubectl create -f deployment.yaml
```

Once deployment is successful, the logs can be viewed by;
```
kubectl logs -l app=adx-load-test
```

To stop the load tests;
```
kubectl delete deployment adx-load-test
```

## Query Performance
Here is how to visualize the duration of all completed queries performed during Test `my_stressful_test`.

```sql
.show queries 
| where Database == "<DATABASE_NAME>" 
    and State == "Completed"
    and Text endswith "TEST_ID=my_stressful_test"
| extend Duration_sec = Duration / time(1s)
| summarize percentile(Duration_sec, 99) by bin(StartedOn, 10s) 
| render timechart 
```