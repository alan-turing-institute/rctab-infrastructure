"""Database infrastructure code."""
from typing import Final, Tuple

import pulumi
import pulumi_azure_native.dbforpostgresql.v20230301preview as dbforpostgresql
import pulumi_random as random
from pulumi import ResourceOptions
from pulumi_azure_native import authorization, keyvault, resources
from pulumi_postgresql import Grant, GrantArgs, Provider, ProviderArgs, Role, RoleArgs

from constants import AD_SERVER_ADMIN, DB_ROOT_CERT_PATH, IDENTIFIER, RCTAB_APP_USER
from utils import raise_if_none

SERVER_VERSION: Final[
    dbforpostgresql.ServerVersion
] = dbforpostgresql.ServerVersion.SERVER_VERSION_14

# pylint: disable=too-many-arguments


def create_database_server(
    name: str,
    admin_username: str,
    resource_group: resources.ResourceGroup,
    vault: keyvault.Vault,
    db_sku_name: str,
    db_sku_tier: str,
) -> Tuple[dbforpostgresql.Server, random.RandomPassword]:
    """
    Create a database server.

    Creates an admin password and stores in a keyvault and adds a user as an
    active directory administrator.

    Args:
        name: The name of the database server.
        admin_username: The username of the database server admin.
        resource_group: The resource group to create the database server in.
        vault: The keyvault to store the admin password in.
        db_sku_name: The name of the database sku to use.
        db_sku_tier: The tier of the database sku to use.

    Returns:
        A tuple containing the database server and the admin password.
    """
    context = authorization.get_client_config()

    # Create admin Credentials and place in keyvault
    admin_password = random.RandomPassword(
        "db-password",
        random.RandomPasswordArgs(
            length=16,
            special=False,
        ),
        opts=ResourceOptions(additional_secret_outputs=["result"]),
    )

    keyvault.Secret(
        "db_password",
        keyvault.SecretArgs(
            properties=keyvault.SecretPropertiesArgs(
                value=admin_password.result,
            ),
            resource_group_name=resource_group.name,
            secret_name="db-admin-pass",
            vault_name=vault.name,
        ),
    )

    # Add Database Server
    server_name = f"{IDENTIFIER}-rctab-".lower()
    # Add random string to end of server name to prevent ServerGroupDropping
    # error on rebuild
    random_code = random.RandomString(
        "random_string", length=4, special=False, upper=False
    )
    server_name_with_random_code = pulumi.Output.concat(server_name, random_code.result)
    server = dbforpostgresql.Server(
        f"{name}{IDENTIFIER}-",
        dbforpostgresql.ServerArgs(
            resource_group_name=resource_group.name,
            location=resource_group.location,
            create_mode="Default",
            server_name=server_name_with_random_code,
            version=SERVER_VERSION,
            administrator_login=admin_username,
            administrator_login_password=admin_password.result,
            auth_config=dbforpostgresql.AuthConfigArgs(active_directory_auth="Enabled"),
            storage=dbforpostgresql.StorageArgs(storage_size_gb=128),
            sku=dbforpostgresql.SkuArgs(
                name=db_sku_name,
                tier=db_sku_tier,
            ),
        ),
    )

    # Set an AAD administrator
    dbforpostgresql.Administrator(
        "serverAdministrator",
        dbforpostgresql.AdministratorArgs(
            principal_type="User",
            principal_name=AD_SERVER_ADMIN,
            resource_group_name=resource_group.name,
            server_name=server.name,
            object_id=context.object_id,
            tenant_id=context.tenant_id,
        ),
    )

    return server, admin_password


def create_database_user(
    database_server: dbforpostgresql.Server,
    database: dbforpostgresql.Database,
    admin_password: random.RandomPassword,
) -> random.RandomPassword:
    """
    Create a user on the database specified and return their password.

    Args:
        database_server: The database server to create the user on.
        database: The database to create the user on.
        admin_password: The password of the database server admin.

    Returns:
        The password of the user created.
    """
    admin_login = database_server.administrator_login.apply(raise_if_none)
    fully_qualified_domain_name = database_server.fully_qualified_domain_name.apply(
        raise_if_none
    )

    # Create new user creds - not stored in database
    new_user_password = random.RandomPassword(
        "new-user-passwords",
        random.RandomPasswordArgs(
            length=16,
            special=False,
        ),
        opts=ResourceOptions(additional_secret_outputs=["result"]),
    )

    postgres_provider = Provider(
        "database_config_provider",
        ProviderArgs(
            database=database.name,
            host=fully_qualified_domain_name,
            password=admin_password.result,
            port=5432,
            sslmode="verify-full",
            sslrootcert=DB_ROOT_CERT_PATH,
            superuser=False,
            username=admin_login,
            expected_version=SERVER_VERSION,
        ),
    )

    new_user = Role(
        RCTAB_APP_USER,
        RoleArgs(
            login=True,
            name=RCTAB_APP_USER,
            password=new_user_password.result,
            create_database=True,
            skip_drop_role=True,
            skip_reassign_owned=True,
        ),
        opts=pulumi.ResourceOptions(provider=postgres_provider),
    )

    Grant(
        "create_schema_grant_user",
        GrantArgs(
            database=database.name,
            role=new_user.name,
            object_type="database",
            privileges=["CREATE"],
        ),
        opts=pulumi.ResourceOptions(provider=postgres_provider),
    )

    return new_user_password
