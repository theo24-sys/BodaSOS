FROM python:3.12-slim

# Injects the missing C-libraries directly into the isolated container space
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Force Render to generate the production migration files during image compilation
RUN python manage.py makemigrations core accounts saccos riders patients dispatch notifications reports --noinput
RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "gunicorn salamanoda.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]
