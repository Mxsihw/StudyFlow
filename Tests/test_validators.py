import unittest

from validators import (
    ValidationError,
    validate_date,
    validate_datetime,
    validate_non_negative_integer,
    validate_optional_text,
    validate_required_text,
    validate_tag_name,
)
class TestRequiredTextValidation(unittest.TestCase):

    def test_required_text_is_trimmed(self):
        result = validate_required_text(
            "  StudyFlow  ",
            "Name",
        )

        self.assertEqual(result, "StudyFlow")

    def test_required_text_rejects_empty_string(self):
        with self.assertRaises(ValidationError):
            validate_required_text("", "Name")

    def test_required_text_rejects_whitespace_only(self):
        with self.assertRaises(ValidationError):
            validate_required_text("   ", "Name")

    def test_required_text_rejects_non_string(self):
        with self.assertRaises(ValidationError):
            validate_required_text(123, "Name")


class TestTagNameValidation(unittest.TestCase):

    def test_tag_name_is_trimmed(self):
        result = validate_tag_name("  Python  ")

        self.assertEqual(result, "Python")

    def test_tag_name_rejects_empty_string(self):
        with self.assertRaises(ValidationError):
            validate_tag_name("")

    def test_tag_name_rejects_whitespace_only(self):
        with self.assertRaises(ValidationError):
            validate_tag_name("   ")

    def test_tag_name_rejects_non_string(self):
        with self.assertRaises(ValidationError):
            validate_tag_name(123)


class TestOptionalTextValidation(unittest.TestCase):

    def test_optional_text_allows_none(self):
        result = validate_optional_text(
            None,
            "Description",
        )

        self.assertIsNone(result)

    def test_optional_text_is_trimmed(self):
        result = validate_optional_text(
            "  Notes  ",
            "Description",
        )

        self.assertEqual(result, "Notes")

    def test_optional_text_allows_empty_string(self):
        result = validate_optional_text(
            "   ",
            "Description",
        )

        self.assertEqual(result, "")

    def test_optional_text_rejects_non_string(self):
        with self.assertRaises(ValidationError):
            validate_optional_text(123, "Description")


class TestNonNegativeIntegerValidation(unittest.TestCase):

    def test_allows_zero(self):
        result = validate_non_negative_integer(
            0,
            "Credits",
        )

        self.assertEqual(result, 0)

    def test_allows_positive_integer(self):
        result = validate_non_negative_integer(
            3,
            "Credits",
        )

        self.assertEqual(result, 3)

    def test_rejects_negative_integer(self):
        with self.assertRaises(ValidationError):
            validate_non_negative_integer(
                -1,
                "Credits",
            )

    def test_rejects_boolean(self):
        with self.assertRaises(ValidationError):
            validate_non_negative_integer(
                True,
                "Credits",
            )

    def test_rejects_non_integer(self):
        with self.assertRaises(ValidationError):
            validate_non_negative_integer(
                "3",
                "Credits",
            )

    def test_rejects_none_by_default(self):
        with self.assertRaises(ValidationError):
            validate_non_negative_integer(
                None,
                "Credits",
            )

    def test_allows_none_when_requested(self):
        result = validate_non_negative_integer(
            None,
            "Credits",
            allow_none=True,
        )

        self.assertIsNone(result)

class TestDateValidation(unittest.TestCase):

    def test_gregorian_date_is_preserved(self):
        result = validate_date(
            "2026-11-05",
            "Date",
        )

        self.assertEqual(result, "2026-11-05")

    def test_jalali_date_is_converted_to_gregorian(self):
        result = validate_date(
            "1405-08-14",
            "Date",
        )

        self.assertEqual(result, "2026-11-05")

    def test_date_is_trimmed(self):
        result = validate_date(
            "  2026-11-05  ",
            "Date",
        )

        self.assertEqual(result, "2026-11-05")

    def test_rejects_invalid_date_format(self):
        with self.assertRaises(ValidationError):
            validate_date(
                "05/11/2026",
                "Date",
            )

    def test_rejects_invalid_gregorian_date(self):
        with self.assertRaises(ValidationError):
            validate_date(
                "2026-02-30",
                "Date",
            )

    def test_rejects_invalid_jalali_date(self):
        with self.assertRaises(ValidationError):
            validate_date(
                "1405-13-01",
                "Date",
            )

    def test_date_allows_none_when_requested(self):
        result = validate_date(
            None,
            "Date",
            allow_none=True,
        )

        self.assertIsNone(result)


class TestDateTimeValidation(unittest.TestCase):

    def test_gregorian_datetime_is_preserved(self):
        result = validate_datetime(
            "2026-11-05 09:30",
            "DateTime",
        )

        self.assertEqual(
            result,
            "2026-11-05 09:30",
        )

    def test_jalali_datetime_is_converted_to_gregorian(self):
        result = validate_datetime(
            "1405-08-14 09:30",
            "DateTime",
        )

        self.assertEqual(
            result,
            "2026-11-05 09:30",
        )

    def test_datetime_is_trimmed(self):
        result = validate_datetime(
            "  2026-11-05 09:30  ",
            "DateTime",
        )

        self.assertEqual(
            result,
            "2026-11-05 09:30",
        )

    def test_rejects_invalid_datetime_format(self):
        with self.assertRaises(ValidationError):
            validate_datetime(
                "2026-11-05T09:30",
                "DateTime",
            )

    def test_rejects_invalid_time(self):
        with self.assertRaises(ValidationError):
            validate_datetime(
                "2026-11-05 25:00",
                "DateTime",
            )

    def test_datetime_allows_none_when_requested(self):
        result = validate_datetime(
            None,
            "DateTime",
            allow_none=True,
        )

        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()