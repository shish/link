FROM python:3.9-slim-buster
RUN apt update && apt install -y curl
HEALTHCHECK --interval=5m --timeout=3s CMD curl --fail http://127.0.0.1:8000/ || exit 1
ENV DB_DSN=sqlite:////db/link.sdb
ENV SECRET=
VOLUME /db
EXPOSE 8000

ENV PYTHONUNBUFFERED 1
RUN /usr/local/bin/pip install --upgrade pip setuptools wheel
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/pip install -r /tmp/requirements.txt
RUN /usr/local/bin/pip install psycopg2-binary

COPY . /app
WORKDIR /app
RUN /usr/local/bin/pytest
CMD ["/usr/local/bin/python", "link.py"]

