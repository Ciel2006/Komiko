# Komiko

Self-hosted comics library, inspired by Plex and Jellyfin, but for comics.

Point it at your folders of CBZ, EPUB, or image files, and it builds a browsable library with a built-in reader. No cloud, no accounts, no subscriptions. Your server, your comics.

---

## Features

- **Library management** — Create named libraries (Manga, Manhwa, Western Comics) pointing to any folder on your system
- **Automatic scanning** — Recursively detects CBZ, EPUB, and image folders, extracts chapter numbers from filenames
- **Built-in reader** — Switch between paginated (book-style) and continuous scroll (webtoon-style); keyboard/touch navigation
- **Cover thumbnails** — Auto-extracted from first page of each comic
- **Multi-user** — Admin accounts for managing the server, user accounts for family/friends
- **First-time setup wizard** — 3-step guided setup: admin account, first library, invite users
- **Dark theme** — Clean, minimal, mobile-first design. No RGB, no glassmorphism.
- **Collapsible sidebar** — Vertical nav, toggle on mobile
- **EPUB support** — Parses OPF spine for correct page order
- **Cross-platform** — Runs on Windows, Linux, Docker, LXC containers

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/komiko/komiko.git
cd komiko
cp .env.example .env          # Edit SECRET_KEY in .env
docker compose up -d
```

Open `http://localhost:5000` and follow the setup wizard.

Your comics folder needs to be mounted into the container. Edit `docker-compose.yml` to point `/comics` to your library:

```yaml
volumes:
  - /path/to/your/comics:/comics:ro
```

Then when creating a library in the UI, use `/comics` as the folder path.

### Debian 13 / LXC

```bash
git clone https://github.com/komiko/komiko.git
cd komiko
sudo bash setup-debian.sh
```

This installs Python, creates a system user, sets up a venv, generates a secret key, and installs a systemd service. Komiko starts on port 5000.

**Manage the service:**

```bash
sudo systemctl status komiko     # Check status
sudo systemctl restart komiko    # Restart
sudo systemctl stop komiko       # Stop
journalctl -u komiko -f          # View logs
```

**Update:**

```bash
cd komiko
git pull
sudo bash update-debian.sh
```

**Data location:** `/var/lib/komiko/` (database + covers)

### Windows

```cmd
git clone https://github.com/komiko/komiko.git
cd komiko
setup-windows.bat C:\Komiko
```

This creates a venv, installs dependencies, and generates a `start.bat`. Run `C:\Komiko\start.bat` to start the server.

