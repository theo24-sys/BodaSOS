FROM python:3.12-slim

# Injects the missing C-libraries directly into the isolated container space
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Set explicit compiler environments for GeoDjango stability
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build-time placeholders so settings load during image build.
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV DATABASE_URL=postgresql://placeholder:placeholder@localhost:5432/placeholder
ENV SECRET_KEY=build-time-placeholder-secret-key-not-real
ENV REDIS_URL=redis://localhost:6379
ENV ALLOWED_HOSTS=localhost,127.0.0.1

# Force Render to generate the production migration files during image compilation
RUN python manage.py makemigrations core accounts saccos riders patients dispatch notifications reports --noinput
RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "daphne -b 0.0.0.0 -p ${PORT:-10000} salamanoda.asgi:application"]
