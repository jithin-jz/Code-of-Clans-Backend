# Docker: What, Why, and How We Implemented It

## 1. What is Docker?

Imagine you are baking a cake. To bake it exactly right, you need not just the recipe (your code) but also the specific oven, the right pans, and the exact brand of ingredients (your environment and dependencies).

**Docker** allows you to package your application (the cake) along with its entire environment (the oven, pans, ingredients) into a single box called a **Container**.

- **Container**: A lightweight, standalone package that includes everything needed to run a piece of software: code, runtime, system tools, system libraries, and settings.
- **Image**: The blueprint or template for creating a container (like the written recipe).
- **Docker vs Virtual Machines (VMs)**: VMs run a whole operating system (heavy, slow). Docker containers share the host's OS kernel but keep the application isolated (lightweight, fast).

## 2. Why Use Docker?

1.  **"It works on my machine" (Solved)**: Since the environment is packaged with the code, if it runs in Docker on your laptop, it will run in Docker on the server, your friend's laptop, or anywhere else.
2.  **Isolation**: Your Django backend has its own clean space. It doesn't care if your computer has Python 3.9 or 3.12 installed; the container uses exactly what it needs (Python 3.12 in our case).
3.  **Dependency Management**: We need a database (PostgreSQL). Instead of installing Postgres manually on Windows, configuring ports, and messing with system services, we just spin up a Postgres *container*. It's clean and disposable.
4.  **Quick Onboarding**: A new developer doesn't need to install Python, Postgres, Redis, etc. They just run `docker-compose up`, and everything works.

---

## 3. How We Implemented It in "Code of Clan"

We made four key changes to "Dockerize" your Django backend.

### A. The Blueprint: `Dockerfile`
**Location**: `/backend/Dockerfile`

This file tells Docker how to build the image for our specific Django app.
*   **`FROM python:3.12-slim`**: We start with a lightweight version of Linux that already has Python 3.12 installed.
*   **`WORKDIR /app`**: We create a folder inside the container to hold our code.
*   **`COPY requirements.txt .`**: We copy our dependency list into the container.
*   **`RUN pip install ...`**: We install Django, DRF, Psycopg2, Channels, etc., *inside* the container.
*   **`COPY . .`**: We copy the rest of your Django code into the container.
*   **`CMD [...]`**: The default command to run when the container starts (`python manage.py runserver`).

### B. The Orchestrator: `docker-compose.yml`
**Location**: `/backend/docker-compose.yml`

This file manages multiple containers at once. We defined two services:
1.  **`web`**: Your Django backend (built from the `Dockerfile` above).
    *   It forwards port `8000` so you can access it at `localhost:8000`.
    *   It depends on the `db` service.
2.  **`db`**: The PostgreSQL database.
    *   Uses the official `postgres:15` image (no installation required on your PC!).
    *   Stores data in a **Volume** (`postgres_data`) so your users/data persist even if you restart the container.
    *   Exposes port `5432` so you can connect to it with tools like pgAdmin/DBeaver.

### C. The Bridge: `settings.py`
**Location**: `/backend/project/settings.py`

Docker runs in a separate network environment. To allow flexibility, we modified `settings.py` to stop hardcoding database credentials and read them from **Environment Variables**:
```python
"HOST": os.getenv("DB_HOST", "127.0.0.1"),
```
*   **Inside Docker**: `DB_HOST` is set to `db` (the internal name of the database container).
*   **On Windows**: It defaults to `127.0.0.1` so you can still run `python manage.py runserver` locally if you want.

### D. The Glue: `.env` and `requirements.txt`
*   **`requirements.txt`**: We added `psycopg2-binary` (Postgres driver) and `daphne/channels` so they are installed in the Docker image.
*   **`.env`**: We updated your local `.env` file to point to the Docker database (`DB_PORT=5432`, `DB_HOST=127.0.0.1`). This means your local tools connect to the database running inside Docker.

## 4. Summary of Workflow

**Before Docker:**
You had to install Python, install Postgres manually, configure it, create a virtual environment, install requirements, and hope everything matches production.

**With Docker:**
You simply run:
```bash
docker-compose up --build
```
Docker downloads Postgres, builds your Python environment, connects them together, and serves your app.


A. Lifecycle Control
docker-compose up              # start services
docker-compose up -d           # start in background (use this daily)
docker-compose down            # stop + remove containers (keeps volumes)
docker-compose down -v         # nuke everything including DB data
docker-compose restart web     # restart only Django

B. Inspect What’s Actually Running
docker ps                      # running containers
docker ps -a                   # all containers (dead ones too)
docker images                  # images on your system
docker volume ls               # persistent data
docker network ls              # internal Docker networks

C. Logs (Stop Guessing, Start Reading)
docker-compose logs
docker-compose logs web
docker-compose logs -f web     # live logs (tail -f equivalent)


2. Getting Inside Containers (You Will Need This)
Django container

    docker-compose exec web bash

Now you are inside Linux, inside your container.

From here:

    python manage.py migrate
    python manage.py createsuperuser
    python manage.py shell


PostgreSQL container

    docker-compose exec db psql -U postgres

You should know how to:

    \l        -- list databases
    \c dbname -- connect
    \dt       -- list tables


| Action     | Command                     | When to use              |
| ---------- | --------------------------- | ------------------------ |
| Restart    | `docker-compose restart`    | Code change only         |
| Rebuild    | `docker-compose up --build` | requirements.txt changed |
| Full reset | `docker-compose down -v`    | You want a clean slate   |



Hard truth:
Changing Python code does not require rebuild.
Changing dependencies does.

If you rebuild every time, you don’t understand Docker yet.

## 5. Data Safety (Important!)

**Q: If I stop Docker, do I lose my database data?**
A: **NO**, not if you configured it correctly (which we did).

We used a **Volume** in `docker-compose.yml`:
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data/
```
This enables data persistence.

**Commands:**
*   `docker-compose down`: Stops containers, **KEEPS** data (Volume preserved).
*   `docker-compose down -v`: Stops containers, **DELETES** data (Volume destroyed).

**Summary**: Use `docker-compose down` daily. Only use `-v` if you want to wipe the database and start fresh.
