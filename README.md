tl;dr:
------

Plain python:
-------------

Using Python 3.6+

```
pip install -r requirements.txt
python link.py DB_DSN=sqlite:///link.sdb
```

When run like that it'll print out `SECRET=<random string>` - this is the
randomly generated session encryption key. You can then add `SECRET=...`
after `DB_DSN=...` to make sure that cookies stay compatible between site
reloads.

Run unit tests with:
```
pytest
```

Or inside docker:
-----------------

```
docker build -t link .
docker run -t -p 0.0.0.0:8100:8000 link
```

And then the website should be visible at http://localhost:8100/

By default we use an sqlite database in `/db`, which will be wiped when the
container stops. To keep /db on a named volume so it will be saved between
runs, add `-v linkdb:/db` after `run`.

If you want to use an external database, add
`-e DB_DSN=postgres://user:password@hostname/database` after `run`.
