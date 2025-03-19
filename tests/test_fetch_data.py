import unittest
from unittest.mock import patch, MagicMock
import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import config as c
import utils as u

class TestFetchData(unittest.TestCase):

    @patch("utils._fetch_launches")
    @patch("utils._fetch_rockets")
    @patch("utils._fetch_launchpads")
    def test_fetch_data_cache_valid(self, mock_launchpads, mock_rockets, mock_launches):        
        u._DATA["launches"] = [{"id": "1"}, {"id": "2"}]
        u._TIMESTAMP = dt.datetime.now() 

        data, notify = u.fetch_data()

        self.assertEqual(data, u._DATA) 
        self.assertFalse(notify) 

        mock_launches.assert_not_called()  
        mock_launchpads.assert_not_called()
        mock_rockets.assert_not_called()

    @patch("utils._fetch_launches", return_value=[{"id": "1"}, {"id": "2"}, {"id": "3"}])
    @patch("utils._fetch_rockets", return_value=[{"id": "R1"}])
    @patch("utils._fetch_launchpads", return_value=[{"id": "LP1"}])
    def test_fetch_data_cache_expired(self, mock_launchpads, mock_rockets, mock_launches): 
        u._DATA = {}       
        u._TIMESTAMP = dt.datetime.now() - dt.timedelta(seconds=c.CACHE_EXPIRY + 1)

        data, notify = u.fetch_data()

        self.assertEqual(data["launches"], [{"id": "1"}, {"id": "2"}, {"id": "3"}]) 
        self.assertEqual(data["rockets"], [{"id": "R1"}])
        self.assertEqual(data["launchpads"], [{"id": "LP1"}])
        self.assertTrue(notify)  

        mock_launches.assert_called_once()  
        mock_launchpads.assert_called_once()
        mock_rockets.assert_called_once()

    @patch("utils._fetch_launches", return_value=[{"id": "1"}, {"id": "2"}])
    @patch("utils._fetch_rockets", return_value=[{"id": "R1"}])
    @patch("utils._fetch_launchpads", return_value=[{"id": "LP1"}])
    def test_fetch_data_no_change_in_launches(self, mock_launchpads, mock_rockets, mock_launches):
        u._DATA["launches"] = [{"id": "1"}, {"id": "2"}]
        u._TIMESTAMP = dt.datetime.now() - dt.timedelta(seconds=c.CACHE_EXPIRY + 1)

        data, notify = u.fetch_data()

        self.assertEqual(len(data["launches"]), 2)
        self.assertFalse(notify)

        mock_launches.assert_not_called()  
        mock_launchpads.assert_not_called()
        mock_rockets.assert_not_called()

    @patch("utils._fetch_launches", return_value=[{"id": "1"}, {"id": "2"}])
    @patch("utils._fetch_rockets", return_value=[{"id": "R1"}])
    @patch("utils._fetch_launchpads", return_value=[{"id": "LP1"}])
    def test_concurrent_fetch_data(self, mock_launchpads, mock_rockets, mock_launches):
        u._DATA = {}
        u._TIMESTAMP = dt.datetime(1453, 5, 29)  

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(u.fetch_data) for _ in range(2)]
            results = [future.result() for future in futures]


        self.assertEqual(results[0][0], results[1][0])
        self.assertTrue(results[0][1])
        self.assertFalse(results[1][1])

        self.assertEqual(mock_launches.call_count, 1)
        self.assertEqual(mock_rockets.call_count, 1)
        self.assertEqual(mock_launchpads.call_count, 1)

    @patch("utils.requests.get")
    def test_fetch_data_first_try(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": "1", "data": "success"}]
        mock_get.return_value = mock_response

        url = "http://example.com/api"
        result = u._fetch_data(url)

        self.assertEqual(result, [{"id": "1", "data": "success"}])
        self.assertEqual(mock_get.call_count, 1)

    @patch("utils.time.sleep", return_value=None)  
    @patch("utils.requests.get")
    def test_fetch_data_second_try(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": "2", "data": "success on second try"}]
        mock_get.side_effect = [Exception("Network error"), mock_response]

        url = "http://example.com/api"
        result = u._fetch_data(url)

        self.assertEqual(result, [{"id": "2", "data": "success on second try"}])
        self.assertEqual(mock_get.call_count, 2)

    @patch("utils.time.sleep", return_value=None) 
    @patch("utils.requests.get")
    def test_fetch_data_all_fail(self, mock_get, mock_sleep):
        mock_get.side_effect = Exception("Network error")

        url = "http://example.com/api"
        result = u._fetch_data(url)

        self.assertEqual(result, [])
        self.assertEqual(mock_get.call_count, 3)
    

if __name__ == "__main__":
    unittest.main()
