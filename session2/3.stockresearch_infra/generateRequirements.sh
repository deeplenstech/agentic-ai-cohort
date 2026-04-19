#!/bin/bash
cd ../1.stockresearch
uv sync
source .venv/bin/activate
uv pip freeze --exclude-editable > requirements.txt