FROM python:3.12-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \ 
    PYTHONDONTWRITEBYTECODE=1 

RUN pip install poetry && poetry config virtualenvs.in-project true

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY lib/_binary_packer.pyx ./lib/
RUN /app/.venv/bin/cythonize -i lib/_binary_packer.pyx

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=builder /app .
COPY . .

CMD ["/app/.venv/bin/fastapi", "run"]
