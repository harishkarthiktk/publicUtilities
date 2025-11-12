## Get All Collections API Reference
curl -X GET 'http://localhost:6333/collections'

### Output reference
{
    "result": {
        "collections": [
            { "name": "collection_a" },
            { "name": "collection_b" },
            { "name": "collection_c" }
        ]
    },
    "status": "ok",
    "time": 0.0
}


## Delete API Reference
for name in $(curl -s -X GET 'http://localhost:6333/collections' | jq -r '.result.collections[].name'); do
  echo "Deleting collection: $name"
  curl -X DELETE "http://localhost:6333/collections/$name"
  echo ""
done

