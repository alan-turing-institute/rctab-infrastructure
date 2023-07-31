"""Pulumi script for creating a Function App (and dependencies) on Azure."""
from pulumi_tls import PrivateKey, PrivateKeyArgs

from api import set_up_api
from function_apps import set_up_function_apps
from rctab_logging import create_action_group, set_up_logging

# Create central logging and workspace
workspace_id, logging_connection_string, logging_resouce_group = set_up_logging()
action_group_id = create_action_group(logging_resouce_group.name)

usage_key, status_key, controller_key = [
    PrivateKey(
        f"{x}-app-key",
        PrivateKeyArgs(
            algorithm="RSA",
            # "Generally, 3072 bits is considered sufficient."
            # See `man ssh-keygen`
            rsa_bits=3072,
        ),
    )
    for x in ("usage", "status", "controller")
]

# Create API webapp
app_plan_id, app_hostname = set_up_api(
    workspace_id,
    logging_connection_string,
    usage_key,
    status_key,
    controller_key,
    action_group_id,
)

# Create function apps
set_up_function_apps(
    workspace_id,
    logging_connection_string,
    app_plan_id,
    app_hostname,
    usage_key,
    status_key,
    controller_key,
    action_group_id,
)
