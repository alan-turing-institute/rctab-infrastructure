"""Configuration values for the RCTab deployment."""
from typing import Final, Optional
from unittest.mock import patch
from pulumi import Config, Output, get_stack
from pulumi_azure_native.web import NameValuePairArgs
from os import environ
from utils import (
    assert_is_file,
    assert_str_true_or_false,
    assert_valid_log_level,
    assert_valid_uuid_list,
    check_valid_ip_address,
    format_list_str,
    format_secret_list_str,
    raise_billing_or_mgmt,
    validate_ticker_stack_combination,
)

config = Config()

# If sphynx autodoc is running the code, mock the calls to config require to
# return some default value (otherwise the sphynx autodoc will fail)
if environ.get("SPHYNX_AUTODOC_MODE", "false") == "true":
    patch("pulumi.Config.require", return_value = "dummy").start()
    patch("pulumi.Config.require_secret", return_value = Output.secret("")).start()
    def assert_is_file(filepath: str) -> str:
        return(filepath)

# Hardcoded config
SESSION_TIMEOUT_MINUTES: Final[str] = "90"
DATABASE_NAME: Final[str] = "RCTab"
APP_MODULE: Final[str] = "rctab:app"
STACK_NAME: Final[str] = f"{get_stack()}"
RCTAB_APP_USER: Final[str] = "rctab-api-user"

# Organisation name
ORGANISATION: Final[str] = config.require("organisation")
TICKER: Final[str] = config.require("ticker")
IDENTIFIER: Final[str] = validate_ticker_stack_combination(TICKER, STACK_NAME)

# Default image tag for latest major version
RCTAB_TAG: Final[str] = config.get("rctab_tag") or "0.latest"

# Optional CI setting
AUTO_DEPLOY: Final[str] = assert_str_true_or_false(config.get("auto_deploy")) or "true"

# optional docker images config
DOCKER_REGISTRY_SERVER_URL: Final[Output[str]] = config.get_secret(
    "docker_registry_server_url"
) or Output.secret("https://index.docker.io/v1")
DOCKER_REGISTRY_SERVER_USERNAME: Final[Output[str]] = config.get_secret(
    "docker_registry_server_username"
) or Output.secret("")
DOCKER_REGISTRY_SERVER_PASSWORD: Final[Output[str]] = config.get_secret(
    "docker_registry_server_password"
) or Output.secret("")
DOCKER_API_IMAGE: Final[str] = (
    config.get("docker_api_image") or f"turingrc/rctab-api:{RCTAB_TAG}"
)
DOCKER_USAGE_IMAGE: Final[str] = (
    config.get("docker_usage_image") or f"turingrc/rctab-usage:{RCTAB_TAG}"
)
DOCKER_STATUS_IMAGE: Final[str] = (
    config.get("docker_status_image") or f"turingrc/rctab-status:{RCTAB_TAG}"
)
DOCKER_CONTROLLER_IMAGE: Final[str] = (
    config.get("docker_controller_image") or f"turingrc/rctab-controller:{RCTAB_TAG}"
)

# required user config
PRIMARY_IP: Final[Output[str]] = config.require_secret("primary_ip_address").apply(
    check_valid_ip_address
)
DB_ROOT_CERT_PATH: Final[str] = config.require("db_root_cert_path")
AD_SERVER_ADMIN: Final[Output[str]] = config.require_secret("ad_server_admin")
AD_TENANT_ID: Final[Output[str]] = config.require_secret("ad_tenant_id")
AD_API_CLIENT_ID: Final[Output[str]] = config.require_secret("ad_api_client_id")
AD_API_CLIENT_SECRET: Final[Output[str]] = config.require_secret("ad_api_client_secret")
AD_STATUS_CLIENT_ID: Final[Output[str]] = config.require_secret("ad_status_client_id")
AD_STATUS_CLIENT_SECRET: Final[Output[str]] = config.require_secret(
    "ad_status_client_secret"
)

# Additional required user config
SENDGRID_API_KEY: Final[Optional[Output[str]]] = config.get_secret("sendgrid_api_key")
SENDGRID_SENDER_EMAIL: Final[Optional[Output[str]]] = config.get_secret(
    "sendgrid_sender_email"
)
NOTIFIABLE_ROLES: Final[Optional[str]] = format_list_str(config.get("notifiable_roles"))
ROLES_FILTER: Final[Optional[str]] = format_list_str(config.get("roles_filter"))
ADMIN_EMAIL_RECIPIENTS: Final[Optional[Output[str]]] = format_secret_list_str(
    config.get_secret("admin_email_recipients")
)
IGNORE_WHITELIST: Final[Optional[str]] = assert_str_true_or_false(
    config.get("ignore_whitelist")
)
WHITELIST: Final[Optional[str]] = format_list_str(
    assert_valid_uuid_list(config.get("whitelist"))
)
LOG_LEVEL: Final[Optional[str]] = assert_valid_log_level(config.get("log_level"))


# XOR
BILLING_ACCOUNT_ID: Final[Output[str]] = config.get_secret(
    "billing_account_id"
) or Output.secret("")
MGMT_GROUP: Final[Output[str]] = config.get_secret("usage_mgmt_group") or Output.secret(
    ""
)

BILLING_OR_MGMT: Final[Output[NameValuePairArgs]] = Output.all(
    billing=BILLING_ACCOUNT_ID, mgmt=MGMT_GROUP
).apply(raise_billing_or_mgmt)

assert_is_file(DB_ROOT_CERT_PATH)
