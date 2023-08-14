"""Function app infrastructure code."""
from typing import Tuple, Union

import pulumi
from pulumi import Output
from pulumi_azure_native import resources, storage, web
from pulumi_azure_native.insights import (
    MetricAlert,
    MetricAlertActionArgs,
    MetricAlertMultipleResourceMultipleMetricCriteriaArgs,
    MetricCriteriaArgs,
)
from pulumi_azure_native.insights.v20200202 import Component, ComponentArgs
from pulumi_azure_native.resources import ResourceGroup
from pulumi_tls import PrivateKey

from constants import (
    AD_STATUS_CLIENT_ID,
    AD_STATUS_CLIENT_SECRET,
    AD_TENANT_ID,
    AUTO_DEPLOY,
    BILLING_OR_MGMT,
    DOCKER_CONTROLLER_IMAGE,
    DOCKER_REGISTRY_SERVER_PASSWORD,
    DOCKER_REGISTRY_SERVER_URL,
    DOCKER_REGISTRY_SERVER_USERNAME,
    DOCKER_STATUS_IMAGE,
    DOCKER_USAGE_IMAGE,
    IDENTIFIER,
)

# pylint: disable=too-many-arguments


def create_alert_rule(
    first_letter: str,
    insights_id: Output[str],
    resource_group: ResourceGroup,
    action_group_id: Output[str],
) -> None:
    """Alert the admin group if more than 2 failures occur in a 5-minute period.

    Args:
        first_letter: The first letter of the function app name.
        insights_id: The id of the app insights instance.
        resource_group: The resource group to create the alert in.
        action_group_id: The id of the action group to email.

    Returns:
        None
    """
    MetricAlert(
        f"{first_letter}-function-failure-alert",
        actions=[
            MetricAlertActionArgs(
                action_group_id=action_group_id,
            )
        ],
        auto_mitigate=True,
        criteria=MetricAlertMultipleResourceMultipleMetricCriteriaArgs(
            all_of=[
                MetricCriteriaArgs(
                    criterion_type="StaticThresholdCriterion",
                    metric_name="requests/failed",
                    threshold=5,
                    metric_namespace="microsoft.insights/components",
                    name=f"{first_letter}-function-failed-requests",
                    operator="GreaterThan",
                    time_aggregation="Count",
                )
            ],
            odata_type="Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria",
        ),
        description=f"Failure alert for {first_letter}-function",
        enabled=True,
        evaluation_frequency="PT1H",
        location="global",
        resource_group_name=resource_group.name,
        rule_name=f"{first_letter}-function-failure",
        scopes=[
            insights_id,
        ],
        severity=1,
        tags={},
        target_resource_region=resource_group.location,
        target_resource_type="microsoft.insights/components",
        window_size="PT6H",
    )


def create_function_app(
    resource_group: ResourceGroup,
    app_plan_id: Output[str],
    app_hostname: Output[str],
    image_name: str,
    workspace_id: Output[str],
    logging_connection_string: Output[str],
    app_settings: Tuple[
        Union[web.NameValuePairArgs, Output[web.NameValuePairArgs]], ...
    ],
    storage_connection_string: Output[str],
    identity_type: web.ManagedServiceIdentityType,
    action_group_id: Output[str],
):
    """Create a function app to run the docker image given by image_name.

    Args:
        resource_group: The resource group to create the function app in.
        app_plan_id: The id of the app service plan to use.
        app_hostname: The hostname of the app service plan to use.
        image_name: The name of the docker image to run.
        workspace_id: The id of the app insights instance to use.
        logging_connection_string: The connection string for application insights.
        app_settings: The app settings to use.
        storage_connection_string: The connection string for the storage account to use.
        identity_type: The type of identity to use.
        action_group_id: The id of the action group to email.

    Returns:
        None
    """
    # presume that the image name is something like
    # hub.docker.io/myorg/rctab-usage:latest
    # but could be as short as "rctab-usage" and,
    # for brevity, we only want "u"
    first_letter = image_name.split("/")[-1].split("-")[-1][0]

    app_insights = Component(
        f"{first_letter}-function-{IDENTIFIER}-",
        ComponentArgs(
            resource_group_name=resource_group.name,
            location=resource_group.location,
            application_type="functionapp",
            kind="web",
            request_source="rest",
            workspace_resource_id=workspace_id,
        ),
    )

    function_app = web.WebApp(
        f"{first_letter}-function-{IDENTIFIER}-",
        web.WebAppArgs(
            identity=web.ManagedServiceIdentityArgs(type=identity_type),
            resource_group_name=resource_group.name,
            location=resource_group.location,
            kind="functionapp",
            server_farm_id=app_plan_id,
            site_config=web.SiteConfigArgs(
                app_settings=(
                    web.NameValuePairArgs(
                        name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"
                    ),
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
                    web.NameValuePairArgs(name="WEBSITES_PORT", value="80"),
                    web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value=AUTO_DEPLOY),
                    web.NameValuePairArgs(
                        name="CENTRAL_LOGGING_CONNECTION_STRING",
                        value=logging_connection_string,
                    ),
                    web.NameValuePairArgs(
                        name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                        value=app_insights.connection_string,
                    ),
                    web.NameValuePairArgs(
                        name="FUNCTIONS_EXTENSION_VERSION",
                        value="~4",
                    ),
                    web.NameValuePairArgs(
                        name="AzureWebJobsStorage",
                        value=storage_connection_string,
                    ),
                    web.NameValuePairArgs(
                        name="API_URL",
                        value=app_hostname,
                    ),
                )
                + app_settings,
                always_on=True,
                linux_fx_version=f"DOCKER|{image_name}",
            ),
            https_only=True,
        ),
    )

    create_alert_rule(first_letter, app_insights.id, resource_group, action_group_id)

    pulumi.export(
        f"getStartedEndpoint-{image_name}",
        function_app.default_host_name.apply(
            lambda default_host_name: f"https://{default_host_name}"
        ),
    )


