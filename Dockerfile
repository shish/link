FROM python:3.6-slim-stretch
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
CMD ["/usr/local/bin/python", "link.py"]

