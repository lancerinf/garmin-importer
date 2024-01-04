from context import garmin_utils

import unittest
import json


class TestCleanActivityFunction(unittest.TestCase):

    def test__clean_activity_succeeds_with_outdoor_running_activity(self):
        with open('../resources/garmin_activity_outdoor_running.json') as json_file:
            outdoor_running_activity = json.load(json_file)
            clean_activity = garmin_utils._clean_activity(outdoor_running_activity)
            self.assertTrue(len(clean_activity))

    def test__clean_activity_succeeds_with_indoor_cycling_activity(self):
        with open('../resources/garmin_activity_indoor_cycling.json') as json_file:
            indoor_cycling_activity = json.load(json_file)
            clean_activity = garmin_utils._clean_activity(indoor_cycling_activity)
            self.assertTrue(len(clean_activity))

    def test__clean_activity_succeeds_with_indoor_swimming_activity(self):
        with open('../resources/garmin_activity_indoor_swimming.json') as json_file:
            indoor_swimming_activity = json.load(json_file)
            clean_activity = garmin_utils._clean_activity(indoor_swimming_activity)
            self.assertTrue(clean_activity)


if __name__ == '__main__':
    unittest.main()
