aws bedrock-runtime invoke-model \
  --model-id openai.gpt-oss-120b-1:0 \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --performance-config-latency standard \
  --body file://2.request-body.json \
  "2.invoke-model-output.json"