import os
import uuid

from query import get_query

from azure.kusto.data.request import KustoClient, KustoConnectionStringBuilder

######################################################
##                        AUTH                      ##
######################################################
cluster = os.environ.get("CLUSTER_QUERY_URL")
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
authority_id = os.environ.get("TENANT_ID")

kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
    cluster, client_id, client_secret, authority_id)

client = KustoClient(kcsb)

######################################################
##                       QUERY                      ##
######################################################

db_name = os.environ.get("DATABASE_NAME")
test_id = os.environ.get("TEST_ID", str(uuid.uuid4()))

def execute_query():
    query = "{0} //TEST_ID={1}".format(get_query(), test_id)
    response = client.execute(db_name, query)
    if response.errors_count > 0:
        raise Exception(response)

# Total number of queries to run or -1 to run forever
queries_total = int(os.environ.get("QUERIES_TOTAL", -1))
queries_executed = 0
while queries_executed < queries_total or queries_total < 0:    
    print("TEST_ID=" + test_id)
    execute_query()
    queries_executed += 1