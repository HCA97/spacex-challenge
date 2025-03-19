
import datetime
import logging
from typing import List, Dict, Any, Optional, Union
import copy

from utils import fetch_data, parse_date

class SpaceXData:
    """
    Class to load and store SpaceX API data.
    """
    def __init__(self, launches: List[Dict[str, Any]], rockets: List[Dict[str, Any]], launchpads: List[Dict[str, Any]]):
        self.launches= launches
        self.rockets= rockets
        self.launchpads= launchpads

    def get_rocket_by_id(self, rocket_id: str) -> Dict[str, Any]:
        """
        Get rocket details by ID.
        """
        for rocket in self.rockets:
            if rocket.get("id") == rocket_id:
                return rocket
        return {}

    def get_launchpad_by_id(self, launchpad_id: str) -> Dict[str, Any]:
        """
        Get launchpad details by ID.
        """
        for launchpad in self.launchpads:
            if launchpad.get("id") == launchpad_id:
                return launchpad
        return {}
    
    def filter_launches(self, 
                       start_date: Optional[datetime.datetime] = None, 
                       end_date: Optional[datetime.datetime] = None, 
                       rocket_name: Optional[Union[str, List[str]]] = None, 
                       success: Optional[bool] = None, 
                       launch_site: Optional[Union[str, List[str]]] = None) -> List[Dict[str, Any]]:
        """
        Filter launches based on:
          - Date range (date must be in utc format)
          - Rocket name(s)
          - Launch success/failure
          - Launch site name(s)
        """

        if start_date and start_date.tzinfo is None:
            logging.warning("Assuming start_date is in UTC timezone")
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)

        if end_date and end_date.tzinfo is None:
            logging.warning("Assuming end_date is in UTC timezone")
            end_date = end_date.replace(tzinfo=datetime.timezone.utc)

        if start_date and end_date and start_date > end_date:
            logging.warning("Invalid date range, start_date is greater than end_date, swapping values")
            start_date, end_date = end_date, start_date

        if isinstance(rocket_name, str):
            rocket_name = [rocket_name]
        
        if rocket_name:
            rocket_name = [name.lower().strip() for name in rocket_name]

        if isinstance(launch_site, str):
            launch_site = [launch_site]

        if launch_site:
            launch_site = [name.lower().strip() for name in launch_site]


        filtered = []
        for launch in self.launches:

            # Parse date
            launch_date = parse_date(launch.get("date_utc", "")) 
            if not launch_date:
                logging.warning(f"Skiping, launch({launch.get('id')}) - Invalid date format.")
                continue
            
            # Filter by date range
            if start_date and launch_date < start_date:
                continue
            if end_date and launch_date > end_date:
                continue

            # Filter by success/failure
            if success is not None and launch.get("success", False) != success:
                continue
            
            # Filter by rocket name
            if rocket_name:
                rocket = self.get_rocket_by_id(launch.get("rocket")).get("name", "").strip().lower()
                if rocket not in rocket_name:
                    continue
            
            # Filter by launch site
            if launch_site:
                launchpad = self.get_launchpad_by_id(launch.get("launchpad")).get("name", "").strip().lower()
                if launchpad not in launch_site:
                    continue

            filtered.append(copy.deepcopy(launch))
        return filtered
    
    def success_rate_by_rocket(self, rocket_name: str) -> Optional[float]:
        """
        Calculate the success rate (in percentage) for a specific rocket.
        """
        filtered = self.filter_launches(rocket_name=rocket_name)
        total_launches = len(filtered)
        if total_launches == 0:
            return None
        successful_launches = sum([1 for launch in filtered if launch.get("success", False)])
        return successful_launches / total_launches * 100
    
    def launches_by_site(self, launch_site: str) -> Optional[int]:
        """
        Count total launches per launch site.
        """
        filtered = self.filter_launches(launch_site=launch_site)
        return len(filtered)
    
    def launch_frequency(self, period: str = "monthly") -> Dict[str, int]:
        """
        Calculate launch frequency grouped by month or year.
        """

        freq: Dict[str, int] = {}
        for launch in self.launches:
            # Parse date
            date_str: str = launch.get("date_utc", "")
            if not date_str:
                continue
            try:
                launch_date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError) as e:
                logging.warning(f"Skiping, launch({launch.get('id')}) - Invalid date format: {date_str} ({e})")
                continue

            if period == "monthly":
                key = launch_date.strftime("%m")
            elif period == "yearly":
                key = launch_date.strftime("%Y")
            else:
                continue
        
            freq[key] = freq.get(key, 0) + 1
        return freq

    def get_rockets(self, by_name: bool = False) -> List[str]:
        if by_name:
            return [rocket.get("name", "") for rocket in self.rockets]
        return [rocket.get("id", "") for rocket in self.rockets]
    
    def get_launch_sites(self, by_name: bool = False) -> List[str]:
        if by_name:
            return [launchpad.get("name", "") for launchpad in self.launchpads]
        return [launchpad.get("id", "") for launchpad in self.launchpads]

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SpaceX Launch Tracker")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD")
    parser.add_argument("--rocket", type=str, help="Rocket name to filter")
    parser.add_argument("--success", type=str, choices=["true", "false"], help="Filter by launch success (true/false)")
    parser.add_argument("--site", type=str, help="Launch site name to filter")
    args = parser.parse_args()

    # Load SpaceX data
    data, _ = fetch_data()
    spacex_data = SpaceXData(**data)

    # Get the full list of launches
    launches = spacex_data.launches

    # Parse optional filter criteria
    start_date = datetime.datetime.fromisoformat(args.start_date) if args.start_date else None
    end_date = datetime.datetime.fromisoformat(args.end_date) if args.end_date else None
    success_filter: Optional[bool] = None
    if args.success:
        success_filter = True if args.success.lower() == "true" else False

    filtered_launches = spacex_data.filter_launches(
        start_date=start_date,
        end_date=end_date,
        rocket_name=args.rocket,
        success=success_filter,
        launch_site=args.site
    )
    print(f"Total Launches: {len(launches)}")
    print(f"Total Launches after filtering: {len(filtered_launches)}\n")

    # Statistics: Success rate per rocket
    print("\nSuccess Rate by Rocket:")
    for rocket in spacex_data.get_rockets(by_name=True):
        rate = spacex_data.success_rate_by_rocket(rocket)
        if rate is not None:
            print(f"  {rocket}: {rate:.2f}%")

    # Count launches by site
    print("\nLaunches by Site:")
    for launch_site in spacex_data.get_launch_sites(by_name=True):
        count = spacex_data.launches_by_site(launch_site)
        if count is not None:
            print(f"  {launch_site}: {count}")

    # Launch frequency
    print("\nMonthly Launch Frequency:")
    monthly = spacex_data.launch_frequency("monthly")
    for month, count in sorted(monthly.items()):
        print(f"  {month}: {count}")

    print("\nYearly Launch Frequency:")
    yearly = spacex_data.launch_frequency("yearly")
    for year, count in sorted(yearly.items()):
        print(f"  {year}: {count}")

if __name__ == "__main__":
    main()
