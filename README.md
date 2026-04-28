## Local setup (MySQL in Docker + Django)

### Prerequisites
Install:
- Git
- Python 3.x (verify with `python --version`)
- Docker Desktop (so `docker compose` works) or docker CLI

---

### Run this if you are on MacOS
#### Docker CLI (macOS) install

If you are on macOS and are unable to install Docker Desktop, you need to use Homebrew to install docker and run from the command line.

#### 1) Installing Homebrew
Run this command:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Visit https://brew.sh/ for more information about Homebrew

#### 2) Installing pre-requisites
```bash
brew update && brew upgrade && brew install docker docker-compose colima
```

After running these commands start Colima to run Docker

#### 3) Running docker
```bash
colima start
```

If Colima fails to run, the download might have failed. Run the command again until Colima starts.

### First-time setup

> **IMPORTANT:** Run all `python manage.py ...` commands from the project root (the folder that contains `manage.py`).

#### 1) Clone the repo
```console
git clone <repo-url>
cd patient-portal
```

#### 2) Create a virtual environment (first time only)
```console
python -m venv .venv
```

#### 3) Activate the virtual environment

> **VS Code note (important):**  
> If you use VS Code and select the correct interpreter, you don’t need to activate `(.venv)` in the terminal just to run/debug inside VS Code.
>
> **Select interpreter:**  
> VS Code → Command Palette → **Python: Select Interpreter**  
> Choose: `...\patient-portal\.venv\Scripts\python.exe`
>
> If you see **“import pymysql could not be resolved”**, VS Code is almost always using the wrong interpreter.  
> Select the `.venv` interpreter and reload the window.

#### 3a) Activate using PowerShell (Windows Users)
Activate in PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Depending on the Python install, a Scripts folder may not exist. If the Scripts folder does not exist, check `.venv\bin\Activate.ps1` for the activation script.

If PowerShell blocks activation, run this once per terminal session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### 3b) Activate using shell (Linux and MacOS)
```console
source .venv\bin\activate
```

After activation you should see `(.venv)` at the left of your prompt.

#### 4) Install Python dependencies
```console
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Quick sanity check:
```console
python -c "import django; print(django.get_version())"
```

#### 5) Create `.env` from the example
- `.env` is local-only (gitignored).
- **Do not modify `.env` unless instructed** — the default values work for local development.

```console
cp .env.example .env
```

#### IMPORTANT Docker/MySQL notes
- Docker Desktop must be running (Docker Engine/WSL backend started) before `docker compose` will work.  
  If you get errors like **“cannot connect” / “file not found” / “daemon not running”**, open Docker Desktop and try again.
- If port **3306** is already in use, MySQL may fail to start. Close other MySQL/XAMPP services or change the mapped port.
- If `python manage.py migrate` fails with a MySQL connection error, confirm the container is running:
  ```powershell
  docker compose ps
  ```
  Then wait ~10–20 seconds and try again.  
  (Optional) View logs:
  ```powershell
  docker compose logs mysql
  ```

#### 6) Start MySQL (Docker)
```console
docker-compose up -d
docker-compose ps
```

You should see the `mysql` container running.

#### 7) Run migrations (build/update schema)
```console
python manage.py migrate
```

#### 8) Create an admin user (first time per machine / fresh DB)
```console
python manage.py createsuperuser
```

#### 9) Run the Django server
```console
python manage.py runserver
```

Stop the server: press **Ctrl + C** in the terminal.

#### 10) Open the site in your browser
- Login: `http://127.0.0.1:8000/accounts/login/`
- Dashboard: `http://127.0.0.1:8000/dashboard/`

---

## Common commands (daily use)

### Start everything
> Only activate `.venv` if you’re running commands in PowerShell.  
> If VS Code is using the `.venv` interpreter, activation may not be necessary.

```powershell
.\.venv\Scripts\Activate.ps1
docker compose up -d
python manage.py migrate
python manage.py runserver
```

Then navigate to the appropriate local URL (e.g., `http://127.0.0.1:8000/accounts/login/`) in your browser.

### Stop MySQL when you’re done (saves RAM/CPU)
```powershell
docker compose down
```

---

## Terminal prompt gotchas (when things suddenly look “stuck”)

### If you see `>>>`
You are inside the Python interactive shell (REPL), not running normal terminal commands.

Exit it with:
```text
exit()
```
or:
```text
quit()
```
or (Windows):
```text
Ctrl + Z, then Enter
```

### If you see `>>` in PowerShell
PowerShell thinks your previous command is incomplete (commonly an unclosed quote `"` or an unclosed bracket/parenthesis).

Cancel the incomplete command with:
```text
Ctrl + C
```
Then re-type the command carefully.

Seed User:
username: alice, bob, frontdesk, drlee
Password for all useranme is : DevPass123!