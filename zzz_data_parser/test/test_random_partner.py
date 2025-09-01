import sys
import os
import random

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from zzz_data_parser.services.partner_service import PartnerService
from zzz_data_parser.formatters.partner_formatter import PartnerFormatter

def main():
    """Main function to demonstrate the partner parser by randomly selecting a partner."""
    print("Initializing PartnerService...")
    service = PartnerService()

    print("Getting list of partner IDs...")
    partner_ids = service.list_partner_ids()

    if not partner_ids:
        print("No partners found!")
        return

    print(f"Found {len(partner_ids)} partners.")

    # Randomly select a partner ID
    selected_partner_id = random.choice(partner_ids)
    print(f"\nSelected partner ID: {selected_partner_id}")

    # Get the partner data
    partner = service.get_partner_by_id(selected_partner_id)

    if not partner:
        print(f"Failed to load partner with ID {selected_partner_id}")
        return

    # Format and print the partner data
    print("\n--- Partner Data (Markdown) ---")
    markdown_output = PartnerFormatter.to_markdown(partner)
    print(markdown_output)

    print("\n--- Partner Data (Dictionary) ---")
    dict_output = PartnerFormatter.to_dict(partner)
    for key, value in dict_output.items():
        # For list values, print each item on a new line
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()