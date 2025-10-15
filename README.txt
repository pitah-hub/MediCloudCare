
MediCloudCare - Patient Management System (Flask)
------------------------------------------------
- Local dev: runs with SQLite by default.
- Production (Render): set DATABASE_URL env var to the Postgres URL provided by Render.
- Start locally: python app.py
- Start on Render: use start command 'gunicorn app:app'
- Remember to set FLASK_SECRET (env) in production.
