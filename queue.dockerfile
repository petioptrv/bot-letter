FROM rabbitmq:3
# Using the below image instead is required to enable the "Broker" tab in the flower UI:
# FROM rabbitmq:3-management
#
# You also have to change the flower command in docker-compose.yml

COPY rabbitmq-deploy-advanced.conf /etc/rabbitmq/advanced.conf
