# Mechanic Shop API — Deployment and CI/CD

A Flask API for customers, mechanics, service tickets, and inventory. This final coursework stage adds Render deployment and a GitHub Actions build/test/deploy pipeline while retaining the earlier authentication, documentation, and testing fixes.

- Repository: https://github.com/shadowless005/mechanic-shop-api-cicd
- Live API: https://mechanic-shop-api-cicd.onrender.com
- Live Swagger: https://mechanic-shop-api-cicd.onrender.com/api/docs/
- JSON specification: https://mechanic-shop-api-cicd.onrender.com/api/swagger.json
- Database health: https://mechanic-shop-api-cicd.onrender.com/health

These are the configured URLs. Verify a completed deployment and working responses before presenting them as live.

## Local setup

Python 3.14 is used by CI. From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with a disposable local database URL and a newly generated secret. Do not commit it. Example local URI: `sqlite:///mechanic_shop_cicd_demo.db`. To generate a secret locally: `python3 -c 'import secrets; print(secrets.token_hex(32))'`. Keep the resulting value private.

The assignment asks you to install python-dotenv locally and remove it from the final requirements. You may install it with `python3 -m pip install python-dotenv`. The committed requirements deliberately omit it; production does not depend on .env loading. If you run `pip freeze > requirements.txt`, remove the python-dotenv line again and review the diff before committing.

Explicitly load your local `.env` in the terminal:

```bash
set -a
source .env
set +a
python3 -m flask --app 'application:create_app()' upgrade-db
python3 -m flask --app 'application:create_app()' run --port 5001
```

Port 5001 allows the previous documentation project to keep using port 5000. Open http://127.0.0.1:5001/api/docs/. Local JSON documentation overrides host/scheme to this server, so Try it out does not write to Render. Production YAML retains the live hostname without `https://` and uses the `https` scheme.

## Tests

```bash
python3 -m unittest discover tests
```

The suite includes the earlier 53 endpoint/security tests and nine deployment checks (62 total). Tests use isolated in-memory SQLite. The deployment checks cover configuration, PostgreSQL URI normalization, local/live Swagger targeting, the schema upgrade, legacy password reset, health behavior, and workflow dependencies. A passing suite does not prove that the remote Render database or deployment is configured; verify those separately below.

## Production entry point and configuration

`flask_app.py` creates `app = create_app(ProductionConfig)` and does not call `app.run()`. Gunicorn serves that app. `config.py` reads `DATABASE_URL` and `SECRET_KEY` with `os.getenv`; production refuses missing settings or a SQLite fallback. Render PostgreSQL URLs are normalized to the installed `psycopg2` driver.

`requirements.txt` includes Gunicorn and `psycopg2-binary`, whose import/module is `psycopg2`. The binary distribution avoids requiring PostgreSQL compiler tools on the local Mac. python-dotenv is deliberately absent from production requirements.

## Render setup — complete before pushing the update

1. Create or reuse a Render PostgreSQL database and web service linked to this repository's `main` branch. Use the same region for both.
2. Set the web service's `DATABASE_URL` to that database's **Internal Database URL**. Set `SECRET_KEY` to a long random value. Do not paste secrets into source code, screenshots, or the presentation.
3. Set **Auto-Deploy to Off** so GitHub Actions controls deployment after tests. A separate On Commit deployment would bypass that gate.
4. Set Build Command to `pip install -r requirements.txt`.
5. Set Start Command to:

```bash
python -m flask --app flask_app upgrade-db && gunicorn flask_app:app --bind 0.0.0.0:$PORT
```

6. Set the health check path to `/health`. Use Python 3.14 (the repository pins a patch version in `.python-version`).
7. In GitHub repository Settings → Secrets and variables → Actions, add repository secrets `SERVICE_ID` and `RENDER_API_KEY`. SERVICE_ID is the Render web service ID, not the database ID. Keep values private.
8. Push the reviewed update to `main`. Watch all three GitHub Actions jobs, then check Render's deployment status and matching commit.

