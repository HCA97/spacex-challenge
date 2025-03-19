from flask import Flask, render_template, request
from threading import Thread, Lock
import json
import math
import logging

from spacex_tracker import SpaceXData
from utils import send_notifications, fetch_data, parse_date
from config import PAGE_SIZE

app = Flask(__name__)

_SUBSCRIBERS = set()
_LOCK = Lock()

@app.route('/')
def launches():

    # Data
    data, notify_subscribers = fetch_data()
    # Notify subscribers as background task, thanks to caching notifies once.
    if notify_subscribers and _SUBSCRIBERS:
        Thread(target=send_notifications, args=(_SUBSCRIBERS,), daemon=True).start()
        
    spacex_data = SpaceXData(**data)

    rockets = spacex_data.get_rockets(by_name=True)
    launchpads = spacex_data.get_launch_sites(by_name=True)
    
    # Request parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    rocket_filter = request.args.getlist('rocket')
    launchpad_filter = request.args.getlist('launchpad')
    success_filter = request.args.get('success')
    page = request.args.get('page', 1, type=int)

    # Filter launches
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)
    success_filter = success_filter.lower() == 'true' if success_filter else None
    
    filtered_launches = spacex_data.filter_launches(
        start_date=start_date,
        end_date=end_date,
        rocket_name=rocket_filter,
        success=success_filter,
        launch_site=launchpad_filter
    )
    
    for launch in filtered_launches:
        launch["rocket"] = spacex_data.get_rocket_by_id(launch["rocket"]).get("name", "Unknown")
        launch["launchpad"] = spacex_data.get_launchpad_by_id(launch["launchpad"]).get("name", "Unknown")
    
    # Pagination logic
    total_launches = len(filtered_launches)
    total_pages = math.ceil(total_launches / PAGE_SIZE)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    paginated_launches = filtered_launches[start:end]

    logging.info(len(paginated_launches))
    
    return render_template("launches.html", 
                           launches=paginated_launches, 
                           rockets=rockets, 
                           launchpads=launchpads,
                           page=page,
                           total_pages=total_pages)

@app.route('/stats')
def stats():
    return render_template("stats.html")

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    url = request.get_json().get("url")
    if not url:
        return "No url", 400
    
    with _LOCK:
        _SUBSCRIBERS.add(url)
   
    return "Subscribed successfully!", 200

@app.route("/api/launches", methods=["GET"])
def export_launches():
    data, notify_subscribers = fetch_data()
    if notify_subscribers and _SUBSCRIBERS:
        Thread(target=send_notifications, args=(_SUBSCRIBERS,), daemon=True).start()

    spacex_data = SpaceXData(**data)

    # Request parameters for filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    rocket_filter = request.args.getlist('rocket')
    launchpad_filter = request.args.getlist('launchpad')
    success_filter = request.args.get('success')

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)
    success_filter = success_filter.lower() == 'true' if success_filter else None
    
    filtered_launches = spacex_data.filter_launches(
        start_date=start_date,
        end_date=end_date,
        rocket_name=rocket_filter,
        success=success_filter,
        launch_site=launchpad_filter
    )
    
    for launch in filtered_launches:
        launch["rocket"] = spacex_data.get_rocket_by_id(launch["rocket"]).get("name", "Unknown")
        launch["launchpad"] = spacex_data.get_launchpad_by_id(launch["launchpad"]).get("name", "Unknown")
        launch.pop("id")

    return filtered_launches, 200

@app.route("/api/stats")
def api_stats():
    # Fetch data and initialize SpaceXData
    data, notify_subscribers = fetch_data()
    if notify_subscribers and _SUBSCRIBERS:
        Thread(target=send_notifications, args=(_SUBSCRIBERS,), daemon=True).start()
    spacex_data = SpaceXData(**data)

    # Get success rates by rocket
    success_rates = {
        rocket: spacex_data.success_rate_by_rocket(rocket)
        for rocket in spacex_data.get_rockets(by_name=True)
    }
    # sort by success rate
    success_rates = dict(sorted(success_rates.items(), key=lambda x: -1 if x[1] is None else x[1], reverse=True))

    # Get launch frequencies
    launch_freq_monthly = spacex_data.launch_frequency("monthly")
    launch_freq_yearly = spacex_data.launch_frequency("yearly")

    # conver monts and years to number (some reason js doesnt use sorted keys)
    launch_freq_monthly = {int(k): v for k, v in launch_freq_monthly.items()}
    launch_freq_yearly = {int(k): v for k, v in launch_freq_yearly.items()}

    # sort by month/year
    launch_freq_monthly = dict(sorted(launch_freq_monthly.items(), key=lambda x: x[0]))
    launch_freq_yearly = dict(sorted(launch_freq_yearly.items(), key=lambda x: x[0]))

    return {
        "success_rates": success_rates,
        "launch_freq_monthly": launch_freq_monthly,
        "launch_freq_yearly": launch_freq_yearly
    }, 200
    



if __name__ == '__main__':
    app.run(debug=True)
