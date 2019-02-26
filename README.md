# azure-kusto-load-test
This tool enables containerized load testing of Azure Data Explorer (ADX). The ADX query that needs to be executed, must be exposed as an online Python script (`QUERY_SCRIPT_URL`). The script should contain a function `get_query()` returning the query. [Here](https://gist.githubusercontent.com/syedhassaanahmed/0635ac90721ac714d7d8bc5fe2fb0913/raw/979e022f4fcc74ce27a6ee27e884ac259dd56309/kusto_query.py) is an example script.

## Authentication
Authentication is done using Azure AD. Please follow [this document](https://docs.microsoft.com/en-us/azure/kusto/management/access-control/how-to-provision-aad-app#application-authentication-use-cases) on how to provision an AAD application and assign it relevant permissions on the ADX cluster.

## Configuration
The tool requires following environment variables. If `TEST_ID` is missing, a guid will be generated.

```
CLUSTER_QUERY_URL=https://<ADX_CLUSTER>.<REGION>.kusto.windows.net
CLIENT_ID=<AAD_CLIENT_ID>
CLIENT_SECRET=<AAD_SECRET>
TENANT_ID=<AAD_TENANT>
DATABASE_NAME=adx_db
QUERY_SCRIPT_URL=https://.../kusto_query.py
TEST_ID=my_stressful_test
```

## Test report
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