If changing Render settings offers to deploy immediately before the new files are pushed, save without deploying when available. Do not run the new upgrade-db start command against the old code. After pushing, use the workflow to trigger the new version.

### Database upgrade and existing accounts

`upgrade-db` creates missing tables and adds `customers.is_staff` to an existing database with default false. It preserves rows and passwords and is safe to rerun. It runs once in the start command before Gunicorn starts, not separately in every worker. This is the focused migration for this coursework update, not a general migration framework.

New registrations are regular customers and passwords are hashed. Existing plaintext accounts cannot log in until their passwords are reset. Do not delete the database to fix this. In a trusted Render shell, after deployment:

```bash
python -m flask --app flask_app reset-password --email EXISTING-DEMO-EMAIL
```

Enter a new disposable password twice. The command changes only that account's password and leaves its role unchanged. Reset any retained legacy accounts before using them; do not describe existing plaintext records as already migrated.

To create a new demo staff account from a trusted Render shell:

```bash
python -m flask --app flask_app create-staff --email staff-demo@example.com --phone 4075559801
```

Enter a disposable password when prompted. Existing emails/phones are not overwritten. If Render Shell is unavailable on your plan, use a trusted local terminal with the database's **External Database URL** (TLS as required) and production environment variables, then run the same command; never share those values. Staff creation is optional for the final read-only live demo.

The staff account from the previous local documentation project does not automatically exist in the Render database.

## CI/CD behavior

`.github/workflows/main.yaml` triggers on pushes and pull requests to main, or manual dispatch.

1. **build:** creates dependency wheels and uploads the wheelhouse artifact.
2. **test:** depends on build, downloads and installs those wheels, and runs unittest discovery.
3. **deploy:** has `needs: test`, only runs on main outside pull requests, and requests the exact tested commit from Render using GitHub secrets. HTTP errors fail the request step.

A green deploy job means Render accepted the API request. It does not mean the remote build has finished. Confirm Render shows the matching commit as Live before recording. Auto-Deploy must remain Off to avoid independent untested deployments.

## Access rules and error handling

| Routes | Access |
| --- | --- |
| Register / log in | Public |
| Customer directory | Staff only; authentication precedes caching |
| Customer record by ID | Owner or staff |
| Customer update/delete, my-tickets | Logged-in customer |
| Create ticket | Owner; staff can create for any existing customer |
| List tickets | Own tickets; staff see all |
| Ticket mechanic assignments / inventory attachment | Staff only |
| Mechanic and inventory writes | Staff only |
| Mechanic and inventory reads | Public |

Passwords are hashed on creation/update and excluded from responses. Registration cannot set roles or IDs. Deleted-account tokens are rejected. Invalid bodies return 400, missing records 404, and duplicate email/phone conflicts 409. A customer with service tickets cannot be deleted (409). Mechanic assignment lists validate all IDs before changing relationships. The older Postman collection, if retained, needs staff bearer tokens for newly protected writes; Swagger is the maintained demo interface for this update.

## Verification and presentation

After Render shows Live:

- GET `/health`: expect 200 with `status: ok` and `database: connected`.
- Open live `/api/docs/`; confirm the base URL is the Render host and HTTPS.
- GET `/inventory/`: expect 200 and a JSON array (an empty array is valid).
- GET `/inventory/999999`: expect 404 if that ID does not exist.
- Show the completed Actions build/test/deploy jobs and matching Render commit.

Use disposable demo data only. This coursework release is not a production security certification; rate-limit storage and the simple cache remain process-local, and public mechanic reads expose the documented fields. Those deployment-scale policies are outside this assignment.

Submit the repository root URL, deployed service URL, and a video uploaded directly to Disco. Keep yourself visible on camera and finish below five minutes.

## References

- https://render.com/docs/deploy-flask
- https://render.com/docs/deploys
- https://api-docs.render.com/reference/create-deploy

Author: Matthew Shin
