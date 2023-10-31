# Local Development
`docker-compose.override-development.yml` should be renamed to `docker-compose.override.yml` in order to
be applied to the `docker-compose.yml` file. This file is used to override the `docker-compose.yml` file for local
development docker compose runs.

`.env` is used for loca development of `backend` and `frontend`, non-docker runs. `docker-compose.override.yml`
should be configured to read `.env-development` instead in order to deploy the docker containers successfully.

# Debugging Locally

## Backend

- Have to update OpenSSL to 3.1
- In order to use system OpenSSL instead of anaconda's: https://askubuntu.com/a/1074050

- When making changes to the db, run `alembic revision --autogenerate -m "message"` to generate a new migration

## Frontend

- Ensure the frontend `.env` has `VUE_APP_DOMAIN_DEV=127.0.0.1:8000` in order to connect to a local backend
- I had to update Node to 18 because {REASON?}, which required updating node to 18 in the frontend Dockerfile
  - Check the changes in the commit "FRONTEND ENV FIXES" to get the necessary changes to make this work

# Deployment

See [this post](https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/322).
Follow these instructions, and DO pull the third-party traefik.yml file. There will be two traefik containers (see
[this comment](https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/116#issuecomment-612941824)).
Copy the env vars from stag-deployment-env-vars.sh and set them before following the instructions, but be careful because
DOMAIN is set twice for two different steps.

REMEMBER TO SET THE TRAEFIK PASSWORD IN THE ENV VARS.

Don't forget to edit `frontend/.env`!

## On Git Pull
- Stop the docker stack to free up resources for the build process.
```bash
sudo su -
sudo docker stack rm prod-bot-letter-com
```
- Copy the contents of `deployment-env-vars.sh` and run it to populate the env.
- Follow the steps 
