# Earnings Task Tracker

A local Streamlit dashboard for logging tasks, configuring rates, and tracking
earnings and bonus milestones. Data is stored in SQLite.

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
it to the same location before starting the app again. 

## Exchange rates

Default preferences live in `default_settings.py`. Startup adds missing settings
to existing databases without overwriting saved preferences.

Set **Conversion fee (%)** in the sidebar (default: 4.5%, range: 0–100%) and
click **Save settings** to persist it. The fee reduces converted MXN earnings;
USD earnings remain unchanged.

The app starts with a manual USD/MXN rate of 18.50, which you can change in the
sidebar. Live FX is optional: enabling it uses public HTTP APIs and requires
internet, but no API credentials. Tasks, rates, and settings always remain local.

## Date filter and task selection

Enable **Filter by date** above the dashboard and choose inclusive start/end
dates. The task log, hours, task count, earnings, earned bonuses, and progress
all use the selected period. Disable the filter to show all dates. Extra earnings
remain a global adjustment because they have no associated date.

The task-name selector updates Rate Type immediately: manual tasks show it;
tiered tasks calculate their rates automatically. After submission, the selector
returns to the first task type.

Deleting checked rows applies only to selected visible tasks. **Clear all tasks**
still clears the entire task history, including entries outside the date filter.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use temporary databases and do not modify your earnings data.
