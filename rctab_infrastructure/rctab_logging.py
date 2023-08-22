"""Logging workspace infrastructure code."""
from typing import Sequence, Tuple

from pulumi import Output
from pulumi_azure_native import operationalinsights, resources
from pulumi_azure_native.insights import ActionGroup, EmailReceiverArgs
from pulumi_azure_native.insights.v20200202 import Component

from rctab_infrastructure.constants import ADMIN_EMAIL_RECIPIENTS, IDENTIFIER


def set_up_logging() -> Tuple[Output[str], Output[str], resources.ResourceGroup]:
    """Set up the centralised logging resources for RCTab."""
    logging_resource_group = resources.ResourceGroup(
        f"rctab-central-logging-{IDENTIFIER}-",
        location="UK South",
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


def create_action_group(logging_resource_group_name: str) -> Output[str]:
    """Create an administration action group."""
    if ADMIN_EMAIL_RECIPIENTS:
        email_receivers: Output[
            Sequence[EmailReceiverArgs]
        ] | None = ADMIN_EMAIL_RECIPIENTS.apply(
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
        action_group_name="RCTab-Admin-Action-Group",
        email_receivers=email_receivers,
        enabled=True,
        group_short_name="RCTab-AAG",
        location="Global",
        resource_group_name=logging_resource_group_name,
        tags={},
    )

    return action_group.id
