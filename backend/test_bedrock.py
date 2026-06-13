import boto3
import json

client = boto3.client(
    "bedrock-runtime",
    region_name="ap-south-1"
)

response = client.invoke_model(
    modelId="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
    body=json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Say hello in one sentence."
                    }
                ]
            }
        ]
    }),
    contentType="application/json"
)

print(response["body"].read().decode())