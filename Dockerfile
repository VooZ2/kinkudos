FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 10001 familyapp \
    && useradd --uid 10001 --gid familyapp --home-dir /app --no-create-home familyapp

COPY requirements.lock ./
RUN python -m pip install --requirement requirements.lock

COPY . .
RUN find /app -type d -name __pycache__ -prune -exec rm -rf -- {} + \
    && find /app -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete \
    && chmod -R a+rX /app \
    && chmod 0755 /app/docker/entrypoint.sh \
    && python scripts/verify_release.py \
    && python scripts/compile_translations.py \
    && KINKUDOS_DEBUG=true KINKUDOS_DATABASE_PATH=/tmp/kinkudos-build.sqlite3 \
        python manage.py makemigrations --check --dry-run \
    && KINKUDOS_DEBUG=true python manage.py collectstatic --noinput \
    && chown -R familyapp:familyapp /app

USER familyapp

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/docker/entrypoint.sh"]
CMD ["gunicorn", "kinkudos.wsgi:application", "--bind=0.0.0.0:8000", "--workers=2", "--threads=2", "--timeout=30", "--access-logfile=-", "--error-logfile=-", "--no-control-socket"]
