# Sentinel AI v1.0.0 — Environment Variables Reference

| Variable Name | Default / Example | Required | Description |
|---|---|---|---|
| `PROJECT_TITLE` | `Sentinel AI` | No | Application display title |
| `PROJECT_VERSION` | `1.0.0` | No | Control plane release version |
| `API_V1_PREFIX` | `/api/v1` | No | REST API endpoint prefix |
| `DATABASE_URL` | `sqlite+aiosqlite:///./sentinel.db` | Yes | PostgreSQL / SQLite database connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | No | Redis connection URL |
| `JWT_SECRET_KEY` | `change_me_super_secret_jwt_key` | Yes | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | No | JWT signature algorithm |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Yes | Allowed client origins for CORS |
| `OPENAI_API_KEY` | `sk-...` | Optional | OpenAI API Key |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Optional | Anthropic API Key |
| `GEMINI_API_KEY` | `AIzaSy...` | Optional | Google Gemini API Key |
