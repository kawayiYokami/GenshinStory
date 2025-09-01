import sys
import os
import unittest

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from ..services.partner_service import PartnerService
from ..formatters.partner_formatter import PartnerFormatter

class TestPartnerPipeline(unittest.TestCase):
    """
    Integration test for the Partner data pipeline:
    Parser -> Service -> Formatter
    """

    def setUp(self) -> None:
        """
        Set up test fixtures before each test method.
        """
        self.service = PartnerService()

    def test_get_partner_and_format(self) -> None:
        """
        Test retrieving a specific partner (e.g., Anbi) and formatting it.
        This verifies the entire pipeline from data loading to output.
        """
        # Use a known partner ID for testing
        test_partner_id = "1011" # Anbi

        # 1. Service Layer: Get the partner object
        partner = self.service.get_partner_by_id(test_partner_id)

        # Assert that the partner was found
        self.assertIsNotNone(partner, f"Partner with ID {test_partner_id} should exist.")

        # 2. Formatter Layer: Format the partner object
        if partner:
            # Test Markdown formatting
            markdown_output = PartnerFormatter.to_markdown(partner)
            self.assertIn(f"# 角色: {partner.name}", markdown_output)
            self.assertIn(partner.outlook_desc, markdown_output)
            for desc in partner.profile_descs:
                self.assertIn(desc, markdown_output)
            if partner.impression_f:
                self.assertIn(partner.impression_f, markdown_output)
            if partner.impression_m:
                self.assertIn(partner.impression_m, markdown_output)

            # Test Dictionary formatting
            dict_output = PartnerFormatter.to_dict(partner)
            self.assertEqual(dict_output['id'], partner.id)
            self.assertEqual(dict_output['name'], partner.name)
            self.assertEqual(dict_output['outlook_desc'], partner.outlook_desc)
            self.assertEqual(dict_output['profile_descs'], partner.profile_descs)
            self.assertEqual(dict_output['impression_f'], partner.impression_f)
            self.assertEqual(dict_output['impression_m'], partner.impression_m)

    def test_list_partner_ids(self) -> None:
        """
        Test that the service can list all partner IDs.
        """
        ids = self.service.list_partner_ids()
        # We expect at least one partner ID to be present
        self.assertGreater(len(ids), 0, "There should be at least one partner ID.")
        # Check if our test ID is in the list
        self.assertIn("1011", ids, "Test partner ID 1011 should be in the list.")

if __name__ == '__main__':
    unittest.main()