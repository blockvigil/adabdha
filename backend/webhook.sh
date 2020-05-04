#!/bin/sh

export FLASK_APP=webhook_listener.py
flask run --host=0.0.0.0 --port=5687
