#!/bin/bash

poetry run alembic upgrade head
poetry run celery -A czytacz.tasks worker --loglevel=INFO -B
