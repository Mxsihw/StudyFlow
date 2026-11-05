from datetime import datetime
import jdatetime

class ValidationError(ValueError):
    """Raised when service-layer input validation fails."""


def validate_required_text(value, field_name):
    """
    Validate required text input and return the normalized value.

    Leading and trailing whitespace is removed.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    normalized_value = value.strip()

    if not normalized_value:
        raise ValidationError(f"{field_name} cannot be empty.")

    return normalized_value


def validate_optional_text(value, field_name):
    """
    Validate optional text input and return the normalized value.

    None is allowed. String values have leading and trailing
    whitespace removed.
    """
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    return value.strip()


def validate_non_negative_integer(value, field_name, allow_none=False):
    """
    Validate that value is a non-negative integer.

    Boolean values are rejected even though bool is a subclass of int.
    If allow_none is True, None is accepted.
    """
    if value is None:
        if allow_none:
            return None

        raise ValidationError(f"{field_name} is required.")

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer.")

    if value < 0:
        raise ValidationError(f"{field_name} cannot be negative.")

    return value

def _parse_supported_date(value, field_name):
    """
    Parse a Gregorian or Jalali date.

    Gregorian input: YYYY-MM-DD
    Jalali input:    YYYY-MM-DD

    Jalali dates are converted to Gregorian dates.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    normalized_value = value.strip()

    if not normalized_value:
        raise ValidationError(f"{field_name} cannot be empty.")

    try:
        year, month, day = map(int, normalized_value.split("-"))
    except ValueError as error:
        raise ValidationError(
            f"{field_name} must be in YYYY-MM-DD format."
        ) from error

    if 1000 <= year < 1800:
        try:
            return jdatetime.date(
                year,
                month,
                day,
            ).togregorian()
        except ValueError as error:
            raise ValidationError(
                f"{field_name} is not a valid Jalali date."
            ) from error

    try:
        return datetime.strptime(
            normalized_value,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValidationError(
            f"{field_name} is not a valid Gregorian date."
        ) from error


def validate_date(value, field_name, allow_none=False):
    """
    Validate a Gregorian or Jalali date.

    Returns the normalized Gregorian date in YYYY-MM-DD format.
    """
    if value is None:
        if allow_none:
            return None

        raise ValidationError(f"{field_name} is required.")

    parsed_date = _parse_supported_date(
        value,
        field_name,
    )

    return parsed_date.strftime("%Y-%m-%d")

def validate_datetime(value, field_name, allow_none=False):
    """
    Validate a Gregorian or Jalali datetime.

    Input format:
        YYYY-MM-DD HH:MM

    Returns the normalized Gregorian datetime
    in YYYY-MM-DD HH:MM format.
    """
    if value is None:
        if allow_none:
            return None

        raise ValidationError(f"{field_name} is required.")

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    normalized_value = value.strip()

    if not normalized_value:
        raise ValidationError(f"{field_name} cannot be empty.")

    try:
        date_part, time_part = normalized_value.split()
        hour, minute = map(int, time_part.split(":"))
    except ValueError as error:
        raise ValidationError(
            f"{field_name} must be in YYYY-MM-DD HH:MM format."
        ) from error

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValidationError(
            f"{field_name} contains an invalid time."
        )

    parsed_date = _parse_supported_date(
        date_part,
        field_name,
    )

    try:
        parsed_datetime = datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            hour,
            minute,
        )
    except ValueError as error:
        raise ValidationError(
            f"{field_name} is not a valid datetime."
        ) from error

    return parsed_datetime.strftime("%Y-%m-%d %H:%M")

def validate_datetime_order(
    start_datetime,
    end_datetime,
):
    """
    Ensure that the end datetime is after the start datetime.
    """
    if end_datetime is None:
        return

    start = datetime.strptime(
        start_datetime,
        "%Y-%m-%d %H:%M",
    )

    end = datetime.strptime(
        end_datetime,
        "%Y-%m-%d %H:%M",
    )

    if end <= start:
        raise ValidationError(
            "End datetime must be after start datetime."
        )