"""Key vault infrastructure code."""
from pulumi_azure_native import authorization, keyvault, resources
from pulumi_azure_native.keyvault import SkuName


def create_vault(name: str, resource_group: resources.ResourceGroup) -> keyvault.Vault:
    """
    Create a keyvault in a resource group.

    Args:
        name: The name of the keyvault.
        resource_group: The resource group to create the keyvault in.

    Returns:
        The keyvault.
    """
    context = authorization.get_client_config()
    return keyvault.Vault(
        name,
        keyvault.VaultArgs(
            resource_group_name=resource_group.name,
            location=resource_group.location,
            properties=keyvault.VaultPropertiesArgs(
                enabled_for_deployment=True,
                enabled_for_disk_encryption=True,
                enabled_for_template_deployment=True,
                sku=keyvault.SkuArgs(
                    family="A",
                    name=SkuName.STANDARD,
                ),
                tenant_id=context.tenant_id,
                access_policies=[
                    keyvault.AccessPolicyEntryArgs(
                        object_id=context.object_id,
                        permissions=keyvault.PermissionsArgs(
                            certificates=[
                                "get",
                                "list",
                                "delete",
                                "create",
                                "import",
                                "update",
                                "managecontacts",
                                "getissuers",
                                "listissuers",
                                "setissuers",
                                "deleteissuers",
                                "manageissuers",
                                "recover",
                                "purge",
                            ],
                            keys=[
                                "encrypt",
                                "decrypt",
                                "wrapKey",
                                "unwrapKey",
                                "sign",
                                "verify",
                                "get",
                                "list",
                                "create",
                                "update",
                                "import",
                                "delete",
                                "backup",
                                "restore",
                                "recover",
                                "purge",
                            ],
                            secrets=[
                                "get",
                                "list",
                                "set",
                                "delete",
                                "backup",
                                "restore",
                                "recover",
                                "purge",
                            ],
                        ),
                        tenant_id=context.tenant_id,
                    )
                ],
            ),
        ),
    )
