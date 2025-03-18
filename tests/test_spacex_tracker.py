import unittest
import datetime
from spacex_tracker import SpaceXData

class TestSpaceXTracker(unittest.TestCase):
    def setUp(self):
        # Dummy SpaceX data for testing
        self.spacex_data = SpaceXData([], [], [])
        self.spacex_data.rockets = [
            {"id": "rocket1", "name": "Falcon 1"},
            {"id": "rocket2", "name": "Falcon 9"}
        ]
        self.spacex_data.launchpads = [
            {"id": "pad1", "name": "Launch Site A"},
            {"id": "pad2", "name": "Launch Site B"}
        ]
        self.spacex_data.launches = [
            {
                "date_utc": "2020-01-01T00:00:00.000Z",
                "rocket": "rocket1",
                "launchpad": "pad1",
                "success": True
            },
            {
                "date_utc": "2020-02-01T00:00:00.000Z",
                "rocket": "rocket2",
                "launchpad": "pad2",
                "success": False
            },
            {
                "date_utc": "2020-03-01T00:00:00.000Z",
                "rocket": "rocket1",
                "launchpad": "pad1",
                "success": True
            }
        ]

    def test_filter_launches_date(self):
        # Filter launches starting from February 2020
        start_date = datetime.datetime(2020, 2, 1)
        filtered = self.spacex_data.filter_launches(start_date=start_date)
        self.assertEqual(len(filtered), 2)

        # Test start date > end date
        end_date = datetime.datetime(2020, 1, 1)
        filtered = self.spacex_data.filter_launches(start_date=start_date, end_date=end_date)
        self.assertEqual(len(filtered), 2)

        # Test start date 
        start_date = datetime.datetime(2020, 5, 1)
        filtered = self.spacex_data.filter_launches(start_date=start_date)
        self.assertEqual(len(filtered), 0)

        # Test end date
        end_date = datetime.datetime(2019, 12, 31)
        filtered = self.spacex_data.filter_launches(end_date=end_date)
        self.assertEqual(len(filtered), 0)

    def test_filter_by_rocket_name(self):
        # Only include launches with rocket name "Falcon 1"
        filtered = self.spacex_data.filter_launches(rocket_name="Falcon 1")
        self.assertEqual(len(filtered), 2)

        # No rocket with name "Falcon Heavy"
        filtered = self.spacex_data.filter_launches(rocket_name="Falcon Heavy")
        self.assertEqual(len(filtered), 0)

        # Add padding
        filtered = self.spacex_data.filter_launches(rocket_name=" Falcon 1 ")
        self.assertEqual(len(filtered), 2)

        # Test multiple rocket names
        filtered = self.spacex_data.filter_launches(rocket_name=["Falcon 1", "Falcon 9"])
        self.assertEqual(len(filtered), 3)

    def test_filter_by_success(self):
        # Only include successful launches
        filtered = self.spacex_data.filter_launches(success=True)
        self.assertEqual(len(filtered), 2)

        # Only include failed launches
        filtered = self.spacex_data.filter_launches(success=False)
        self.assertEqual(len(filtered), 1)

    def test_calc_success_rate(self):
        rates = self.spacex_data.success_rate_by_rocket("Falcon 1")
        self.assertAlmostEqual(rates, 100.0)

        rates = self.spacex_data.success_rate_by_rocket("Falcon 9")
        self.assertAlmostEqual(rates, 0.0)

        rates = self.spacex_data.success_rate_by_rocket("Falcon Heavy")
        self.assertIsNone(rates)

    def test_count_launches_by_site(self):
        counts = self.spacex_data.launches_by_site("Launch Site A")
        self.assertEqual(counts, 2)

        counts = self.spacex_data.launches_by_site("Launch Site B")
        self.assertEqual(counts, 1)

        counts = self.spacex_data.launches_by_site("Launch Site C")
        self.assertEqual(counts, 0)

        counts = self.spacex_data.launches_by_site(["Launch Site A", "Launch Site B"])
        self.assertEqual(counts, 3)

    def test_launch_frequency(self):
        freq = self.spacex_data.launch_frequency()
        self.assertEqual(freq, {"2020-01": 1, "2020-02": 1, "2020-03": 1})

        freq = self.spacex_data.launch_frequency(period="yearly")
        self.assertEqual(freq, {"2020": 3})

if __name__ == "__main__":
    unittest.main()
