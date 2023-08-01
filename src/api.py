"""Infrastructure code to make a web app with a database."""
from typing import Tuple

import pulumi_azure_native.dbforpostgresql.v20230301preview as dbforpostgresql
from pulumi import Output, ResourceOptions
from pulumi_azure_native import resources, web
from pulumi_azure_native.insights import (
    MetricAlert,
    MetricAlertActionArgs,
    MetricAlertMultipleResourceMultipleMetricCriteriaArgs,
    MetricCriteriaArgs,
)
from pulumi_azure_native.insights.v20200202 import Component, ComponentArgs
from pulumi_tls import PrivateKey

from constants import DATABASE_NAME, IDENTIFIER, PRIMARY_IP
from database import create_database_server, create_database_user
from keyvault import create_vault
from webapp import create_webapp

# pylint: disable=too-many-arguments


def create_availability_alert_rule(
    insights_id: Output[str],
    resource_group: resources.ResourceGroup,
    action_group_id: Output[str],
) -> None:
    """
    Alert to email admin if API availability drops bellow 100%.

    Args:
        insights_id: The id of the application insights resource.
        resource_group: The resource group to create the alert in.
        action_group_id: The id of the action group to email.

    Returns:
        None
    """
    MetricAlert(
        "API-availability-alert",
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
                    metric_name="availabilityResults/availabilityPercentage",
                    threshold=100,
                    metric_namespace="microsoft.insights/components",
                    name="API-availability-alert",
                    operator="LessThan",
                    time_aggregation="Average",
                )
            ],
            odata_type="Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
        ),
        description="Failure alert for API having less than 100%% availability",
        enabled=True,
        evaluation_frequency="PT1M",
        location="global",
        resource_group_name=resource_group.name,
        rule_name="API-availability-alert",
        scopes=[
            insights_id,
        ],
        severity=2,
        tags={},
        target_resource_region=resource_group.location,
        target_resource_type="microsoft.insights/components",
        window_size="PT5M",
    )


def set_up_api(
    workspace_id: Output[str],
    logging_connection_string: Output[str],
    usage_key: PrivateKey,
    status_key: PrivateKey,
    controller_key: PrivateKey,
    action_group_id: Output[str],
) -> Tuple[Output[str], Output[str]]:
    """
    Create resources for the RCTab API.

    Args:
        workspace_id: The id of the application insights workspace.
        logging_connection_string: The connection string for the logging database.
        usage_key: The private key for the usage database.
        status_key: The private key for the status database.
        controller_key: The private key for the controller database.
        action_group_id: The id of the action group to email.

    Returns:
        A tuple containing the app plan id and the url of the webapp.
    """
    api_resource_group = resources.ResourceGroup(
        f"rctab-{IDENTIFIER}-",
        resources.ResourceGroupArgs(location="UK South"),
    )

    # Dedicated plan (not based on usage)
    app_plan = web.AppServicePlan(
        # Dedicated plan (not based on usage)
        f"rctab-app-plan-{IDENTIFIER}-",
        web.AppServicePlanArgs(
            location=api_resource_group.location,
            resource_group_name=api_resource_group.name,
            kind="Linux",
            reserved=True,
            sku=web.SkuDescriptionArgs(tier="Premium", name="P1v2"),
        ),
    )

    app_insights = Component(
        f"rctab-{IDENTIFIER}-",
        ComponentArgs(
            resource_group_name=api_resource_group.name,
            location=api_resource_group.location,
            application_type="webapp",
            kind="web",
            request_source="rest",
            workspace_resource_id=workspace_id,
        ),
    )

    create_availability_alert_rule(app_insights.id, api_resource_group, action_group_id)

    vault = create_vault(f"{IDENTIFIER}-vlt", api_resource_group)

    db_server, db_admin_password = create_database_server(
        "rctab-database-",
        admin_username="rctabadmin",
        resource_group=api_resource_group,
        vault=vault,
        db_sku_name="Standard_D4ds_v4",
        db_sku_tier=dbforpostgresql.SkuTier.GENERAL_PURPOSE,
    )

    database = dbforpostgresql.Database(
        f"{DATABASE_NAME}-{IDENTIFIER}-",
        dbforpostgresql.DatabaseArgs(
            database_name=DATABASE_NAME,
            resource_group_name=api_resource_group.name,
            server_name=db_server.name,
        ),
    )

    dbforpostgresql.FirewallRule(
        "access_ip",
        dbforpostgresql.FirewallRuleArgs(
            start_ip_address=PRIMARY_IP,
            end_ip_address=PRIMARY_IP,
            firewall_rule_name="access_ip",
            resource_group_name=api_resource_group.name,
            server_name=db_server.name,
        ),
        # This is a hack because adding the firewall too soon errors
        opts=ResourceOptions(depends_on=database),
    )

    # Add a database user for the RCTab API
    rctab_app_password = create_database_user(
        database_server=db_server,
        database=database,
        admin_password=db_admin_password,
    )

    webapp = create_webapp(
        resource_group=api_resource_group,
        vault=vault,
        app_plan_id=app_plan.id,
        database_server=db_server,
        database=database,
        logging_connection_string=logging_connection_string,
        database_user_password=rctab_app_password,
        app_insights_connection_string=app_insights.connection_string,
        usage_key=usage_key,
        status_key=status_key,
        controller_key=controller_key,
    )

    return app_plan.id, webapp.default_host_name.apply(lambda x: f"https://{x}")
