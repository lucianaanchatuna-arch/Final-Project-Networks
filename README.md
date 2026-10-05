# Final Project Networks

## Project Overview

This project measures false assurance in LLM-based automated vulnerability repair.

The system sends vulnerable Python code from Vul4Py to an LLM through the OpenAI API. The LLM returns a patch, a success claim, and a confidence score. Then, the patch is independently evaluated using Vul4Py.

## Main Metrics

- VRR: Verified Repair Rate
- FAR: False Assurance Rate

## Tools

- AWS EC2
- Python
- OpenAI API
- Vul4Py
- Semgrep
- GitHub

## Current Status

Initial repository setup.
