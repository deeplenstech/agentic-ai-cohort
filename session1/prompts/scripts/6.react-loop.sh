aws bedrock-runtime invoke-model \
  --model-id openai.gpt-oss-120b-1:0 \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --performance-config-latency standard \
  --body file://6.react-input.json \
  "6.tmp-model-output.json"

# Extract from content, stripping <reasoning>...</reasoning> if present
python3 -c "
import json, re
with open('6.tmp-model-output.json') as f:
    data = json.load(f)
content = data['choices'][0]['message']['content']
content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL).strip()
if content:
    print(content)
else:
    tool_calls = data['choices'][0]['message'].get('tool_calls', [])
    pretty = json.dumps(tool_calls, indent=2)
    print(pretty)
    print()
    print(json.dumps(pretty))
"