# API Reference

All endpoints are prefixed with `/api/v1/`. Authentication is via Bearer token in the `Authorization` header. The only public routes are the login / logout / refresh endpoints and the optional OIDC entry / callback endpoints. All other API routes require an authenticated session.

!!! note "Legacy `/api/` paths during the deprecation window"
    Unversioned `/api/...` requests return HTTP 308 Permanent Redirect to the matching `/api/v1/...` endpoint, with `Deprecation: true` and a `Sunset: Mon, 01 Jun 2026 00:00:00 GMT` header. New integrations should call `/api/v1/...` directly. After the Sunset date the redirect goes away.

## Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Login, get access token | Public |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Cookie |
| `POST` | `/api/v1/auth/logout` | Clear refresh cookie | Public |
| `GET` | `/api/v1/auth/oidc/login` | Start OIDC flow | Public |
| `GET` | `/api/v1/auth/oidc/callback` | OIDC callback | Public |
| `GET` | `/api/v1/users` | List users | Admin |
| `GET` | `/api/v1/users/reviewers` | List active reviewers | Admin / Reviewer |
| `GET` | `/api/v1/users/me` | Current user profile | Authenticated |
| `POST` | `/api/v1/users` | Create user | Admin |
| `PATCH` | `/api/v1/users/me` | Update own profile | Authenticated |
| `PATCH` | `/api/v1/users/{user_id}` | Update user | Admin |
| `GET` | `/api/v1/clients` | List clients | Authenticated |
| `POST` | `/api/v1/clients` | Create client | Admin / Reviewer |
| `GET` | `/api/v1/clients/{id}` | Get client | Authenticated |
| `PATCH` | `/api/v1/clients/{id}` | Update client | Admin / Reviewer |
| `GET` | `/api/v1/assets` | List assets | Authenticated |
| `POST` | `/api/v1/assets` | Create asset | Admin / Reviewer |
| `GET` | `/api/v1/assets/{id}` | Get asset | Authenticated |
| `PATCH` | `/api/v1/assets/{id}` | Update asset | Admin / Reviewer |
| `GET` | `/api/v1/sessions` | List sessions | Authenticated |
| `POST` | `/api/v1/sessions` | Create session | Admin / Reviewer |
| `GET` | `/api/v1/sessions/{id}` | Get session | Authenticated |
| `PATCH` | `/api/v1/sessions/{id}` | Update session | Admin / Reviewer |
| `GET` | `/api/v1/findings` | List findings (filterable) | Authenticated |
| `POST` | `/api/v1/findings` | Create finding | Admin / Reviewer |
| `GET` | `/api/v1/findings/{id}` | Get finding | Authenticated |
| `PATCH` | `/api/v1/findings/{id}` | Update finding | Admin / Reviewer |
| `GET` | `/api/v1/findings/{id}/history` | Get change history | Authenticated |
| `GET` | `/api/v1/findings/{id}/attachments` | List attachments | Authenticated |
| `POST` | `/api/v1/findings/{id}/attachments` | Upload file | Admin / Reviewer |
| `GET` | `/api/v1/attachments/{id}/download` | Download file | Authenticated |
| `DELETE` | `/api/v1/attachments/{id}` | Delete file | Admin / Reviewer |
| `GET` | `/api/v1/templates` | List templates | Authenticated |
| `POST` | `/api/v1/templates` | Create template | Admin / Reviewer |
| `GET` | `/api/v1/templates/{id}` | Get template | Authenticated |
| `PATCH` | `/api/v1/templates/{id}` | Update template | Admin / Reviewer |
| `DELETE` | `/api/v1/templates/{id}` | Delete template | Admin / Reviewer |
| `GET` | `/api/v1/taxonomy/current` | Get the active taxonomy version | Authenticated |
| `GET` | `/api/v1/taxonomy/versions` | List all taxonomy versions | Admin |
| `POST` | `/api/v1/taxonomy/versions` | Create and activate a new taxonomy version | Admin |
| `POST` | `/api/v1/taxonomy/activate` | Activate an existing taxonomy version | Admin |
| `GET` | `/api/v1/reports/sessions/{id}/pdf` | Download PDF report | Authenticated |
| `GET` | `/api/v1/reports/sessions/{id}/csv` | Download CSV export | Authenticated |
| `GET` | `/api/v1/reports/sessions/{id}/json` | Download JSON export | Authenticated |
| `GET` | `/api/v1/reports/sessions/{id}/exports` | List stored exports for a session | Authenticated |
| `GET` | `/api/v1/reports/exports/{id}/download` | Download a previously stored export artifact | Authenticated |
| `GET` | `/api/v1/health` | Health check | Authenticated |
| `GET` | `/api/v1/health/live` | Liveness probe (used by Docker healthcheck) | Public |

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

A live OpenAPI schema is served at `/api/v1/openapi.json` (currently authenticated; subject to change for public consumption). Swagger UI lives at `/api/v1/docs` and ReDoc at `/api/v1/redoc`. The frontend uses the live schema to generate typed API clients via `npm --prefix frontend run generate:types`.

For external consumers, an exported snapshot lives at `backend/openapi.generated.json` in the repository.
