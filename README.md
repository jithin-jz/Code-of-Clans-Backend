# Code of Clans - Backend

The robust backend API and real-time server for the Code of Clans platform, built with Django and Django Channels.

## 🚀 Tech Stack

- **Framework:** [Django 6](https://www.djangoproject.com/)
- **API:** [Django REST Framework](https://www.django-rest-framework.org/)
- **Real-time:** [Django Channels](https://channels.readthedocs.io/) (WebSockets)
- **Database:** PostgreSQL (via [Supabase](https://supabase.com/))
- **Authentication:** JWT (JSON Web Tokens) + OAuth (GitHub, Google, Discord)
- **Storage:** Supabase Storage (Buckets)

## ✨ Features

- **REST API:** Endpoints for user management, profiles, and auth.
- **WebSocket Server:** Handles real-time global chat messaging.
- **OAuth Integration:** Seamless login with multiple providers.
- **Referral System:** Built-in referral code logic and XP tracking.

## 🛠️ Setup & Installation

1.  **Clone the repository**.

2.  **Create a virtual environment**:
    ```bash
    cd backend
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If `channels` or `daphne` are missing, install them: `pip install channels daphne`*

4.  **Environment Variables**:
    Create a `.env` file in the `backend` directory with the following keys:
    ```env
    SECRET_KEY=your_secret_key
    DEBUG=True
    
    # Database (Supabase Request)
    DATABASE_URL=postgresql://user:password@host:port/dbname
    
    # Supabase (For Storage Buckets)
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your_supabase_anon_key

    # OAuth Credentials
    GITHUB_CLIENT_ID=...
    GITHUB_CLIENT_SECRET=...
    GOOGLE_CLIENT_ID=...
    GOOGLE_CLIENT_SECRET=...
    DISCORD_CLIENT_ID=...
    DISCORD_CLIENT_SECRET=...

    # Frontend URL (for CORS/Redirects)
    FRONTEND_URL=http://localhost:5173
    ```

5.  **Run Migrations**:
    ```bash
    python manage.py migrate
    ```

6.  **Run Development Server**:
    ```bash
    python manage.py runserver
    ```
    *The server will run on `http://127.0.0.1:8000`. WebSockets are available at `ws://127.0.0.1:8000/ws/chat/`.*

## 📂 Project Structure

- `authentication/`: User models, views, and OAuth logic.
- `chat/`: WebSocket consumers (`consumers.py`) and routing (`routing.py`).
- `project/`: Main Django settings and URL configuration.
