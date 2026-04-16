import secrets
import string

from django.contrib.auth.hashers import check_password, make_password


RECOVERY_KEY_PREFIX = "HFIR"
RECOVERY_KEY_GROUPS = 5
RECOVERY_KEY_GROUP_LENGTH = 4
RECOVERY_KEY_ALPHABET = "".join(
    character
    for character in string.ascii_uppercase + string.digits
    if character not in {"0", "1", "I", "O"}
)


def generate_recovery_key():
    groups = [
        "".join(secrets.choice(RECOVERY_KEY_ALPHABET) for _ in range(RECOVERY_KEY_GROUP_LENGTH))
        for _ in range(RECOVERY_KEY_GROUPS)
    ]
    return "-".join([RECOVERY_KEY_PREFIX, *groups])


def normalize_recovery_key(value):
    return "-".join(value.strip().upper().replace(" ", "-").split("-"))


def hash_recovery_key(recovery_key):
    return make_password(normalize_recovery_key(recovery_key))


def check_recovery_key(recovery_key, encoded_hash):
    return check_password(normalize_recovery_key(recovery_key), encoded_hash)
