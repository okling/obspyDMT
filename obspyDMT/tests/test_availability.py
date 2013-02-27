import unittest

from obspyDMT.availability import filter_channel_priority


class AvailibilityTestCase(unittest.TestCase):
    """
    Tests suite for functions regarding the channel availability.
    """
    def test_priority_filtering(self):
        """
        Tests the filter_channel_prority() function.
        """
        channels = {
            "A.B.C.EHE": {"some": "content"},
            "A.B.C.EHN": {"some": "content"},
            "A.B.C.EHX": {"some": "content"},
            "A.B.C.HHE": {"some": "content"},
            "A.B.C.HHN": {"some": "content"},
            "A.B.C.LHE": {"some": "content"},
            "1.2.3.4": {"some": "content"},
            "1.B.C.LHE": {"some": "content"},
            "1.B.C.LHN": {"some": "content"},
            "1.B.C.LHZ": {"some": "content"},
            "1.B.C.LHX": {"some": "content"},
            "A.B.D.EHE": {"some": "content"}}

        channels = filter_channel_priority(channels, priorities=["HH[Z,N,E]",
            "BH[Z,N,E]", "MH[Z,N,E]", "EH[Z,N,E]", "LH[Z,N,E]"])

        self.assertEqual(channels, {
            "A.B.C.HHE": {"some": "content"},
            "A.B.C.HHN": {"some": "content"},
            "A.B.D.EHE": {"some": "content"},
            "1.B.C.LHE": {"some": "content"},
            "1.B.C.LHN": {"some": "content"},
            "1.B.C.LHZ": {"some": "content"}})


if __name__ == '__main__':
    unittest.main()
