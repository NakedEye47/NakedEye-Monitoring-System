# NakedEye Web Security Checklist

Use these settings before exposing NakedEye through a domain, reverse proxy, or tunnel.

## Required `.env` settings

```env
ADMIN_USERNAME=your-admin-name
ADMIN_PASSWORD=use-a-long-random-password
SECRET_KEY=use-a-different-long-random-secret
API_KEY=use-a-different-long-random-api-key
SESSION_COOKIE_SECURE=true
ALLOWED_HOSTS=nakedeye.yourdomain.com
ALLOWED_ORIGINS=https://nakedeye.yourdomain.com
```

For local-only development, `SESSION_COOKIE_SECURE=false` is okay. For HTTPS public access, set it to `true`.

## Public routes

These routes are intentionally public:

- `/status`
- `/api/public/status`
- `/api/jobs/email-open/{tracking_pixel_id}.gif`
- `/health`

The private dashboard and private `/api` routes require login.

## Deployment notes

- Put NakedEye behind HTTPS.
- Do not expose Postgres publicly.
- Do not share `.env` files or screenshots containing secrets.
- Rotate any secret that was pasted into a chat or screenshot.
- Keep the Docker socket mount read-only. It is currently required for Docker monitoring.
- Set `ALLOWED_HOSTS` to your real domain before public exposure.
- Use strong unique passwords for `ADMIN_PASSWORD`, `SECRET_KEY`, and `API_KEY`.
