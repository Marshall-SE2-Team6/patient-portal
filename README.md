# Patient Portal (SE2)

Django web application for our Software Engineering II group project.

## Repo Layout (Conventions)

- `config/` — Django project package (settings, root URLs, ASGI/WSGI)
- `apps/` — Django apps live here (e.g., `apps/accounts/`)
- `templates/` — global templates
- `static/` — global static files
- `media/` — uploads (kept local; not committed)
- `.venv/` — local virtual environment (not committed)

## Requirements

- Python 3.x
- Git

## Quick Start (Windows PowerShell)

```powershell
git clone https://github.com/Marshall-SE2-Team6/patient-portal.git
cd patient-portal

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/  
Stop server: `Ctrl + C`

## Quick Start (macOS / Linux)

```bash
git clone https://github.com/Marshall-SE2-Team6/patient-portal.git
cd patient-portal

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Contributing

See `CONTRIBUTING.md` for the branch + PR workflow.




