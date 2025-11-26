FROM python:3.11-slim

WORKDIR /backend

COPY ./requirements.txt /backend/requirements.txt

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   build-essential \
	   gcc \
	   libpq-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

COPY ./src /backend/src
COPY ./alembic /backend/alembic
COPY ./alembic.ini /backend/alembic.ini

# Copy entrypoint and make it executable
COPY ./entrypoint.sh /backend/entrypoint.sh
RUN chmod +x /backend/entrypoint.sh

ENTRYPOINT ["/backend/entrypoint.sh"]