**To run as a Windows Service** (auto-start on boot), use [NSSM](https://nssm.cc/):

```cmd
nssm install Komiko C:\Komiko\venv\Scripts\waitress-serve.exe
nssm set Komiko AppParameters "--host=0.0.0.0 --port=5000 --threads=4 run:app"
nssm set Komiko AppDirectory C:\Komiko
nssm set Komiko AppEnvironmentExtra FLASK_ENV=production SECRET_KEY=your-key-here KOMIKO_DATA_DIR=C:\Komiko\data
nssm start Komiko
```

### Manual (any OS)

```bash
git clone https://github.com/komiko/komiko.git
cd komiko
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows

pip install -r requirements.txt
python run.py
```

Open `http://localhost:5000`.

---

## Configuration

All settings are configurable via environment variables (or a `.env` file):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | Auto-generated hash | Session encryption key. Change in production. |
| `FLASK_ENV` | `development` | `development` or `production` |
| `KOMIKO_DATA_DIR` | `./data` | Where the database and cover thumbnails are stored |
| `KOMIKO_HOST` | `0.0.0.0` | Bind address |
| `KOMIKO_PORT` | `5000` | Bind port |
| `DATABASE_URL` | `sqlite:///data/komiko.db` | Database URI (only change if using external DB) |

---

## Library Folder Structure

Komiko expects your comics organized like this:

```
Library Root/
├── Comic Name/
│   ├── chapter 1.cbz
│   ├── ch.2.cbz
│   ├── 003.cbz
│   └── ch.4 - the return.cbz
├── Another Comic/
│   ├── Volume 1/
│   │   ├── ch.1.cbz
│   │   └── ch.2.cbz
│   └── Volume 2/
│       ├── ch.1.cbz
│       └── ch.2.cbz
└── Webtoon Title/
    ├── ch.1.epub
    └── ch.2.epub
```

**Rules:**
- Each **subfolder** of the library root = one comic series
- **CBZ files** inside = chapters (number extracted from filename)
- **EPUB files** inside = chapters (spine order preserved)
- **Image folders** = chapters (images sorted alphabetically)
- Nested subfolders (e.g. "Volume 1") are flattened into the parent comic

**Chapter number detection** (in order of priority):
1. `ch.1`, `ch.2`, `Ch.10` — matches `ch.` prefix
2. `chapter 1`, `Chapter 2` — matches "chapter" prefix
3. `001`, `002` — leading digits
4. Fallback: alphabetical order = chapter order

---

## Supported Formats

| Format | Status | Notes |
|---|---|---|
| **CBZ** | Supported | ZIP archives containing images |
| **EPUB** | Supported | Parses OPF manifest/spine for page order |
| **Image folders** | Supported | JPG, JPEG, PNG, WebP, GIF |
| **CBR** | Planned | RAR archives (requires `unrar`) |

---

## First-Time Setup

When you launch Komiko for the first time, a 3-step wizard walks you through:

1. **Create admin account** — Set a server name, username, and password
2. **Add a library** — Point Komiko to a folder of comics (or skip and add later)
3. **Invite users** — Add family/friends (or skip and add from admin panel later)

After setup, you can manage users, libraries, and settings from the admin panel (accessible via the sidebar).

---

## The Reader

The built-in reader supports two modes:

- **Paginated** — One page at a time. Navigate with arrow keys, spacebar, or tap the edges. Good for left-to-right comics.
- **Continuous scroll** — All pages stacked vertically. Swipe or scroll naturally. Good for manhwa/webtoons.

Toggle between modes with the button in the reader toolbar. You can also switch between fit-to-width and fit-to-height.

---

## Project Structure

```
Komiko/
├── app/
│   ├── __init__.py              # Flask app factory + auth middleware
│   ├── models.py                # SQLAlchemy models
│   ├── config.py                # Loaded from env vars
│   ├── routes/
│   │   ├── pages.py             # Web pages + image serving
│   │   ├── api.py               # Health check
│   │   ├── libraries.py         # Library CRUD + scan API
│   │   └── auth.py              # Setup, login, admin, user management
│   ├── services/
│   │   ├── scanner.py           # Recursive folder scanner
│   │   ├── comic_parser.py      # CBZ/EPUB extraction, covers
│   │   └── metadata.py          # AniList API (Phase 2)
│   ├── static/css/style.css     # Dark theme stylesheet
│   └── templates/                # Jinja2 HTML templates
├── config.py
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
├── komiko.service               # systemd unit
├── setup-debian.sh              # One-command Debian install
├── setup-windows.bat            # One-command Windows install
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Library listing page |
| `GET` | `/library/<id>` | Comic grid for a library |
| `GET` | `/comic/<id>` | Chapter list for a comic |
| `GET` | `/reader/<id>` | Built-in comic reader |
| `GET` | `/covers/<filename>` | Served cover thumbnail |
| `GET` | `/page_image/<id>` | Served comic page image |
| `GET` | `/auth/setup` | First-time setup wizard |
| `GET/POST` | `/auth/login` | Login page |
| `GET` | `/auth/logout` | Logout |
| `GET` | `/auth/admin` | Admin dashboard |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/libraries` | List all libraries (JSON) |
| `POST` | `/api/libraries` | Create a library |
| `GET` | `/api/libraries/<id>` | Get library details |
| `DELETE` | `/api/libraries/<id>` | Delete a library |
| `POST` | `/api/libraries/<id>/scan` | Scan library for comics |

---

## Tech Stack

- **Backend:** Python 3.11+, Flask, SQLAlchemy
- **Database:** SQLite (zero-config)
- **Auth:** Flask sessions + Werkzeug password hashing
- **Frontend:** Jinja2 templates + vanilla JavaScript
- **Reader:** Custom paginated/scroll viewer with touch support
- **WSGI:** Gunicorn (Linux/Docker) / Waitress (Windows)

---

## License

MIT