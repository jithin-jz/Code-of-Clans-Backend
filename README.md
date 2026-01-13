# Code of Clans - Backend

The backend API for **Code of Clans**, built with Django and Django REST Framework. It handles authentication, data management, and integration with Supabase.

## 🛠️ Tech Stack

-   **Django 6.0**: High-level Python web framework.
-   **Django REST Framework**: Toolkit for building Web APIs.
-   **Supabase / PostgreSQL**: Database and storage solution.
-   **OAuth2**: Authentication via GitHub, Google, and Discord.

## 📂 Apps

-   `authentication`: Handles user registration, login, and OAuth flows.
-   `project`: Main project configuration and settings.

## 🔑 Environment Variables

Create a `.env` file in this directory with the following keys:

```ini
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True
FRONTEND_URL=http://localhost:5173

# Database (Supabase PostgreSQL Connection URL)
DATABASE_URL=postgres://user:password@host:port/dbname

# OAuth Providers
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...

# Supabase Storage
SUPABASE_URL=...
SUPABASE_KEY=...
```

## 🚀 Setup & Run

1.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate  # Windows
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Migrations**:
    ```bash
    python manage.py migrate
    ```

4.  **Start Server**:
    ```bash
    python manage.py runserver
    ```

## 📜 Scripts

-   `scripts/process_new_assets.py`: Utility to process and clean green-screen assets.
