import os, uuid, timeit, functools

from query import get_query
from azure.kusto.data.request import KustoClient, KustoConnectionStringBuilder, ClientRequestProperties
from applicationinsights import TelemetryClient

######################################################
##                        AUTH                      ##
######################################################
cluster = os.environ.get("CLUSTER_QUERY_URL")
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
tenant_id = os.environ.get("TENANT_ID")

kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
    cluster, client_id, client_secret, tenant_id)

kusto_client = KustoClient(kcsb)

######################################################
##                       QUERY                      ##
######################################################

db_name = os.environ.get("DATABASE_NAME")
test_id = os.environ.get("TEST_ID", str(uuid.uuid4()))
query_consistency = os.environ.get("QUERY_CONSISTENCY", "weakconsistency")

request_properties = ClientRequestProperties()
request_properties.set_option("queryconsistency", query_consistency)

instrumentation_key = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
telemetry_client = None
if instrumentation_key:
    telemetry_client = TelemetryClient(instrumentation_key)

print("Test run for '{}' started.".format(test_id))

def execute_query(raw_query):
    query = "{} //TEST_ID={}".format(raw_query, test_id)
    response = kusto_client.execute(db_name, query, request_properties)

    if response.errors_count > 0:
        if telemetry_client:
            telemetry_client.track_exception(response)
            telemetry_client.flush()

        raise Exception(response)

queries_total = int(os.environ.get("QUERIES_TOTAL", -1))
queries_executed = 0

while queries_executed < queries_total or queries_total < 0:
    raw_query = get_query()
    print("\nTest '{}' executing #{}:\n{}\n".format(test_id, queries_executed, raw_query))

    t = timeit.Timer(functools.partial(execute_query, raw_query))
    query_time = t.timeit(number=1)

    print("Query took: {:.2f} seconds".format(query_time))
    queries_executed += 1

    if telemetry_client:
        telemetry_client.track_metric("query_time", query_time, properties={"test_id": test_id})
        telemetry_client.flush()

print("Test run for '{}' ended.".format(test_id))
