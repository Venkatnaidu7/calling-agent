import phonenumbers
from phonenumbers import NumberParseException

def normalize_phone(number: str, default_country: str = "US") -> str:
    try:
        parsed_number = phonenumbers.parse(number, default_country)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException as e:
        raise ValueError(f"Invalid phone number format: {str(e)}")

def validate_phone(number: str, default_country: str = "US") -> bool:
    try:
        parsed_number = phonenumbers.parse(number, default_country)
        return phonenumbers.is_valid_number(parsed_number)
    except NumberParseException:
        return False

def format_phone(number: str, format: str = "E164") -> str:
    try:
        parsed_number = phonenumbers.parse(number, None)
        if format.upper() == "E164":
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        elif format.upper() == "INTERNATIONAL":
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        elif format.upper() == "NATIONAL":
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        else:
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return number

def get_country_code(number: str) -> str:
    try:
        parsed_number = phonenumbers.parse(number, None)
        return str(parsed_number.country_code)
    except NumberParseException:
        return ""
