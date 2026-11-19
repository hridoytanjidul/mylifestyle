# My Life Hub

The website runs as a local Flask app with a SQLite database. Its HTML/CSS/JavaScript
interface stays in `personal-hub.html`; Flask serves it and persists the app state.

## Run locally

```sh
python3 -m pip install -r requirements.txt
python3 app.py
```

Open <http://127.0.0.1:5000>. Keep the terminal running while you use the website.
The database is stored in `personal-hub.sqlite3` beside `app.py`. The server binds to
localhost only; it is intended for personal use on this device.

If you previously opened `personal-hub.html` directly, that browser storage belongs
to the `file://` origin and cannot be read by the Flask site. Export a JSON backup
from the old page, open the Flask site, then use Settings → Import JSON once to move
that data into SQLite.

## Test

```sh
python3 -m unittest discover -s tests
```
