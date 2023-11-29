#!/bin/sh

poetry run alembic upgrade head
poetry run czytacz api
