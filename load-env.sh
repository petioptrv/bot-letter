#!/bin/bash
while read -r line || [[ -n "$line" ]]; do
    if [[ ! "$line" =~ ^# && "$line" != "" ]]; then
        export "$line"
    fi
done < .env
