# API Reference

All endpoints are prefixed with `/api`. Authentication is via Bearer token in the `Authorization` header. The only public routes are the login / logout / refresh endpoints and the optional OIDC entry / callback endpoints. All other API routes require an authenticated session.

## Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/login` | Login, get access token | Public |
| `POST` | `/api/auth/refresh` | Refresh access token | Cookie |
| `POST` | `/api/auth/logout` | Clear refresh cookie | Public |
| `GET` | `/api/auth/oidc/login` | Start OIDC flow | Public |
| `GET` | `/api/auth/oidc/callback` | OIDC callback | Public |
| `GET` | `/api/users` | List users | Admin |
| `GET` | `/api/users/reviewers` | List active reviewers | Admin / Reviewer |
| `GET` | `/api/users/me` | Current user profile | Authenticated |
| `POST` | `/api/users` | Create user | Admin |
| `PATCH` | `/api/users/me` | Update own profile | Authenticated |
| `PATCH` | `/api/users/{user_id}` | Update user | Admin |
| `GET` | `/api/clients` | List clients | Authenticated |
| `POST` | `/api/clients` | Create client | Admin / Reviewer |
| `GET` | `/api/clients/{id}` | Get client | Authenticated |
| `PATCH` | `/api/clients/{id}` | Update client | Admin / Reviewer |
| `GET` | `/api/assets` | List assets | Authenticated |
| `POST` | `/api/assets` | Create asset | Admin / Reviewer |
| `GET` | `/api/assets/{id}` | Get asset | Authenticated |
| `PATCH` | `/api/assets/{id}` | Update asset | Admin / Reviewer |
| `GET` | `/api/sessions` | List sessions | Authenticated |
| `POST` | `/api/sessions` | Create session | Admin / Reviewer |
| `GET` | `/api/sessions/{id}` | Get session | Authenticated |
| `PATCH` | `/api/sessions/{id}` | Update session | Admin / Reviewer |
| `GET` | `/api/findings` | List findings (filterable) | Authenticated |
| `POST` | `/api/findings` | Create finding | Admin / Reviewer |
| `GET` | `/api/findings/{id}` | Get finding | Authenticated |
| `PATCH` | `/api/findings/{id}` | Update finding | Admin / Reviewer |
| `GET` | `/api/findings/{id}/history` | Get change history | Authenticated |
| `GET` | `/api/findings/{id}/attachments` | List attachments | Authenticated |
| `POST` | `/api/findings/{id}/attachments` | Upload file | Admin / Reviewer |
| `GET` | `/api/attachments/{id}/download` | Download file | Authenticated |
| `DELETE` | `/api/attachments/{id}` | Delete file | Admin / Reviewer |
| `GET` | `/api/templates` | List templates | Authenticated |
| `POST` | `/api/templates` | Create template | Admin / Reviewer |
| `GET` | `/api/templates/{id}` | Get template | Authenticated |
| `PATCH` | `/api/templates/{id}` | Update template | Admin / Reviewer |
| `DELETE` | `/api/templates/{id}` | Delete template | Admin / Reviewer |
| `GET` | `/api/taxonomy/current` | Get the active taxonomy version | Authenticated |
| `GET` | `/api/taxonomy/versions` | List all taxonomy versions | Admin |
| `POST` | `/api/taxonomy/versions` | Create and activate a new taxonomy version | Admin |
| `POST` | `/api/taxonomy/activate` | Activate an existing taxonomy version | Admin |
| `GET` | `/api/reports/sessions/{id}/pdf` | Download PDF report | Authenticated |
| `GET` | `/api/reports/sessions/{id}/csv` | Download CSV export | Authenticated |
| `GET` | `/api/reports/sessions/{id}/json` | Download JSON export | Authenticated |
| `GET` | `/api/reports/sessions/{id}/exports` | List stored exports for a session | Authenticated |
| `GET` | `/api/reports/exports/{id}/download` | Download a previously stored export artifact | Authenticated |
| `GET` | `/api/health` | Health check | Authenticated |
| `GET` | `/api/health/live` | Liveness probe (used by Docker healthcheck) | Public |

## Pagination

All list endpoints support pagination via `?page=N&per_page=M` and return:

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 25,
  "pages": 2
}
```

## OpenAPI schema

A live OpenAPI schema is served at `/openapi.json` (currently authenticated; subject to change for public consumption). The frontend uses it to generate typed API clients via `npm --prefix frontend run generate:types`.

For external consumers, an exported snapshot lives at `backend/openapi.generated.json` in the repository.
