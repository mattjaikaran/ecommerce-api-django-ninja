#!/bin/bash
set -e

wait_for() {
    local host="$1" port="$2" name="$3"
    echo "Waiting for $name at $host:$port..."
    until nc -z "$host" "$port"; do sleep 1; done
    echo "$name is ready."
}

# Wait for dependencies
[ -n "$DB_HOST" ] && [ -n "$DB_PORT" ] && wait_for "$DB_HOST" "$DB_PORT" "PostgreSQL"

if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|.*://([^:@]+).*|\1|; s|.*@([^:]+).*|\1|')
    REDIS_PORT=$(echo "$REDIS_URL" | grep -oE ':[0-9]+/' | tr -d ':/')
    [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ] && wait_for "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Skip migrate/collectstatic for Celery and Flower processes
case "$*" in
    celery*|flower*)
        exec "$@"
        ;;
esac

echo "Running migrations..."
python manage.py migrate --noinput

# Collect static only in production
if [ "${DEBUG:-1}" = "0" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Create superuser if credentials provided (idempotent)
if [ -n "$SUPERUSER_EMAIL" ] && [ -n "$SUPERUSER_PASSWORD" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(email='$SUPERUSER_EMAIL', password='$SUPERUSER_PASSWORD')
    print('Superuser created.')
"
fi

exec "$@"
