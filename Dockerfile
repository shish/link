# Build frontend in an isolated environment
FROM node:26 AS build
COPY package.json package-lock.json /app/
WORKDIR /app
RUN npm install
COPY . /app
RUN npm run build


FROM astral/uv:0.13.6-alpine
VOLUME /data
EXPOSE 8000
COPY . /app
WORKDIR /app
RUN uv sync --locked --no-dev
COPY --from=build /app/dist /app/frontend/dist
RUN ln -s /data ./data
CMD ["uv", "run", "--no-sync", "gunicorn", "-w", "4", "backend.app:create_app()", "-b", "0.0.0.0:8000", "--access-logfile", "-"]
