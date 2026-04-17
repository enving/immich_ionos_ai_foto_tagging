# Immich Server with IONOS AI Integration

Self-hosted photo management with Docker, enhanced with AI-powered multimodal indexing via IONOS AI Model Hub.

## Overview

This repo provides a production-ready Immich (self-hosted Google Photos alternative) setup with:

- **Docker Compose** deployment for simple startup
- **IONOS Multimodal AI** integration for automatic image tagging and description
- **PostgreSQL** local database
- **Troubleshooting guides** for common issues

## Quick Start

```bash
# 1. Copy and edit environment
cp .env.example .env
# Edit .env with your settings

# 2. Start Immich
docker compose up -d

# 3. Access at http://localhost:2283
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_LOCATION` | Where photos are stored | `./library` |
| `DB_DATA_LOCATION` | PostgreSQL data path | `./postgres` |
| `IMMICH_VERSION` | Immich version | `release` |
| `DB_PASSWORD` | Database password | (set your own) |

## IONOS AI Integration

Images are automatically indexed using IONOS Multimodal AI (Mistral-based). See `ionos_multimodal_indexing/README.md` for setup instructions.

### Setup

1. Get an IONOS Cloud API key from [IONOS AI Model Hub](https://ionos.com/ai)
2. Install dependencies: `pip3 install requests psycopg2-binary python-dotenv Pillow`
3. Configure `.env` with your API keys:

```bash
IONOS_API_KEY=your_key
IONOS_API_URL=https://openai.inference.de-txl.ionos.com/v1
IONOS_MODEL=mistralai/Mistral-Small-24B-Instruct
```

4. Run indexing: `cd ionos_multimodal_indexing && python3 index_images.py`

Or automate via cron (see `ionos_multimodal_indexing/run_indexing.sh`).

## Project Structure

```
.
├── .env                    # Environment config (DO NOT COMMIT)
├── docker-compose.yml       # Immich + PostgreSQL
├── library/             # Photo storage (gitignored)
├── postgres/            # Database storage (gitignored)
├── ionos_multimodal_indexing/
│   ├── index_images.py  # Main AI indexing script
│   ├── trigger_immich_scan.py
│   └── run_indexing.sh  # Cron wrapper
├── TROUBLESHOOTING-IMMICH.md
└── scripts/
    └── immich-doctor.sh
```

## Troubleshooting

- **Immich not starting?** See `TROUBLESHOOTING-IMMICH.md`
- **Container unhealthy?** Check Postgres logs: `docker compose logs immich_postgres`
- **Missing photos?** Verify `UPLOAD_LOCATION` matches where your photos are

## Security Notes

- Change `DB_PASSWORD` in `.env` to a secure random password
- Keep `.env` out of version control (already in `.gitignore`)
- IONOS API keys should also stay local

## References

- [Immich Docs](https://docs.immich.app)
- [IONOS AI Model Hub](https://ionos.com/ai)