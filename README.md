# NakedEye Monitoring System
### v1.0.0 · Real-time Uptime & Performance Monitoring

NakedEye is a self-hosted monitoring dashboard that tracks the uptime, response time, and SSL status of your websites, APIs, and social media pages — all in one place.

---

## Features

- **Real-time Monitoring** — Tracks HTTP endpoints, APIs, and social media pages
- **Uptime Dashboard** — Visual overview of all monitors with live status
- **Response Time Tracking** — Monitors average response times across all endpoints
- **SSL Certificate Monitoring** — Tracks SSL expiry dates for all your domains
- **Incident Management** — Logs and tracks incidents automatically
- **Visitor Analytics** — Built-in analytics for your monitored sites
- **Notifications** — Alerts via Email, SMS, and Telegram
- **Job Pipeline** — Built-in job tracking and management
- **Public Status Page** — Share a public status page with your users
- **Docker Support** — Easy deployment with Docker and Docker Compose

---

## Tech Stack

- **Backend** — Python (FastAPI)
- **Database** — PostgreSQL (via SQLAlchemy + Alembic)
- **Frontend** — HTML, CSS, JavaScript
- **Containerization** — Docker, Docker Compose
- **Notifications** — Email, SMS, Telegram

---

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Installation

1. Clone the repository:
```bash
git clone https://github.com/NakedEye47/NakedEye-Monitoring-System.git
cd NakedEye-Monitoring-System
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Start the application:
```bash
sudo service docker start
docker-compose up -d
```

4. Access the dashboard at `http://localhost:8000`

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

---

## Security

See [SECURITY_HARDENING.md](SECURITY_HARDENING.md) for security best practices and hardening guidelines.

---

## License

This project is private and proprietary. All rights reserved.

---

*Built by [NakedEye47](https://github.com/NakedEye47)*
