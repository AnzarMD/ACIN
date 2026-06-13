import boto3
import json

client = boto3.client(
    "bedrock-runtime",
    region_name="ap-south-1"
)

body = {
    "messages": [
        {
            "role": "user",
            "content": [{"text": "Say hello"}]
        }
    ]
}

try:
    response = client.invoke_model(
        modelId="amazon.nova-micro-v1:0",
        body=json.dumps(body)
    )

    print("SUCCESS")
    print(response["ResponseMetadata"]["HTTPStatusCode"])

except Exception as e:
    print("ERROR:", e)