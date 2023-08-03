"""General infrastructure code utilities."""
import ipaddress
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar

from pulumi import Output
from pulumi_azure_native.web import NameValuePairArgs

T = TypeVar("T")


def format_list_str(input_str: Optional[str]) -> Optional[str]:
    """
    Convert a comma-separated list of strings into a JSON compatible list.

    Args:
        input_str: A comma separated list such as 'abc, def, ghi'

    Example:
        >>> format_list_str("abc, def, ghi")

    Returns:
        A JSON compatible list string such as '["abc", "def", "ghi"]'
    """
    if input_str:
        formatted_str = ", ".join(
            [f'"{item.strip()}"' for item in input_str.split(",")]
        )
        return f"[{formatted_str}]"
    return input_str


def format_secret_list_str(input_str: Optional[Output[str]]) -> Optional[Output[str]]:
    """
    Convert a comma-separated list into a JSON compatible list.

    Args:
        input_str: A comma separated list such as 'abc, def, ghi', wrapped in an Output.

    Example:
        >>> format_secret_list_str(Ouput.secret("abc, def, ghi"))

    Returns:
        A JSON compatible secret list string such as '["abc", "def", "ghi"]'
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
    """
    Raise an exception if value is None.

    Args:
        value: The value to check.

    Example:
        >>> raise_if_none("not None")

    Raises:
        ValueError: If value is None.

    Returns:
        The value if it is not None.
    """
    if value is None:
        raise ValueError("Value should not be None")
    return value


def assert_is_file(filepath: str) -> str:
    """
    Raise an error if filepath is not a valid path to a real file.

    Args:
        filepath: The path to check.

    Example:
        >>> assert_is_file("src/webapp.py")

    Raises:
        AssertionError: If filepath is not a valid path to a real file.

    Returns:
        The filepath if it is a valid path to a real file.
    """
    assert Path(filepath).is_file()
    return filepath


def assert_str_true_or_false(checkstr: Optional[str]) -> Optional[str]:
    """
    Raise an error if checkstr is not 'true' or 'false'.

    Args:
        checkstr: The string to check.

    Example:
        >>> assert_str_true_or_false("true")
        >>> assert_str_true_or_false("false")

    Raises:
        AssertionError: If checkstr is not 'true' or 'false'.

    Returns:
        checkstr if the value is 'true' or 'false'.
    """
    if checkstr:
        assert checkstr in (
            "true",
            "false",
        ), "Invalid value for auto_deploy. Allowed values are 'true' or 'false'."
    return checkstr


def validate_ticker_stack_combination(ticker: str, stack: str) -> str:
    """
    Raise an error if ticker and stack names are not valid names.

    The length of the ticker must be between 2 and 5 characters. The stack name can
    be any length but combined the two must not be larger than 14 characters long
    due to resource naming limits. See
    https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules

    Args:
        ticker: The name of the ticker.
        stack: The name of the stack.

    Example:
        >>> validate_ticker_stack_combination("abc", "def")

    Raises:
        AssertionError: If ticker is not between 2 and 5 characters long or if
        the name does not meet the naming requirements.

    Returns:
        The proposed identifier for the stack.
    """
    valid_identifier_pattern = r"^[a-zA-Z0-9-]{3,20}$"
    proposed_identifier = f"{ticker}-{stack}"
    org_stack = f"{proposed_identifier}-abcdefgh"
    # check ticker and stack name together is valid
    assert len(ticker) > 1, "Ticker cannot be less than 2 characters"
    assert len(ticker) < 6, "Ticker cannot be more than 5 characters"
    assert re.match(valid_identifier_pattern, org_stack), (
        f"The organisation and stack name must match the pattern "
        f"'{valid_identifier_pattern}'. ",
        "Please ensure the combined stack and organisation names "
        "are less than 24 characters long.",
    )
    return proposed_identifier


def raise_billing_or_mgmt(kwargs: Dict[str, Any]) -> NameValuePairArgs:
    """
    Raise if both billing and mngmt are set or neither are set.

    Args:
        kwargs: A dictionary of keyword arguments including billing or mgmt.

    Example:
        >>> raise_billing_or_mgmt({"billing": "00000000-0000-0000-0000-000000000000"})
        >>> raise_billing_or_mgmt({"mgmt": "00000000-0000-0000-0000-000000000000"})

    Raises:
        ValueError: If both billing and mgmt are set or neither are set.

    Returns:
        A NameValuePairArgs object with either BILLING_ACCOUNT_ID or MGMT_GROUP set.
    """
    billing = kwargs["billing"]
    mgmt = kwargs["mgmt"]
    if (billing and mgmt) or (not billing and not mgmt):
        raise ValueError("Either billing_account_id or mgmt_group must be set")
    if billing:
        return NameValuePairArgs(name="BILLING_ACCOUNT_ID", value=billing)
    return NameValuePairArgs(name="MGMT_GROUP", value=mgmt)


def is_valid_uuid(check_uuid: str) -> bool:
    """
    Check a provided uuid is a valid uuid.

    Args:
        check_uuid: The uuid to check.

    Example:
        >>> is_valid_uuid("00000000-0000-0000-0000-000000000000")

    Returns:
        True if check_uuid is a valid uuid. False otherwise.
    """
    try:
        uuid.UUID(check_uuid)
        return True
    except ValueError:
        return False


def assert_valid_uuid_list(whitelist: Optional[str]) -> Optional[str]:
    """
    Check the uuid list provided is a list of valid uuid's or an empty string.

    Args:
        whitelist: A comma separated list of uuid's.

    Example:
        >>> assert_valid_uuid_list(
            "00000000-0000-0000-0000-000000000000,
            00000000-0000-0000-0000-0000000000001"
        )

    Raises:
        AssertionError: If any of the uuid's in the list are not valid uuid's.

    Returns:
        The whitelist if it is a list of valid uuid's or an empty string.
    """
    if whitelist:
        uuids = whitelist.split(",")
        for item in uuids:
            assert (
                is_valid_uuid(item.strip()) is True
            ), f"{item.strip()} is not a valid UUID"
    return whitelist


def assert_valid_log_level(log_level: Optional[str]) -> Optional[str]:
    """
    Check the log level is a valid log level.

    See https://docs.python.org/3/library/logging.html#logging-levels.

    Args:
        log_level: The log level to check.

    Example:
        >>> assert_valid_log_level("INFO")

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
    """
    Check an IP address is a valid IP address.

    Args:
        ip2check: The IP address to check.

    Example:
        >>> check_valid_ip_address("192.168.123.132")

    Returns:
        The IP address if it is a valid IP address.
    """
    ipaddress.ip_address(ip2check)
    return ip2check
