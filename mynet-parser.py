#!/usr/bin/env python3

import re
import phonenumbers
from phonenumbers import NumberParseException
import csv
import argparse
import spacy
import string

def load_blacklist(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def is_professional_title(token):
    return token.ent_type_ == 'ORG' or token.ent_type_ == 'PERSON'

def is_valid_name_spacy(name, blacklist, valid_chars, nlp):
    # Check for invalid characters
    if any(char not in valid_chars for char in name):
        return False

    # Check for blacklist words
    name_lower = name.lower()
    for keyword in blacklist:
        if keyword.lower() in name_lower:
            return False

    # Check for only one part (either name or surname), unless it contains "u."
    parts = name.split()
    if len(parts) == 1 and "u." not in name_lower:
        return False

    # Check for names with single letter abbreviation, unless it contains "u."
    if any(len(part) == 1 for part in parts) and "u." not in name_lower:
        return False

    # Check for professional titles using spaCy
    doc = nlp(name)
    for token in doc:
        if is_professional_title(token):
            return True

    return True

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
    Cleans the name by removing invalid characters, trimming spaces,
    and ensuring proper capitalization. It allows only valid Latin characters.
    """
    # Define a regex pattern for valid Latin characters, spaces, and question marks
    pattern = r'[^a-zA-ZçÇğĞıİöÖşŞüÜéÉèÈêÊáÁàÀâÂíÍìÌîÎóÓòÒôÔúÚùÙûÛÿŸýÝžŽçÇñÑß\'\s?-]'
    cleaned_name = re.sub(pattern, '', name).strip()  # Remove invalid characters and trim spaces
    capitalized_name = ' '.join(word.capitalize() for word in cleaned_name.split())
    return capitalized_name

def replace_non_latin_characters(name):
    """
    Replaces non-Latin characters in the name with '?'.
    """
    pattern = r'[^a-zA-ZçÇğĞıİöÖşŞüÜéÉèÈêÊáÁàÀâÂíÍìÌîÎóÓòÒôÔúÚùÙûÛÿŸýÝžŽçÇñÑß\'\s-]'
    replaced_name = re.sub(pattern, '?', name).strip()
    return replaced_name

def is_valid_name(name):
    """
    Checks if the name is valid (contains at least a first name and a last name).
    """
    parts = name.split()
    return len(parts) >= 2

def is_latin_name(name):
    """
    Checks if the name contains only Latin characters.
    """
    pattern = r'^[a-zA-ZçÇğĞıİöÖşŞüÜéÉèÈêÊáÁàÀâÂíÍìÌîÎóÓòÒôÔúÚùÙûÛÿŸýÝžŽçÇñÑß\'\s?-]+$'
    return bool(re.match(pattern, name))

def all_question_marks(name):
    """
    Checks if the name consists entirely of '?' characters.
    """
    return all(char == '?' for char in name)

def process_csv(input_file, output_file, process_types, replace_non_latin, blacklist_file):
    # Load blacklist
    blacklist = load_blacklist(blacklist_file)

    # Load German language model
    nlp = spacy.load('de_core_news_sm')

    # Create a list of valid characters (Latin alphabets from various languages)
    valid_chars = string.ascii_letters + string.whitespace + "äöüßÄÖÜáàâãåçéèêëíìîïñóòôõøúùûýÿÁÀÂÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÕØÚÙÛÝ"

    invalid_numbers = []
    invalid_names = []
    non_latin_names = []
    changed_names = []

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

            if 'name' in process_types:
                if not is_latin_name(name):
                    if replace_non_latin:
                        original_name = name
                        name = replace_non_latin_characters(name)
                        if all_question_marks(name):
                            non_latin_names.append(original_name)
                            continue
                        changed_names.append(f"{original_name} -> {name}")
                    else:
                        non_latin_names.append(name)
                        continue

                cleaned_name = clean_name(name)
                if not is_valid_name(cleaned_name):
                    invalid_names.append(name)
                    continue
                if cleaned_name != name:
                    changed_names.append(f"{name} -> {cleaned_name}")
                row['Adı Soyadı'] = cleaned_name

            if 'spacy' in process_types:
                if not is_valid_name_spacy(name, blacklist, valid_chars, nlp):
                    invalid_names.append(name)
                    continue

            if 'number' in process_types:
                converted_number = convert_to_international(phone_number)
                if not converted_number:
                    invalid_numbers.append(phone_number)
                    continue
                row['Telefon'] = converted_number

            writer.writerow(row)

    if invalid_numbers:
        print("Invalid phone numbers removed:")
        for number in invalid_numbers:
            print(number)

    if invalid_names:
        print("Invalid names removed:")
        for name in invalid_names:
            print(name)

    if non_latin_names:
        print("Names removed due to non-Latin characters or consisting entirely of '?':")
        for name in non_latin_names:
            print(name)

    if changed_names:
        print("Names changed:")
        for name_change in changed_names:
            print(name_change)

def main():
    parser = argparse.ArgumentParser(description="Process CSV file to clean phone numbers and/or names.")
    parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file')
    parser.add_argument('--process_types', '-p', choices=['number', 'name', 'spacy'], nargs='+', required=True, help="Type of processing to be done: 'number' to process only phone numbers, 'name' to process only names, 'spacy' to process names using spacy's NER")
    parser.add_argument('--replace_non_latin', '-r', action='store_true', help="Replace non-Latin characters with '?' in names")
    parser.add_argument('--blacklist', '-b', required=True, help='Blacklist file path')

    args = parser.parse_args()

    process_csv(args.input, args.output, args.process_types, args.replace_non_latin, args.blacklist)
    print(f"Processed data has been saved to {args.output}")

if __name__ == "__main__":
    main()
