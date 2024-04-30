"""Web app infrastructure code."""
import pulumi_azure_native.dbforpostgresql.v20230301preview as dbforpostgresql
import pulumi_random as random
from pulumi import Output, ResourceOptions
from pulumi_azure_native import keyvault, resources, web
from pulumi_tls import PrivateKey

from rctab_infrastructure.constants import (
    AD_API_CLIENT_ID,
    AD_API_CLIENT_SECRET,
    AD_TENANT_ID,
    ADMIN_EMAIL_RECIPIENTS,
    APP_MODULE,
    AUTO_DEPLOY,
    DOCKER_API_IMAGE,
    DOCKER_REGISTRY_SERVER_PASSWORD,
    DOCKER_REGISTRY_SERVER_URL,
    DOCKER_REGISTRY_SERVER_USERNAME,
    IDENTIFIER,
    IGNORE_WHITELIST,
    LOG_LEVEL,
    NOTIFIABLE_ROLES,
    ORGANISATION,
    RCTAB_APP_USER,
    ROLES_FILTER,
    SENDGRID_API_KEY,
    SENDGRID_SENDER_EMAIL,
    SESSION_TIMEOUT_MINUTES,
    WHITELIST,
)
from rctab_infrastructure.utils import raise_if_none

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals


def create_webapp(
    resource_group: resources.ResourceGroup,
    vault: keyvault.Vault,
    app_plan_id: Output[str],
    database_server: dbforpostgresql.Server,
    database: dbforpostgresql.Database,
    database_user_password: random.RandomPassword,
    app_insights_connection_string: Output[str],
    logging_connection_string: Output[str],
    usage_key: PrivateKey,
    status_key: PrivateKey,
    controller_key: PrivateKey,
) -> web.WebApp:
    """Create a webapp and add outbound IPs to database whitelist.

    Args:
        resource_group: The resource group to create the webapp in.
        vault: The keyvault to store the session cookie secret in.
        app_plan_id: The app plan id to create the webapp in.
        database_server: The database server to whitelist the webapp outbound ips.
        database: The database to connect the webapp to.
        database_user_password: The password for the database user.
        app_insights_connection_string: The connection string for application insights.
        logging_connection_string: The connection string for central logging.
        usage_key: The private key for the usage function.
        status_key: The private key for the status function.
        controller_key: The private key for the controller function.

    Returns:
        The webapp.
    """
    active_directory_args = [
        web.NameValuePairArgs(name="TENANT_ID", value=AD_TENANT_ID),
        web.NameValuePairArgs(name="CLIENT_ID", value=AD_API_CLIENT_ID),
        web.NameValuePairArgs(name="CLIENT_SECRET", value=AD_API_CLIENT_SECRET),
    ]

    web_args = [
        web.NameValuePairArgs(
            name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"
        ),
        web.NameValuePairArgs(name="WEBSITES_PORT", value="80"),
        web.NameValuePairArgs(name="WEBSITE_HTTPLOGGING_RETENTION_DAYS", value="30"),
        web.NameValuePairArgs(name="FORWARDED_ALLOW_IPS", value="*"),
        web.NameValuePairArgs(
            name="DOCKER_REGISTRY_SERVER_URL",
            value=DOCKER_REGISTRY_SERVER_URL,
        ),
        web.NameValuePairArgs(
            name="DOCKER_REGISTRY_SERVER_USERNAME",
            value=DOCKER_REGISTRY_SERVER_USERNAME,
        ),
        web.NameValuePairArgs(
            name="DOCKER_REGISTRY_SERVER_PASSWORD",
            value=DOCKER_REGISTRY_SERVER_PASSWORD,
        ),
        web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value=AUTO_DEPLOY),
        web.NameValuePairArgs(
            name="CENTRAL_LOGGING_CONNECTION_STRING",
            value=logging_connection_string,
        ),
        web.NameValuePairArgs(
            name="APPLICATIONINSIGHTS_CONNECTION_STRING",
            value=app_insights_connection_string,
        ),
        web.NameValuePairArgs(name="ORGANISATION", value=ORGANISATION),
    ]

    fully_qualified_domain_name = database_server.fully_qualified_domain_name.apply(
        raise_if_none
    )
    database_connection_args = [
        web.NameValuePairArgs(name="APP_MODULE", value=APP_MODULE),
        web.NameValuePairArgs(name="TIMEOUT", value="300"),
        web.NameValuePairArgs(name="DB_HOST", value=fully_qualified_domain_name),
        web.NameValuePairArgs(name="DB_NAME", value=database.name),
        web.NameValuePairArgs(name="DB_USER", value=RCTAB_APP_USER),
        web.NameValuePairArgs(name="DB_PASSWORD", value=database_user_password.result),
        web.NameValuePairArgs(name="SSL_REQUIRED", value="true"),
    ]

    additional_settings = [
        web.NameValuePairArgs(name=item[0], value=item[1])
        for item in (
            ["SENDGRID_API_KEY", SENDGRID_API_KEY],
            ["SENDGRID_SENDER_EMAIL", SENDGRID_SENDER_EMAIL],
            ["EXPIRY_EMAIL_FREQ", EXPIRY_EMAIL_FREQ],
            ["NOTIFIABLE_ROLES", NOTIFIABLE_ROLES],
            ["ROLES_FILTER", ROLES_FILTER],
            ["ADMIN_EMAIL_RECIPIENTS", ADMIN_EMAIL_RECIPIENTS],
            ["IGNORE_WHITELIST", IGNORE_WHITELIST],
            ["WHITELIST", WHITELIST],
            ["LOG_LEVEL", LOG_LEVEL],
        )
        if item[1]
    ]

    session_cookie_secret = random.RandomPassword(
        "session_cookie_secret",
        random.RandomPasswordArgs(
            length=25,
            special=True,
            override_special="_%@",
        ),
        opts=ResourceOptions(additional_secret_outputs=["result"]),
    )

    keyvault.Secret(
        "session_cookie_secret",
        keyvault.SecretArgs(
            properties=keyvault.SecretPropertiesArgs(
                value=session_cookie_secret.result,
            ),
            resource_group_name=resource_group.name,
            secret_name="session-cookie-secret",
            vault_name=vault.name,
        ),
    )

    session_cookie_args = [
        web.NameValuePairArgs(
            name="SESSION_EXPIRE_TIME_MINUTES", value=SESSION_TIMEOUT_MINUTES
        ),
        web.NameValuePairArgs(
            name="SESSION_SECRET",
            value=session_cookie_secret.result,
        ),
    ]

    public_key_args = [
        web.NameValuePairArgs(
            name="USAGE_FUNC_PUBLIC_KEY",
            value=usage_key.public_key_openssh,
        ),
        web.NameValuePairArgs(
            name="STATUS_FUNC_PUBLIC_KEY",
            value=status_key.public_key_openssh,
        ),
        web.NameValuePairArgs(
            name="CONTROLLER_FUNC_PUBLIC_KEY",
            value=controller_key.public_key_openssh,
        ),
    ]

    # Concat all settings
    app_settings = (
        active_directory_args
        + web_args
        + session_cookie_args
        + database_connection_args
        + public_key_args
        + additional_settings
    )

    web_app = web.WebApp(
        f"rctab-api-{IDENTIFIER}",
        web.WebAppArgs(
            name=f"rctab-{IDENTIFIER}",
            resource_group_name=resource_group.name,
            location=resource_group.location,
            server_farm_id=app_plan_id,
            site_config=web.SiteConfigArgs(
                app_settings=app_settings,
                always_on=True,
                linux_fx_version=f"DOCKER|{DOCKER_API_IMAGE}",
            ),
            https_only=True,
        ),
    )

    # Add the webapps outbound ips to the database whitelist
    web_app.possible_outbound_ip_addresses.apply(
        lambda x: [
            dbforpostgresql.FirewallRule(
                f"firewallRule_outbound_{i}",
                dbforpostgresql.FirewallRuleArgs(
                    start_ip_address=ip,
                    end_ip_address=ip,
                    firewall_rule_name=f"outbound_{i}",
                    resource_group_name=resource_group.name,
                    server_name=database_server.name,
                ),
            )
            for i, ip in enumerate(x.split(","))
        ]
    )

    return web_app
