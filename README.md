# Code of Clans - Backend

Django API for the Code of Clans gaming profile application.

## Tech Stack
-   **Framework**: Django + Django REST Framework
-   **Database**: SQLite (Dev) / PostgreSQL (Supabase)
-   **Authentication**: OAuth2 (GitHub, Google, Discord)
-   **Storage**: Supabase Storage

## Setup

1.  Create a virtual environment:
    ```bash
    python -m venv .venv
    ```
2.  Activate it:
    ```bash
    .\.venv\Scripts\activate
    ```
3.  Install extensions:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run migrations:
    ```bash
    python manage.py migrate
    ```
5.  Start server:
    ```bash
    python manage.py runserver
    ```
