#!/bin/bash
PROMPT=$(cat /app/vision_prompt_test.txt)
python /app/test_vision_llm_call.py /app/主接线.png --prompt "$PROMPT" --sync-only


