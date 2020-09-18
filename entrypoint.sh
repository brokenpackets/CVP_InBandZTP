#!/usr/bin/env bash

cd /app && python uploader.py || exit 1
python autoprovision.py || exit 1
