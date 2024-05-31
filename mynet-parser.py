#!/usr/bin/env python3

import re
import phonenumbers
from phonenumbers import NumberParseException
import csv
import sys

def clean_phone_number(phone_number):
    """
    Cleans the phone number by removing non-numeric characters from the start and end,
    and keeping only digits and the leading + if present.
    """
    cleaned_number = re.sub(r'^\D+|\D+$', '', phone_number)  # Remove non-numeric characters from start and end
    cleaned_number = re.sub(r'(?<!^)\D', '', cleaned_number)  # Remove non-numeric characters except for leading +
    return cleaned_number

def convert_to_international(phone_number, region="DE"):
    try:
        cleaned_number = clean_phone_number(phone_number)
        # Check if the number starts with + or 00, if not, assume it's a local number
        if not (cleaned_number.startswith('+') or cleaned_number.startswith('00')):
            cleaned_number = '0' + cleaned_number.lstrip('0')  # Ensure it starts with a single leading 0
        parsed_number = phonenumbers.parse(cleaned_number, region)
        if phonenumbers.is_possible_number(parsed_number) and phonenumbers.is_valid_number(parsed_number):
            international_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            numeric_format = international_number.lstrip('+')  # Remove the leading '+' to get the numeric format
            return numeric_format
        else:
            return None
    except NumberParseException:
        return None

def clean_name(name):
    """
    Cleans the name by removing invalid characters and trimming spaces.
    """
    cleaned_name = re.sub(r'[^\w\s]', '', name).strip()  # Remove invalid characters and trim spaces
    return cleaned_name

def is_valid_name(name):
    """
    Checks if the name is valid (contains at least a first name and a last name).
    """
    parts = name.split()
    return len(parts) >= 2

def process_csv(input_file, output_file):
    invalid_numbers = []
    invalid_names = []
    with open(input_file, 'r', newline='', encoding='utf-8-sig') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile, delimiter=';')
        fieldnames = reader.fieldnames
        expected_fields = ['Adı Soyadı', 'Telefon', 'Email', 'p', 'Not', 'n', 'Lead Olusturulma Tarihi', 'Lead Olusruran Adı', 'ls', 'd', 't', 'las', 'hf', 'r']

        if fieldnames != expected_fields:
            print("Error: Input file must contain the correct headers.")
            print(f"Expected headers: {expected_fields}")
            print(f"Found headers: {fieldnames}")
            return

        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for row in reader:
            name = row['Adı Soyadı']
            phone_number = row['Telefon']

            cleaned_name = clean_name(name)
            if not is_valid_name(cleaned_name):
                invalid_names.append(name)
                continue

            converted_number = convert_to_international(phone_number)
            if converted_number:
                row['Adı Soyadı'] = cleaned_name
                row['Telefon'] = converted_number
                writer.writerow(row)
            else:
                invalid_numbers.append(phone_number)

    if invalid_numbers:
        print("Invalid numbers:")
        for number in invalid_numbers:
            print(number)

    if invalid_names:
        print("Invalid names:")
        for name in invalid_names:
            print(name)

def main(input_file, output_file):
    process_csv(input_file, output_file)
    print(f"Converted phone numbers have been saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)
