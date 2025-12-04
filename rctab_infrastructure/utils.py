"""General infrastructure code utilities."""

import ipaddress
import re
import uuid
from pathlib import Path
from typing import Any, Optional, TypeVar

from pulumi import Output
from pulumi_azure_native import dbforpostgresql
from pulumi_azure_native.web import NameValuePairArgs

T = TypeVar("T")


def format_list_str(input_str: Optional[str]) -> Optional[str]:
    """Convert a comma-separated list of strings into a JSON compatible list.

    Args:
        input_str: A comma separated list such as 'abc, def, ghi'

    Returns:
        A JSON compatible list string such as '["abc", "def", "ghi"]'.
    """
    if input_str:
        formatted_str = ", ".join(
            [f'"{item.strip()}"' for item in input_str.split(",")]
        )
        return f"[{formatted_str}]"
    return input_str


def format_list_int(input_str: Optional[str]) -> Optional[str]:
    """Convert a comma-separated list of ints into a JSON compatible list.

    Args:
        input_str: A comma separated list such as '1, 7, 30'

    Returns:
        A JSON compatible list such as '[1, 7, 30]'.
    """
    if input_str:
        return f"[{input_str}]"
    return input_str


def format_secret_list_str(input_str: Optional[Output[str]]) -> Optional[Output[str]]:
    """Convert a comma-separated list into a JSON compatible list.

    Args:
        input_str: A comma separated list such as 'abc, def, ghi', wrapped in an Output.

    Returns:
        A JSON compatible secret list string such as '["abc", "def", "ghi"]'.
    """
    if input_str:
        formatted_str = input_str.apply(
            lambda x: "["
            + ", ".join([f'"{item.strip()}"' for item in x.split(",")])
            + "]"
        )
        return formatted_str
    return input_str


def raise_if_none(value: Optional[T]) -> T:
    """Raise an exception if value is None.

    Args:
        value: The value to check.

    Raises:
        ValueError: If value is None.

    Returns:
        The value if it is not None.
    """
    if value is None:
        raise ValueError("Value should not be None")
    return value


def assert_is_file(filepath: str) -> str:
    """Raise an error if filepath is not a valid path to a real file.

    Args:
        filepath: The path to check.

    Raises:
        AssertionError: If filepath is not a valid path to a real file.

    Returns:
        The filepath if it is a valid path to a real file.
    """
    assert Path(filepath).is_file()
    return filepath


def assert_str_true_or_false(checkstr: Optional[str]) -> Optional[str]:
    """Raise an error if checkstr is not 'true' or 'false'.

    Args:
        checkstr: The string to check.

    Raises:
        AssertionError: If checkstr is not 'true' or 'false'.

    Returns:
        checkstr if the value is 'true' or 'false'.
    """
    if checkstr:
        assert checkstr in (
            "true",
            "false",
        ), f"{checkstr} is an invalid value. Allowed values are 'true' or 'false'."
    return checkstr


def validate_ticker_stack_combination(ticker: str, stack: str) -> str:
    """Raise an error if ticker and stack names are not valid names.

    The length of the ticker must be between 2 and 6 characters. The stack name can
    be any length but combined the two must not be larger than 10 characters long
    due to resource naming limits:
    https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules

    Args:
        ticker: The ticker.
        stack: The name of the stack.

    Raises:
        AssertionError: If ticker is not between 2 and 6 characters long or if
        the name does not meet the naming requirements.

    Returns:
        The proposed identifier for the stack.
    """
    valid_identifier_pattern = r"^[a-zA-Z0-9-]{3,20}$"
    proposed_identifier = f"{ticker}-{stack}"
    org_stack = f"{proposed_identifier}-abcdefgh"
    # check ticker and stack name together is valid
    assert len(ticker) > 1, "Ticker cannot be less than 2 characters"
    assert len(ticker) < 7, "Ticker cannot be more than 6 characters"
    assert re.match(valid_identifier_pattern, org_stack), (
        f"The organisation and stack name must match the pattern "
        f"'{valid_identifier_pattern}' but is '{org_stack}'."
    )
    return proposed_identifier