def set_up_function_apps(
    workspace_id: Output[str],
    logging_connection_string: Output[str],
    app_plan_id: Output[str],
    app_hostname: Output[str],
    usage_key: PrivateKey,
    status_key: PrivateKey,
    controller_key: PrivateKey,
    action_group_id: Output[str],
) -> None:
    """Set up the function app resources for RCTab.

    Args:
        workspace_id: The id of the log analytics workspace to use.
        logging_connection_string: The connection string for the centralised logging.
        app_plan_id: The id of the app service plan to use.
        app_hostname: The hostname of the web app.
        usage_key: The private key to use for the usage function app.
        status_key: The private key to use for the status function app.
        controller_key: The private key to use for the controller function app.
        action_group_id: The id of the action group to email.

    Returns:
        None
    """
    resource_group = resources.ResourceGroup(
        f"rctab-mngmnt-functions-{IDENTIFIER}-",
        resources.ResourceGroupArgs(
            location="UK South",
        ),
    )

    account = storage.StorageAccount(
        "store" + "".join(char for char in IDENTIFIER if char.isalpha()).lower(),
        storage.StorageAccountArgs(
            resource_group_name=resource_group.name,
            location=resource_group.location,
            sku=storage.SkuArgs(name="Standard_LRS"),
            kind=storage.Kind.STORAGE_V2,
        ),
    )

    primary_key = (
        pulumi.Output.all(resource_group.name, account.name)
        .apply(
            lambda args: storage.list_storage_account_keys(
                resource_group_name=args[0], account_name=args[1]
            )
        )
        .apply(lambda account_keys: account_keys.keys[0].value)
    )

    connection_string = Output.concat(
        "DefaultEndpointsProtocol=https;AccountName=",
        account.name,
        ";AccountKey=",
        primary_key,
        ";EndpointSuffix=core.windows.net",
    )

    for image_name, app_settings, identity_type in zip(
        [DOCKER_USAGE_IMAGE, DOCKER_STATUS_IMAGE, DOCKER_CONTROLLER_IMAGE],
        [
            (
                web.NameValuePairArgs(
                    name="PRIVATE_KEY", value=usage_key.private_key_openssh
                ),
                BILLING_OR_MGMT,
            ),
            (
                web.NameValuePairArgs(
                    name="PRIVATE_KEY", value=status_key.private_key_openssh
                ),
                web.NameValuePairArgs(name="AZURE_TENANT_ID", value=AD_TENANT_ID),
                web.NameValuePairArgs(
                    name="AZURE_CLIENT_ID", value=AD_STATUS_CLIENT_ID
                ),
                web.NameValuePairArgs(
                    name="AZURE_CLIENT_SECRET", value=AD_STATUS_CLIENT_SECRET
                ),
            ),
            (
                web.NameValuePairArgs(
                    name="PRIVATE_KEY", value=controller_key.private_key_openssh
                ),
            ),
        ],
        [
            web.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
            web.ManagedServiceIdentityType.NONE,
            web.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
        ],
    ):
        create_function_app(
            resource_group,
            app_plan_id,
            app_hostname,
            image_name,
            workspace_id,
            logging_connection_string,
            app_settings,
            connection_string,
            identity_type,
            action_group_id,
        )
