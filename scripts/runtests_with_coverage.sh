#!/bin/sh
coverage run --source couchdb tests.py
coverage report -m
