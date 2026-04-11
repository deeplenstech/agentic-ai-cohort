aws bedrock-runtime invoke-model \
  --model-id openai.gpt-oss-120b-1:0 \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --performance-config-latency standard \
  --body file://3.structured-request-body.json \
  "4.structured-v2-invoke-model-output.json"

# Extract JSON from content, stripping <reasoning>...</reasoning> if present
python3 -c "
import json, re
with open('4.structured-v2-invoke-model-output.json') as f:
    data = json.load(f)
content = data['choices'][0]['message']['content']
content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL).strip()
with open('4.structured-v2-invoke-model-output.json', 'w') as out:
    json.dump(json.loads(content), out, indent=2)
"
