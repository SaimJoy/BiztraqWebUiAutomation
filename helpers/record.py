import random
import string

from config import DATE_OF_BIRTH


def make_random_record():
    """Random First Name and Last Name; Date of Birth is typed as digits for the Kendo mask."""
    first_name = "".join(random.choices(string.ascii_lowercase, k=6)).capitalize()
    last_name = "".join(random.choices(string.ascii_lowercase, k=7)).capitalize()
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": DATE_OF_BIRTH,
        "display_name": f"{first_name} {last_name}",
    }
