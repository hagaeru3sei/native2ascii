#!/usr/bin/env bash

PROJECT_ROOT=./

mkdir -p logs
mkdir -p var/db

sqlite3 var/db/native2ascii.db < src/res/strings.sql


