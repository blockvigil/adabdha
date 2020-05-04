#!/bin/sh

export FLASK_APP=stripe_listener.py
flask run --host=0.0.0.0 --port=8000
