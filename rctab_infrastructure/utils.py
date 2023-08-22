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
    """Convert a comma-separated list into a JSON compatible list.

    input_str:
        A comma separated list such as 'abc, def, ghi'

    returns:
        A JSON compatible list such as '["abc", "def", "ghi"]'
    """
    if input_str:
        formatted_str = ", ".join(
            [f'"{item.strip()}"' for item in input_str.split(",")]
        )
        return f"[{formatted_str}]"
    return input_str


def format_secret_list_str(input_str: Optional[Output[str]]) -> Optional[Output[str]]:
    """Convert a comma-separated list into a JSON compatible list.

    input_str:
        A comma separated list such as 'abc, def, ghi'

    returns:
        A JSON compatible list such as '["abc", "def", "ghi"]'
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
    """Raise an exception if value is None."""
    if value is None:
        raise ValueError("Value should not be None")
    return value


def assert_is_file(filepath: str) -> str:
    """Raise an error if filepath is not a valid path to a real file."""
    assert Path(filepath).is_file()
    return filepath


def assert_str_true_or_false(checkstr: Optional[str]) -> Optional[str]:
    """Raise an error if checkstr is not 'true' or 'false'."""
    if checkstr:
        assert checkstr in (
            "true",
            "false",
        ), "Invalid value for auto_deploy. Allowed values are 'true' or 'false'."
    return checkstr


def validate_ticker_stack_combination(ticker: str, stack: str) -> str:
    """Raise an error if ticker and stack names are not valid names.

    The length of the ticker must be between 2 and 6 characters. The stack name can
    be any length but combined the two must not be larger than 10 characters long
    due to resource naming limits:
    https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules
    """
    valid_identifier_pattern = r"^[a-zA-Z0-9-]{3,20}$"
    proposed_identifier = f"{ticker}-{stack}"
    org_stack = f"{proposed_identifier}-abcdefgh"
    # check ticker and stack name together is valid
    assert len(ticker) > 1, "Ticker cannot be less than 2 characters"
    assert len(ticker) < 7, "Ticker cannot be more than 6 characters"
    assert re.match(valid_identifier_pattern, org_stack), (
        f"The organisation and stack name must match the pattern "
        f"'{valid_identifier_pattern}'. ",
        "Please ensure the combined stack and organisation names "
        "are less than 24 characters long.",
    )
    return proposed_identifier


def raise_billing_or_mgmt(kwargs: Dict[str, Any]) -> NameValuePairArgs:
    """Raise if both are set or both are not set."""
    billing = kwargs["billing"]
    mgmt = kwargs["mgmt"]
    if (billing and mgmt) or (not billing and not mgmt):
        raise ValueError("Either billing_account_id or usage_mgmt_group must be set")
    if billing:
        return NameValuePairArgs(name="BILLING_ACCOUNT_ID", value=billing)
    return NameValuePairArgs(name="MGMT_GROUP", value=mgmt)


def is_valid_uuid(uuid_: str) -> bool:
    """Check a uuid_ is a valid uuid."""
    try:
        uuid.UUID(uuid_)
        return True
    except ValueError:
        return False


def assert_valid_uuid_list(whitelist: Optional[str]) -> Optional[str]:
    """Check the uuid list provided is a list of valid uuid's or an empty string."""
    if whitelist:
        uuids = whitelist.split(",")
        for item in uuids:
            assert (
                is_valid_uuid(item.strip()) is True
            ), f"{item.strip()} is not a valid UUID"
    return whitelist


def assert_valid_log_level(log_level: Optional[str]) -> Optional[str]:
    """Check the log level is a valid log level.

    See https://docs.python.org/3/library/logging.html#logging-levels.
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
    """Check an IP address is a valid IP address."""
    ipaddress.ip_address(ip2check)
    return ip2check
