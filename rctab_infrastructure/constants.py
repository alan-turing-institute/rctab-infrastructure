"""Configuration values for the RCTab deployment.

This module contains the configuration values for the RCTab deployment.
REQUIRED values must be set using `pulumi config set ...`. Optional values can be
set using `pulumi config set ...` or can be ignored, in which case they will be
given a default value. Note that the pulumi config values are lowercase
versions of the Python variable names.

Attributes:
    SESSION_TIMEOUT_MINUTES (str): The number of minutes before a user session
        times out. Defaults to "90".
    DATABASE_NAME (str): The name of the database to create. Defaults to "RCTab".
    APP_MODULE (str): The name of the FastAPI app. Defaults to "rctab:app".
    STACK_NAME (str): The name of the pulumi stack. Set automatically.
    RCTAB_APP_USER (str): The name of the user to create for the RCTab app.
        Defaults to "rctab-api-user".
    ORGANISATION (str): Your organisation's name. REQUIRED.
    TICKER (str): A short form of your organisation's name. REQUIRED.
    IDENTIFIER (str): The identifier of the organisation. This is the combination
        of the ticker and stack name. Set automatically.
    RCTAB_TAG (str): The tag of the RCTab Docker image to use. Defaults to "1.latest".
    AUTO_DEPLOY (str): Whether to automatically pull new images. Defaults to "true".
    DOCKER_REGISTRY_SERVER_URL (str): The URL of the Docker registry server.
        Defaults to "https://index.docker.io/v1".
    DOCKER_REGISTRY_SERVER_USERNAME (str): The username for the Docker registry.
        Defaults to an empty string.
    DOCKER_REGISTRY_SERVER_PASSWORD (str): The password for Docker registry.
        Defaults to an empty string.
    DOCKER_API_IMAGE (str): The name of the Docker image for the API.
        Defaults to "turingrc/rctab-api:1.latest".
    DOCKER_USAGE_IMAGE (str): The name of the Docker image for the usage app.
        Defaults to "turingrc/rctab-usage:1.latest".
    DOCKER_STATUS_IMAGE (str): The name of the Docker image for the status app.
        Defaults to "turingrc/rctab-status:1.latest".
    DOCKER_CONTROLLER_IMAGE (str): The name of the Docker image for the
        controller app. Defaults to "turingrc/rctab-controller:1.latest".
    PRIMARY_IP (str): Your organisation's static IP address. REQUIRED.
    DB_ROOT_CERT_PATH (str): The path to the root certificate for the database.
        REQUIRED.
    AD_SERVER_ADMIN (str): The name of the admin user for the AD server.
        REQUIRED.
    AD_TENANT_ID (str): The ID of your Azure AD tenant. REQUIRED.
    AD_API_CLIENT_ID (str): The Azure AD ID of the API app.
        REQUIRED.
    AD_API_CLIENT_SECRET (str): The Azure AD client secret for the API app.
        REQUIRED.
    AD_STATUS_CLIENT_ID (str): The Azure AD ID of the status app service principal.
        REQUIRED.
    AD_STATUS_CLIENT_SECRET (str): The Azure AD secret for the status app
        service principal. REQUIRED.
    SENDGRID_API_KEY (str): The API key for SendGrid. REQUIRED.
    SENDGRID_SENDER_EMAIL (str): The sender email address for SendGrid. REQUIRED.
    EXPIRY_EMAIL_FREQ (str): The list of days to send expiry email notification.
        REQUIRED.
    NOTIFIABLE_ROLES (str): The roles to notify. Defaults to an empty string.
    ROLES_FILTER (str): The roles to filter. Defaults to an empty string.
    ADMIN_EMAIL_RECIPIENTS (str): The email recipients for admin emails.
        Defaults to an empty string.
    IGNORE_WHITELIST (str): Whether to ignore the whitelist. Defaults to an
        empty string.
    WHITELIST (str): The subscription UUID whitelist. Defaults to an empty string.
    LOG_LEVEL (str): The log level. Defaults to an empty string.
    BILLING_ACCOUNT_ID (str): The billing account ID. REQUIRED.
    MGMT_GROUP (str): The management group. REQUIRED.
"""
from typing import Final, Optional

from pulumi import Config, Output, get_stack
from pulumi_azure_native.web import NameValuePairArgs

from rctab_infrastructure.utils import (
    assert_is_file,
    assert_str_true_or_false,
    assert_valid_int_list,
    assert_valid_log_level,
    assert_valid_uuid_list,
    check_valid_ip_address,
    format_list_str,
    format_secret_list_str,
    raise_billing_or_mgmt,
    validate_ticker_stack_combination,
)

config = Config()

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
RCTAB_TAG: Final[str] = config.get("rctab_tag") or "1.latest"

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
EXPIRY_EMAIL_FREQ: Final[Optional[Output[str]]] = assert_valid_int_list(
    config.get("expiry_email_freq")
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
