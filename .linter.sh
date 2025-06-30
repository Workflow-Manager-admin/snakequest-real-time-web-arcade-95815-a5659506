#!/bin/bash
cd /home/kavia/workspace/code-generation/snakequest-real-time-web-arcade-95815-a5659506/django_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

