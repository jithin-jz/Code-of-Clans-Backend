# How Authentication Works in "Code of Clan"

This document explains the inner workings of the `authentication` app. We use a **JWT (JSON Web Token)** based system integrated with **OAuth providers** (GitHub, Google, Discord).

## 1. High-Level Overview

1.  **Frontend requests login**: User clicks "Login with GitHub".
2.  **Backend generates URL**: The backend constructs the correct OAuth URL for the provider.
3.  **User authenticates**: User logs in on the provider's site.
4.  **Callback**: Identifying code is sent back to our backend.
5.  **Exchange & Create**: Backend swaps the code for an access token, gets user info, creates/updates the user in our DB, and issues our own **JWT**.
6.  **Access**: Frontend uses our JWT to access protected API endpoints.

---

## 2. Key Components

### A. Data Models (`models.py`)
We rely on Django's built-in `User` model for the core authentication, but we extend it with:
*   **`UserProfile`**: Stores OAuth data (`provider`, `provider_id`), profile visuals (`avatar_url`), and game stats (`xp`, `referral_code`). It is linked One-to-One with `User`.
*   **`UserFollow`**: Manages the "Following" system (who follows whom).

### B. The Gatekeeper: `authentication.py`
We don't use sessions. We use **`JWTAuthentication`**.
*   It looks for a header: `Authorization: Bearer <token>`.
*   It decodes the token to find the `user_id`.
*   It sets `request.user` for the view if the token is valid.

### C. URLs & Views Breakdown (`urls.py`)

The views are organized into modules for clarity:

**1. OAuth Flow (`views/oauth.py`)**
*   **`*AuthURLView`**: Returns the URL to redirect the user to (e.g., `github.com/login...`).
*   **`*CallbackView`**: The heavy lifter.
    *   Receives the `code` from the frontend.
    *   Calls the provider (GitHub/Google) to get the user's email/avatar.
    *   **Logic**:
        *   Does this user exist? -> Log them in.
        *   Is this a new user? -> Create `User` + `UserProfile`.
    *   **Returns**: Access & Refresh tokens (JWTs) to the frontend.

**2. User Management (`views/user.py`)**
*   **`CurrentUserView`**: "Who am I?" (Returns profile of the token owner).
*   **`RefreshTokenView`**: Swaps an old refresh token for a new access token.
*   **`LogoutView`**: Blacklists the refresh token (if implemented) or just tells frontend to discard it.

**3. Profile & Social (`views/profile.py`)**
*   **`ProfileDetailView`**: Public profile data (stats, bio).
*   **`FollowToggleView`**: Follow/Unfollow logic.

### D. Security Features
*   **`admin.py`**: Custom admin panel configurations.
*   **`utils.py`**: Helper functions for generating/decoding tokens.

---

## 3. The Login Flow (Step-by-Step)

Here is what happens when a user logs in with GitHub:

1.  **GET** `/auth/github/`: Backend returns `auth_url`.
2.  Frontend redirects user to `auth_url`.
3.  User approves access on GitHub.
4.  GitHub redirects back to Frontend with `?code=xyz`.
5.  **POST** `/auth/github/callback/` with `{ code: "xyz" }`.
6.  Backend:
    *   Exchanges `xyz` for a GitHub token.
    *   Fetches user profile from GitHub API.
    *   Finds/Creates user in PostgreSQL.
    *   Generates `access_token` (valid 1 hour) and `refresh_token` (valid 7 days).
7.  Backend responds with tokens.
8.  Frontend saves tokens (e.g., in localStorage).

## 4. Protected Routes
Any view using `permission_classes = [IsAuthenticated]` requires the JWT.

```python
# Example in views.py
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated] # <--- The Guard
    
    def put(self, request):
        user = request.user # <--- Set by JWTAuthentication
        # ... update logic
```
