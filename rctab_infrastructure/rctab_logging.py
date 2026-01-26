"""Logging workspace infrastructure code."""

from typing import Optional, Sequence, Tuple

from pulumi import Output
from pulumi_azure_native import operationalinsights, resources
from pulumi_azure_native.applicationinsights import Component
from pulumi_azure_native.monitor import (
    ActionGroup,
    ActionGroupInitArgs,
    EmailReceiverArgs,
)

from rctab_infrastructure.constants import ADMIN_EMAIL_RECIPIENTS, IDENTIFIER


def set_up_logging() -> Tuple[Output[str], Output[str], resources.ResourceGroup]:
    """Set up the centralised logging resources for RCTab.

    Includes a workspace and an app insights instance, all housed in a single
    resource group.

    Returns:
        The id of the log analytics workspace to use, the centralised logging
        connection string and the resource group.
    """
    logging_resource_group = resources.ResourceGroup(
        f"rctab-central-logging-{IDENTIFIER}-",
    )

    workspace = operationalinsights.Workspace(
        f"rctab-workspace-{IDENTIFIER}-",
        location=logging_resource_group.location,
        resource_group_name=logging_resource_group.name,
        sku=operationalinsights.WorkspaceSkuArgs(
            name="PerGB2018",
        ),
    )

    logging_app_insights = Component(
        f"rctab-logging-{IDENTIFIER}-",
        resource_group_name=logging_resource_group.name,
        location=logging_resource_group.location,
        application_type="functionapp",
        kind="web",
        request_source="rest",
        workspace_resource_id=workspace.id,
    )

    return workspace.id, logging_app_insights.connection_string, logging_resource_group


def create_action_group(logging_resource_group_name: Output[str]) -> Output[str]:
    """Create an action group of administrators to email.

    Action group members are specified in the config variable ADMIN_EMAIL_RECIPIENTS.

    Args:
        logging_resource_group_name: The name of the logging resource group.

    Returns:
        The id of the action group.
    """
    email_receivers: Optional[Output[Sequence[EmailReceiverArgs]]]

    if ADMIN_EMAIL_RECIPIENTS is not None:
        email_receivers = ADMIN_EMAIL_RECIPIENTS.apply(
            lambda x: [
                EmailReceiverArgs(
                    email_address=split_x.strip(),
                    name=split_x.split("@")[0].strip(),
                    use_common_alert_schema=False,
                )
                for split_x in x.translate(str.maketrans("", "", '[]"')).split(",")
            ]
        )
    else:
        email_receivers = None

    action_group = ActionGroup(
        "RCTab-Admin-Action-Group",
        ActionGroupInitArgs(
            action_group_name="RCTab-Admin-Action-Group",
            email_receivers=email_receivers,
            enabled=True,
            group_short_name="RCTab-AAG",
            location="Global",
            resource_group_name=logging_resource_group_name,
            tags={},
        ),
    )

    return action_group.id
