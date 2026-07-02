# Build frontend in an isolated environment
FROM node:26 AS build
COPY package.json package-lock.json /app/
WORKDIR /app
RUN npm install
COPY . /app
RUN npm run build


FROM python:3.14-slim
VOLUME /data
EXPOSE 8000

ENV PYTHONUNBUFFERED=1 UV_NO_DEV=1
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

COPY . /app
WORKDIR /app
RUN uv sync --locked
COPY --from=build /app/dist /app/frontend/dist
RUN ln -s /data ./data
CMD ["uv", "run", "gunicorn", "-w", "4", "backend.app:create_app()", "-b", "0.0.0.0:8000"]
