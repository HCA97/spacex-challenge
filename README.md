# spacex-challenge

A Flask-based web app that tracks and analyzes SpaceX launches using the [SpaceX API v4](https://api.spacexdata.com/v4). It offers filtering, statistics, notifications, data export, and CLI support.

## Features

- **Launch Tracking:** View and filter launches by date, rocket, success status, and launch site.
- **Notifications:** Webhook support for new launches.
- **Data Export:** Export launch data in JSON format.
- **Command Line Interface (CLI):**
  - Filter launches via CLI arguments.
  - Display launch statistics.
  - Track launch frequency by month and year.

## Setup

### Requirements

- Python 3.10+
- pip
- Docker (optional)

### Installation

```sh
git clone https://github.com/your-repo/spacex-launch-tracker.git
cd spacex-launch-tracker
pip install -r requirements.txt
python app.py
```

Access at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### Docker Deployment

```sh
docker build -t spacex-launch-tracker .
docker run -p 8000:8000 spacex-launch-tracker
```

Access at: [http://localhost:8000/](http://localhost:8000/)

## API Endpoints

- **`GET /`** - List launches (supports filtering)
- **`POST /subscribe`** - Subscribe to webhook notifications
- **`GET /export`** - Export launch data

## CLI Usage

The CLI allows users to filter launches and generate statistics from the terminal.

### Example Commands:

```sh
python spacex_tracker.py --start-date 2023-01-01 --end-date 2023-12-31 --rocket "Falcon 9"
```

```sh
python spacex_tracker.py --site "Cape Canaveral"
```

### Available Arguments:

- `--start-date YYYY-MM-DD` - Filter by start date
- `--end-date YYYY-MM-DD` - Filter by end date
- `--rocket "Rocket Name"` - Filter by rocket name
- `--success true/false` - Filter by success status
- `--site "Launch Site"` - Filter by launch site

## Development & Debugging

- Debug using the VSCode **Python Debugger: Flask** configuration.
- Run tests: `python -m unittest discover -s tests`

## License

MIT License.

