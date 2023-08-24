# Local Development
`docker-compose.override-development.yml` should be renamed to `docker-compose.override.yml` in order to
be applied to the `docker-compose.yml` file. This file is used to override the `docker-compose.yml` file for local
development docker compose runs.

`.env` is used for loca development of `backend` and `frontend`, non-docker runs. `docker-compose.override.yml`
should be configured to ready `.env-development` instead in order to deploy the docker containers successfully.

# Debugging Locally

## Backend

- Have to update OpenSSL to 3.1
- In order to use system OpenSSL instead of anaconda's: https://askubuntu.com/a/1074050

- When making changes to the db, run `alembic revision --autogenerate -m "message"` to generate a new migration

## Frontend

- Ensure the frontend `.env` has `VUE_APP_DOMAIN_DEV=127.0.0.1:8000` in order to connect to a local backend
- I had to update Node to 18 because {REASON?}, which required updating node to 18 in the frontend Dockerfile
  - Check the changes in the commit "FRONTEND ENV FIXES" to get the necessary changes to make this work