def validate_sku_type(sku_type: str) -> dict[str, str]:
    """Validate the sku_type is one of the allowed types."""
    allowed_choices = {
        "test": {
            "db_sku_name": "Standard_B1ms",
            "db_sku_tier": dbforpostgresql.SkuTier.BURSTABLE,
        },
        "prod": {
            "db_sku_name": "Standard_D4ds_v4",
            "db_sku_tier": dbforpostgresql.SkuTier.GENERAL_PURPOSE,
        },
    }
    if sku_type not in allowed_choices:
        raise ValueError(f"sku_type must be one of {list(allowed_choices.keys())}")
    return allowed_choices[sku_type]


def raise_billing_or_mgmt(kwargs: dict[str, Any]) -> NameValuePairArgs:
    """Raise if both billing and mgmt are set or neither are set.

    Args:
        kwargs: A dictionary that should have a key of "billing" or of "mgmt".

    Raises:
        ValueError: If both billing and mgmt are set or neither are set.

    Returns:
        A NameValuePairArgs object with either BILLING_ACCOUNT_ID or MGMT_GROUP set.
    """
    billing = kwargs["billing"]
    mgmt = kwargs["mgmt"]
    if billing and mgmt:
        raise ValueError(
            "Only one of billing_account_id or usage_mgmt_group "
            "should be set but both are."
        )
    if (not billing) and (not mgmt):
        raise ValueError(
            "One of billing_account_id or usage_mgmt_group "
            "should be set but neither is."
        )
    if billing:
        return NameValuePairArgs(name="BILLING_ACCOUNT_ID", value=billing)
    return NameValuePairArgs(name="MGMT_GROUP", value=mgmt)


def is_valid_uuid(check_uuid: str) -> bool:
    """Check a provided UUID is a valid UUID.

    Args:
        check_uuid: The UUID to check.

    Returns:
        True if check_uuid is a valid UUID. False otherwise.
    """
    try:
        uuid.UUID(check_uuid)
        return True
    except ValueError:
        return False


def assert_valid_uuid_list(whitelist: Optional[str]) -> Optional[str]:
    """Check the UUID list provided is a list of valid UUIDs or an empty string.

    Args:
        whitelist: A comma separated list of UUIDs.

    Raises:
        AssertionError: If any of the UUIDs in the list are not valid UUIDs.

    Returns:
        The whitelist if it is a list of valid UUIDs or an empty string.
    """
    if whitelist:
        uuids = whitelist.split(",")
        for item in uuids:
            assert (
                is_valid_uuid(item.strip()) is True
            ), f"{item.strip()} is not a valid UUID"
    return whitelist


def assert_valid_log_level(log_level: Optional[str]) -> Optional[str]:
    """Check the log level is a valid log level.

    Log level is not case sensitive and is converted to uppercase before checking.
    See https://docs.python.org/3/library/logging.html#logging-levels.

    Args:
        log_level: The log level to check.

    Raises:
        AssertionError: If the log level is not a valid log level.

    Returns:
        The log level if it is a valid log level.
    """
    if log_level:
        log_level = log_level.upper()
        allowed_levels = (
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARNING",
            "WARN",
            "INFO",
            "DEBUG",
            "NOTSET",
        )
        assert log_level in allowed_levels, f"{log_level} not in {allowed_levels}"
    return log_level


def check_valid_ip_address(ip2check: str):
    """Check an IP address is a valid IP address.

    Args:
        ip2check: The IP address to check.

    Returns:
        The IP address if it is a valid IP address.
    """
    ipaddress.ip_address(ip2check)
    return ip2check


def assert_valid_int_list(int_list: Optional[str]) -> Optional[str]:
    """Check the integer list provided is a list of valid integers or an empty string.

    Args:
        int_list: A comma separated list of integers.

    Raises:
        AssertionError: If any of the items in the list are not valid integers.

    Returns:
        The int_list if it is a list of valid integers or an empty string.
    """
    if int_list:
        integers = int_list.split(",")
        for item in integers:
            assert (
                item.strip().isdecimal() is True
            ), f"{item.strip()} is not a valid integer."
    return int_list
