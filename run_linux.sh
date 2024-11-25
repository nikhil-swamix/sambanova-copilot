#!/bin/bash
cd "$(dirname "$0")"
echo "$(dirname "$0")"
pip install -r requirements.txt
python3 copilot.pyw 
