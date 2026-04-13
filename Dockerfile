FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./pyproject.toml ./README.md ./
COPY ./app ./app
COPY ./static ./static

RUN pip install .

CMD ["python", "-m", "app.main"]
