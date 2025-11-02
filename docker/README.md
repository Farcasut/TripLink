
**An easy way to start a Docker container with the project database**


To get started, make sure you have **Docker** and **Docker Compose** installed on your machine.

1. Create a `.env` file in the same directory as your `docker-compose.yml` and add the following variables:

   ```bash
   POSTGRES_USER=admin
   POSTGRES_PASSWORD=password
   ```
   
2. **Start the PostgreSQL container** by running:

   ```bash
    docker-compose up -d
   ```
