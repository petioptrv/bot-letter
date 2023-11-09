# todo: create a small instance just with the DB and cache 

Migrating your app to a larger EC2 instance while preserving your Redis and PostgreSQL databases involves several steps. Here's a summarized plan to achieve this migration:

1. **Backup Database and Redis Data:**
   - Run `export PGPASSWORD=PASSWORD docker exec CONTAINER_ID pg_dump -U USERNAME DBNAME > backup.sql` to backup your PostgreSQL database.
   - For Redis, execute `docker exec CONTAINE_ID redis-cli save` followed by `docker cp CONTAINER_ID:/dump.rdb ./dump.rdb` to get a backup.

2. **Stop Current Services:**

3. **Create a New Larger EC2 Instance:**

4. **Transfer Data:**
   - Use `scp` or a similar tool to transfer `backup.sql`, `dump.rdb`, and your project files (including your `docker-compose.yml` file) to the new EC2 instance.

5. **Setup Docker and Docker-Compose:**
   - Install Docker and Docker-Compose on the new EC2 instance if not already installed.

6. **Restore Database and Redis Data:**
   - Place `backup.sql` and `dump.rdb` in the appropriate directories as specified in your `docker-compose.yml` file.
   - Run `docker-compose up -d db` to start your PostgreSQL container, then `cat backup.sql | docker-compose exec -T db psql -U USERNAME DBNAME` to restore your database.
   - Run `docker-compose up -d cache` to start your Redis container, ensure that Redis configuration is set to load the data from `dump.rdb`.

7. **Start All Services:**
   - Finally, run `docker-compose up -d` to start all your services on the new EC2 instance.

8. **Update DNS or Load Balancer:**
   - Update your DNS settings or load balancer to point to the new EC2 instance.

9. **Verify:**
   - Verify that your app is working as expected on the new EC2 instance.

10. **Cleanup:**
    - Once you're sure everything has been migrated and is working correctly, you can terminate the old EC2 instance to stop incurring charges for it.

Remember to replace `USERNAME`, `DBNAME`, `CONTAINER_ID`, and other placeholders with your actual values. This plan assumes that your `docker-compose.yml` file and other configurations are set up correctly to handle the data restoration process.