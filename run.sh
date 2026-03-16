#!/bin/bash
# WIRAWISE Coffee Chatbot - Run Script

# Install dependencies and run
pip install "numpy<2" -q && PYTHONPATH=. python backend/main.py
