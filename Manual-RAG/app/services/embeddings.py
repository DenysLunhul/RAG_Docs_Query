import boto3
import json

client = boto3.client('bedrock-runtime', region_name='us-east-1')

def get_embedding(text: str) -> list[float]:
    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({
            "inputText": text
        })
    )
    result = json.loads(response['body'].read())
    vector = result['embedding']
    return vector



if __name__ == "__main__":
    vector = get_embedding("Hello world!")
    print(f"Vector size: {len(vector)}")
    print(f"First 10 values: {vector[:10]}")