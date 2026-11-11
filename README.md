# Earnings Task Tracker

A local Streamlit dashboard for logging tasks, configuring rates, and tracking
earnings and bonus milestones. Data is stored in SQLite; no Google account,
credentials, database server, or API configuration is required.

## Run locally

With Python 3.11 or newer installed, run from the project folder:

```sh
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py
```

Open the local URL printed by Streamlit. Add task types and rates in the sidebar,
save settings, and start logging tasks. Dependency installation requires internet;
the dashboard runs offline by default afterward.

## Local database

On startup, `database.py` automatically creates `data/earnings.sqlite3` next to
the application, including missing tables and default settings. Repeated startup
preserves existing data. SQLite is included with Python.

- `tasks`: individually identified task entries, dates, durations, and rate types.
- `task_rates`: full/discounted rates, pricing modes, and tier thresholds.
- `settings`: JSON values for targets, bonus milestones, extra earnings, and FX preferences.

`storage.py` implements persistence without depending on Streamlit. Inserts and
deletions target individual task records; removing a rate does not delete past
tasks. Earnings continue to be calculated using the currently configured rates.

You can optionally create the schema without launching the dashboard:

```sh
python database.py
```

Set `EARNINGS_DB_PATH` to use a different database file (prefer an absolute path).
For example, in PowerShell:

```powershell
$env:EARNINGS_DB_PATH = 'C:\MyData\earnings.sqlite3'
python -m streamlit run dashboard.py
```

The default location does not depend on the working directory. Each clone has its
own data unless configured to use the same file. Database files are ignored by
Git. To back up or transfer data, stop the app and copy the database file; restore
it to the same location before starting the app again. Use a local disk for an
active database; do not share an active SQLite file over a network or sync service.

Existing Google Sheets data is **not automatically imported**. A fresh database
starts with an empty task log and no rates; the original spreadsheet is untouched.
Old Streamlit Google secrets are no longer used.

## Exchange rates

The app starts with a manual USD/MXN rate of 18.50, which you can change in the
sidebar. Live FX is optional: enabling it uses public HTTP APIs and requires
internet, but no API credentials. Tasks, rates, and settings always remain local.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use temporary databases and do not modify your earnings data.
