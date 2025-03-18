from flask import Flask, render_template, request
import json
from utils import fetch_data, parse_date
import math
import logging

from spacex_tracker import SpaceXData
from config import PAGE_SIZE

app = Flask(__name__)


@app.route('/')
def launches():

    # Data
    data, _ = fetch_data()
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
    # Fetch data and initialize SpaceXData
    data, _ = fetch_data()
    spacex_data = SpaceXData(**data)

    # Get success rates by rocket
    success_rates = {
        rocket: spacex_data.success_rate_by_rocket(rocket) 
        for rocket in spacex_data.get_rockets(by_name=True)
    }

    # Get launch frequencies
    launch_freq_monthly = spacex_data.launch_frequency("monthly")
    launch_freq_yearly = spacex_data.launch_frequency("yearly")

    return render_template(
        "stats.html",
        success_rates=success_rates,
        launch_freq_monthly=launch_freq_monthly,
        launch_freq_yearly=launch_freq_yearly
    )

if __name__ == '__main__':
    app.run(debug=True)
