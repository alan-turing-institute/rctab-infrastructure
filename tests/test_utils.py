import unittest
from pathlib import Path

import pulumi
from pulumi import Output
from pulumi_azure_native import dbforpostgresql
from pulumi_azure_native.web import NameValuePairArgs

from rctab_infrastructure.utils import (
    assert_is_file,
    assert_str_true_or_false,
    assert_valid_int_list,
    assert_valid_log_level,
    assert_valid_uuid_list,
    check_valid_ip_address,
    format_list_int,
    format_list_str,
    format_secret_list_str,
    is_valid_uuid,
    raise_billing_or_mgmt,
    raise_if_none,
    validate_sku_type,
    validate_ticker_stack_combination,
)


class SyncTestCase(unittest.TestCase):
    """Normal, synchronous tests."""

    def test_format_list_str(self):
        self.assertEqual('["abc", "def", "ghi"]', format_list_str("abc, def, ghi"))

    def test_format_list_int(self):
        self.assertEqual("[1, 2]", format_list_int("1, 2"))

    def test_assert_str_true_or_false(self):
        self.assertEqual("true", assert_str_true_or_false("true"))
        self.assertEqual("false", assert_str_true_or_false("false"))

        with self.assertRaises(AssertionError):
            assert_str_true_or_false("True")

        self.assertIsNone(assert_str_true_or_false(None))

    def test_raise_if_none(self):
        with self.assertRaises(ValueError) as cm:
            raise_if_none(None)
        self.assertEqual("Value should not be None", str(cm.exception))

        self.assertEqual("AOK", raise_if_none("AOK"))
        self.assertEqual(100, raise_if_none(100))
        self.assertEqual([100], raise_if_none([100]))
        self.assertEqual({"a": 100}, raise_if_none({"a": 100}))

    def test_assert_is_file(self):
        afilethatexists = str(Path(__file__))
        afilethatdoesnotexist = "afilethatdoesnotexist.tmp"
        self.assertEqual(afilethatexists, assert_is_file(afilethatexists))
        with self.assertRaises(AssertionError):
            assert_is_file(afilethatdoesnotexist)

    def test_validate_ticker_stack_combination(self):
        self.assertEqual("tkr-stack", validate_ticker_stack_combination("tkr", "stack"))

        with self.assertRaises(AssertionError) as cm:
            validate_ticker_stack_combination("a", "ticker")
        self.assertEqual("Ticker cannot be less than 2 characters", str(cm.exception))

        with self.assertRaises(AssertionError) as cm:
            validate_ticker_stack_combination("ticker_", "stack")
        self.assertEqual("Ticker cannot be more than 6 characters", str(cm.exception))

        valid_identifier_pattern = r"^[a-zA-Z0-9-]{3,20}$"
        msg = (
            "The organisation and stack name must match the pattern "
            f"'{valid_identifier_pattern}' "
        )
        with self.assertRaises(AssertionError) as cm:
            validate_ticker_stack_combination("tkr..", "stack..")
        self.assertEqual(msg + "but is 'tkr..-stack..-abcdefgh'.", str(cm.exception))

        with self.assertRaises(AssertionError) as cm:
            validate_ticker_stack_combination("tk", "atickernamethatistoo")
        self.assertEqual(
            msg + "but is 'tk-atickernamethatistoo-abcdefgh'.", str(cm.exception)
        )

    def test_is_valid_uuid(self):
        self.assertTrue(is_valid_uuid("00000000-0000-0000-0000-000000000000"))
        self.assertFalse(is_valid_uuid("0000000-0000-0000-0000-000000000000"))

    def test_assert_valid_uuid_list(self) -> None:
        self.assertIsNone(assert_valid_uuid_list(None))
        self.assertEqual(
            assert_valid_uuid_list(
                "00000000-0000-0000-0000-000000000000, "
                "11111111-1111-1111-1111-111111111111"
            ),
            "00000000-0000-0000-0000-000000000000, "
            "11111111-1111-1111-1111-111111111111",
        )
        with self.assertRaises(AssertionError) as cm:
            assert_valid_uuid_list("hi")
        self.assertEqual("hi is not a valid UUID", str(cm.exception))

    def test_assert_valid_log_level(self):
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
        for level in allowed_levels:
            self.assertEqual(level, assert_valid_log_level(level))
        self.assertEqual("CRITICAL", assert_valid_log_level("critical"))
        self.assertIsNone(assert_valid_log_level(None))
        with self.assertRaises(AssertionError) as cm:
            assert_valid_log_level("hi")
        self.assertEqual(f"HI not in {allowed_levels}", str(cm.exception))

    def test_check_valid_ip_address(self):
        self.assertEqual("192.168.123.132", check_valid_ip_address("192.168.123.132"))
        with self.assertRaises(ValueError):
            check_valid_ip_address("092.168.123.132")

    def test_raise_billing_or_mgmt(self):
        billing_kwargs = {"billing": "mybillinggroup", "mgmt": ""}
        billing_return = NameValuePairArgs(
            name="BILLING_ACCOUNT_ID", value="mybillinggroup"
        )
        mgmt_kwargs = {"billing": "", "mgmt": "mymgmtgroup"}
        mgmt_return = NameValuePairArgs(name="MGMT_GROUP", value="mymgmtgroup")
        self.assertEqual(billing_return, raise_billing_or_mgmt(billing_kwargs))
        self.assertEqual(mgmt_return, raise_billing_or_mgmt(mgmt_kwargs))

        bad_kwargs = {"billing": "", "mgmt": ""}
        msg = (
            "One of billing_account_id or usage_mgmt_group "
            "should be set but neither is."
        )
        with self.assertRaises(ValueError) as cm:
            raise_billing_or_mgmt(bad_kwargs)
        self.assertEqual(msg, str(cm.exception))

        bad_kwargs = {"billing": "mybillinggroup", "mgmt": "mymgmtgroup"}
        msg = (
            "Only one of billing_account_id or usage_mgmt_group "
            "should be set but both are."
        )
        with self.assertRaises(ValueError) as cm:
            raise_billing_or_mgmt(bad_kwargs)
        self.assertEqual(msg, str(cm.exception))

    def test_assert_valid_int_list(self) -> None:
        self.assertIsNone(assert_valid_int_list(None))
        self.assertEqual(assert_valid_int_list(""), "")
        self.assertEqual(assert_valid_int_list("1, 7, 14, 21"), "1, 7, 14, 21")
        with self.assertRaises(AssertionError) as cm:
            assert_valid_int_list("12.4")
        self.assertEqual("12.4 is not a valid integer.", str(cm.exception))

    def test_validate_sku_type(self) -> None:
        """We can validate the choice of sku_type."""
        # db_sku_name="Standard_B1ms",
        self.assertEqual(
            {
                "db_sku_name": "Standard_B1ms",
                "db_sku_tier": dbforpostgresql.SkuTier.BURSTABLE,
            },
            validate_sku_type("test"),
        )
        self.assertEqual(
            {
                "db_sku_name": "Standard_D4ds_v4",
                "db_sku_tier": dbforpostgresql.SkuTier.GENERAL_PURPOSE,
            },
            validate_sku_type("prod"),
        )
        with self.assertRaises(ValueError) as cm:
            validate_sku_type("dev")
        self.assertEqual("sku_type must be one of ['test', 'prod']", str(cm.exception))


class AsyncTestCase(unittest.TestCase):
    """Tests that return Futures or Outputs.

    Remember to decorate each test and to return the awaitables."""

    @pulumi.runtime.test  # type: ignore
    def test_format_secret_list_str(self) -> Output[str]:
        def check_list_str(list_str: str) -> str:
            self.assertEqual('["abc", "def", "ghi"]', list_str)
            return ""

        output = format_secret_list_str(Output.secret("abc, def, ghi"))
        assert output is not None
        return output.apply(check_list_str)
