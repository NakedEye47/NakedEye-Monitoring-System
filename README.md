# 👁️ NakedEye — AI-Powered Job Search & Monitoring System

> *"In a world full of blind spots — NakedEye gives you full visibility."* 👁️

> **Nothing is hidden from the Naked Eye.**

NakedEye is a self-built, full-stack monitoring and job search intelligence platform. It combines real-time portfolio visitor tracking, uptime monitoring, ATS detection, AI-powered resume analysis, and a complete job application pipeline — all in one dashboard.

## Demo

[![NakedEye Dashboard](./app/static/favicon.svg)](https://nakedeye47.github.io/NakedEye-Monitoring-System/)

---

## 🚀 Features

### 📊 Dashboard
- Real-time system overview
- Monitor status summary
- Incident tracking
- Response time metrics

### 📡 Uptime Monitoring
- HTTP, Ping, and Docker container checks
- Configurable check intervals and timeouts
- Incident detection and alerting
- SSL certificate expiry tracking
- Response time history

### 👁️ Visitor Analytics
- Real-time portfolio visitor tracking
- Location and IP tracking
- Session timeline and event logging
- Live activity feed with auto-refresh

### 💼 Job Pipeline
- **ATS Detector** — Detects 50+ ATS systems (Workday, Greenhouse, SAP SuccessFactors, iCIMS, Lever, and more) with confidence scoring
- **Application Strength Analyzer** — AI-powered resume vs job description keyword matching
- **Email Tracking** — Pixel-based email open tracking for follow-up and application emails
- **Send Application** — Send professional application emails with resume attachment directly from the dashboard
- **Follow-up Generator** — AI-generated follow-up email drafts
- **Job Pipeline Board** — Track applications from Applied → Screening → Interview → Offer

### 🔔 Notifications
- Email alerts (SMTP/Gmail)
- SMS alerts (Semaphore)
- Telegram alerts
- Configurable alert thresholds

### 📈 Additional Features
- Social Media Tracker (YouTube & Facebook)
- Uptime Reports (CSV export)
- Maintenance Windows scheduling
- Response Time analytics
- Public Status Page

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, SQLAlchemy |
| **Database** | PostgreSQL 16 |
| **Frontend** | Vanilla HTML/CSS/JavaScript |
| **Containerization** | Docker, Docker Compose |
| **Email** | SMTP (Gmail) |
| **SMS** | Semaphore API |
| **Tunnel** | ngrok (permanent URL) |
| **Scheduling** | APScheduler |
| **AI Integration** | Anthropic Claude API |

---

## 📁 Project Structure

```
nakedeye/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── analytics.py        # Visitor analytics endpoints
│   │   ├── jobs.py             # Job pipeline, ATS detector, strength analyzer
│   │   ├── monitors.py         # Monitor management
│   │   ├── settings.py         # App settings
│   │   └── social.py           # Social media tracking
│   ├── checker/
│   │   ├── __init__.py
│   │   ├── docker_checker.py   # Docker container health checks
│   │   ├── facebook_checker.py # Facebook page monitoring
│   │   ├── http_checker.py     # HTTP uptime checks
│   │   ├── ping_checker.py     # Ping checks
│   │   ├── scheduler.py        # Check scheduler
│   │   └── youtube_checker.py  # YouTube channel monitoring
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py         # SQLAlchemy models
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_sender.py     # Email alert sender
│   │   ├── sms_sender.py       # SMS alert sender
│   │   └── telegram_sender.py  # Telegram alert sender
│   ├── static/
│   │   ├── favicon.svg
│   │   ├── index.html          # Main dashboard
│   │   ├── login.html          # Login page
│   │   ├── manifest.json
│   │   ├── public-status.html  # Public status page
│   │   ├── sw.js               # Service worker
│   │   └── tracker.js          # Portfolio visitor tracker
│   ├── __init__.py
│   ├── config.py               # App configuration
│   ├── main.py                 # FastAPI app entry point
│   ├── main_notifications_routes.py
│   └── notifications.py
├── tests/
├── .env                        # Environment variables (not committed)
├── .env.example                # Environment variables template
├── .gitignore
├── docker-compose.yml          # Docker services
├── Dockerfile                  # App container
├── migrate.py                  # Database migrations
├── requirements.txt            # Python dependencies
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/)
- [ngrok](https://ngrok.com/) (for public URL)
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/nakedeye.git
cd nakedeye
```

---

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://nakedeye:secret@db:5432/nakedeye

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# Admin credentials
ADMIN_USERNAME=your-username
ADMIN_PASSWORD=your-password

# Session
SESSION_COOKIE_SECURE=false  # Set to true in production

# CORS
ALLOWED_HOSTS=localhost,127.0.0.1,::1
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Public URL (ngrok or your domain)
PUBLIC_BASE_URL=https://your-ngrok-url.ngrok-free.dev

# Email Notifications (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-gmail-app-password
ALERT_EMAIL_TO=alert-recipient@gmail.com

# SMS Notifications (Semaphore)
SEMAPHORE_API_KEY=your-semaphore-api-key
ALERT_SMS_TO=your-phone-number

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Social Monitoring (Optional)
YOUTUBE_API_KEY=your-youtube-api-key
YOUTUBE_CHANNEL_ID=your-channel-id
FACEBOOK_PAGE_ID=your-page-id
FACEBOOK_ACCESS_TOKEN=your-facebook-token
```

---

### 3. Build and Run with Docker

```bash
docker compose up --build -d
```

This will start:
- **nakedeye-api-1** — FastAPI backend on port 8000
- **nakedeye-db-1** — PostgreSQL database on port 5432

---

### 4. Access the Dashboard

Open your browser and navigate to:

```
http://localhost:8000
```

Login with your `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`

---

### 5. Set Up ngrok (For Public URL)

NakedEye requires a public URL for:
- Email open tracking pixels
- Portfolio visitor tracking
- External webhook callbacks

**Install ngrok:**
```bash
# Windows
winget install ngrok

# macOS
brew install ngrok

# Linux
snap install ngrok
```

**Authenticate ngrok:**
```bash
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

**Start ngrok tunnel:**
```bash
ngrok http 8000
```

Copy your ngrok URL and update `PUBLIC_BASE_URL` in `.env`:
```env
PUBLIC_BASE_URL=https://your-url.ngrok-free.dev
```

Restart the containers:
```bash
docker compose restart api
```

---

### 6. Add Portfolio Visitor Tracking

Add the tracker script to your portfolio website's HTML:

```html
<script>
  (function() {
    const NAKEDEYE_URL = 'https://your-ngrok-url.ngrok-free.dev';
    const API_KEY = 'your-api-key';
    // tracker.js handles the rest
  })();
</script>
<script src="https://your-ngrok-url.ngrok-free.dev/static/tracker.js"></script>
```

---

## 🔧 Docker Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild and restart
docker compose up --build -d

# Restart specific service
docker compose restart api

# View logs
docker compose logs -f api

# View database logs
docker compose logs -f db

# Access PostgreSQL directly
docker exec -it nakedeye-db-1 psql -U nakedeye -d nakedeye
```

---

## 📧 Email Setup (Gmail)

1. Enable **2-Factor Authentication** on your Gmail account
2. Go to **Google Account → Security → App Passwords**
3. Generate an app password for "Mail"
4. Use that password as `SMTP_PASS` in `.env`

---

## 🤖 ATS Detection

NakedEye detects **50+ Applicant Tracking Systems** including:

| ATS | Detection Method |
|-----|-----------------|
| Workday | URL pattern + page inspection |
| SAP SuccessFactors | URL pattern + page inspection |
| Greenhouse | URL pattern + page inspection |
| Lever | URL pattern + page inspection |
| iCIMS | URL pattern + page inspection |
| Oracle Taleo | URL pattern + page inspection |
| SmartRecruiters | URL pattern + page inspection |
| BambooHR | URL pattern + page inspection |
| LinkedIn Jobs | URL pattern |
| Indeed | URL pattern |
| ...and 40+ more | |

Each detected ATS provides **tailored resume tips** to maximize your application success.

---

## 📊 Resume Strength Analyzer

The strength analyzer:
1. Extracts keywords from the job description dynamically
2. Matches them against your resume intelligently
3. Provides a score with matched/missing keywords
4. Suggests quick wins to improve your score
5. Works for **any job posting** — not hardcoded

---

## 🔒 Security

- Session-based authentication
- Configurable CORS origins
- API key protection for tracker endpoints
- Secure cookie settings for production
- Bot detection for email tracking

---

## 🐛 Troubleshooting

**Database connection error:**
```bash
# Check if database is running
docker compose ps

# Check database logs
docker compose logs db
```

**API not starting:**
```bash
# Check API logs
docker compose logs api

# Rebuild the container
docker compose up --build -d
```

**ngrok not working:**
```bash
# Make sure ngrok is running
ngrok http 8000

# Update PUBLIC_BASE_URL in .env
# Restart the API container
docker compose restart api
```

---

## 📝 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | Session secret key |
| `API_KEY` | ✅ | Tracker API key |
| `ADMIN_USERNAME` | ✅ | Dashboard login username |
| `ADMIN_PASSWORD` | ✅ | Dashboard login password |
| `PUBLIC_BASE_URL` | ✅ | Public ngrok/domain URL |
| `SMTP_HOST` | ⚠️ | SMTP server host |
| `SMTP_PORT` | ⚠️ | SMTP server port |
| `SMTP_USER` | ⚠️ | SMTP email address |
| `SMTP_PASS` | ⚠️ | SMTP app password |
| `ALERT_EMAIL_TO` | ⚠️ | Alert recipient email |
| `SEMAPHORE_API_KEY` | ❌ | SMS notifications |
| `TELEGRAM_BOT_TOKEN` | ❌ | Telegram notifications |
| `YOUTUBE_API_KEY` | ❌ | YouTube monitoring |
| `FACEBOOK_ACCESS_TOKEN` | ❌ | Facebook monitoring |

✅ Required | ⚠️ Required for feature | ❌ Optional

---

## 🙏 Built With

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [PostgreSQL](https://www.postgresql.org/) — Database
- [Docker](https://www.docker.com/) — Containerization
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
- [APScheduler](https://apscheduler.readthedocs.io/) — Task scheduling
- [ngrok](https://ngrok.com/) — Public tunnel

---

## 👨‍💻 Author

**Alexander E. Sugian**
- 🌐 Portfolio: [portfolio-eosin-tau-91.vercel.app](https://portfolio-eosin-tau-91.vercel.app)
- 💼 LinkedIn: [linkedin.com/in/alexanderdgreat](https://linkedin.com/in/alexanderdgreat)
- 🐙 GitHub: [github.com/NakedEye47](https://github.com/NakedEye47)

---

## 📄 License

© 2026 Alexander E. Sugian. All Rights Reserved.

This project and its source code are made publicly available for **portfolio and demonstration purposes only.**

You may:
- ✅ View and inspect the source code
- ✅ Reference the code for learning purposes

You may NOT:
- ❌ Copy, reproduce, or distribute this project
- ❌ Use this code commercially or privately without written permission
- ❌ Claim this project as your own

For inquiries or permissions, contact: **alexander.s.dgreat@gmail.com**

---

> *"Most job applicants are blind after submitting their application. NakedEye gives you full visibility."* 👁️
