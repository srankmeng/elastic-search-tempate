import opensearchpy
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from dotenv import load_dotenv
from retry import retry
import pandas as pd
import json
import os

@retry(opensearchpy.ConnectionError, max_delay=300, delay=5)
def indexer():
    load_dotenv()

    print("============== Connect opensearch ==============")
    OPENSEARCH_USERNAME = os.getenv('OPENSEARCH_USERNAME')
    OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD')
    OPENSEARCH_INDEX_NAME = os.getenv('OPENSEARCH_INDEX_NAME')
    OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST') or "localhost"
    OPENSEARCH_PORT = os.getenv('OPENSEARCH_PORT')

    os_client = OpenSearch(
        hosts = [{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth = (OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
        use_ssl = True,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
    )

    print("=============== Read csv file ===============")
    csv_file_path = os.path.join("data", "initial_data.csv")
    df = pd.read_csv(csv_file_path)
    json_str = df.to_json(orient='records')
    json_records = json.loads(json_str)

    index_name = OPENSEARCH_INDEX_NAME
    number_of_shards = 1
    os_params = {

        "settings": {"index": {
            "number_of_shards": number_of_shards,
            "max_ngram_diff": 100,
            "analysis": {
                "analyzer": {
                    "trigrams": {
                    "type": "custom",
                    "tokenizer": "trigram_tokenizer",
                    "filter": [
                        "lowercase"
                    ]
                    }
                },
                "tokenizer": {
                    "trigram_tokenizer": {
                    "type": "ngram",
                    "min_gram": 3,
                    "max_gram": 100,
                    "token_chars": []
                    }
                }
            }
        }},
        "mappings": {
            "properties": {
                "spec_no": {
                    "type": "keyword"
                },
                "spec_issue_no": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "spec_name": {
                    "analyzer": "trigrams",
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "spec_shortname": {
                    "analyzer": "trigrams",
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "status": {
                    "type": "keyword"
                },
                "cross_reference": {
                    "type": "keyword"
                },
                "effective_date": {
                    "type": "date",
                    "format": ["dd-MMM-yy"]
                },
                "originator": {
                    "analyzer": "trigrams",
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                }
            }
            
        }
    }
    if os_client.indices.exists(index=index_name):
        os_client.indices.delete(index=index_name)
    os_client.indices.create(index_name, body=os_params)
    action_list = []
    
    for row in json_records:
        record ={
            '_op_type': 'index',
            '_index': index_name,
            '_source': row
        }
        action_list.append(record)

    print("============= Start import data =============")
    bulk(os_client, action_list)

    print("=========== Import data successful ==========")

if __name__ == "__main__":
    indexer()