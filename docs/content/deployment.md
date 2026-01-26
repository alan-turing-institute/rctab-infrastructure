# Deployment

## Quick Start Steps

1. Clone this repository and install the Python package with either `pip install .` or `poetry install`.
2. Install the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) and login with `az login`.
3. Set the desired subscription with `az account set --subscription '<subscription-name-or-id>'`.
4. Create a service principal for the Status function to use.
   See the Status function [docs](https://rctab-functions.readthedocs.io/en/latest/content/status.html#creating-a-service-principal-with-graph-permissions).
5. Install [Pulumi](https://www.pulumi.com/), set up an account and login.
6. Set the [Configuration Variables](#configuration-variables).
7. Run `pulumi up`.
8. Complete the [Post Pulumi Deployment](#post-pulumi-deployment) steps.

You can take down the instance with `pulumi down --continue-on-error`.

## Configuration Variables

The resources required for RCTab are built by running `pulumi up` in the root directory of this repository.
Before you can run this, however, you are required to set a number of config variables.
These variables allow Azure to run the application and configure your instance of RCTab.
Some of these are stored as environment variables in the functions' and webapp's [configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-common?tabs=portal).

If you are testing/developing RCTab, it may be sufficient to use the [Example Minimal Configuration](#example-minimal-configuration) below.

**Note**, whilst it is possible to edit these configurations directly on Azure, if a future update is made to the RCTab infrastructure, and you run `pulumi up` again, these config variables will be **overwritten** or **deleted** from Azure and reset to the value specified in the Pulumi config.

### Required Configuration Variables

#### Stack Name

```shell
pulumi stack init <stack-name>
```

The stack name isn't actually a configuration variable (it is the name of the [Pulumi stack](https://www.pulumi.com/docs/concepts/stack/)) but is used to form some of the resource names for RCTab.
This imposes some restrictions on what you can call your stack.
You will be notified, when you run `pulumi up` or `pulumi preview`, if your stack name is too long or otherwise invalid.

> **Warning**
Do not change the stack name or org ticker after deployment.
The stack name and org ticker are used to form the name of the database server.
If you change the stack name (e.g. with `pulumi stack rename`) after deployment, Pulumi will drop and recreate the database server but will not know to recreate the database user, leaving you with a broken deployment.

#### Location

The location specifies the [location of resources on Azure](https://azure.microsoft.com/en-gb/explore/global-infrastructure/geographies/#overview).

```shell
pulumi config set azure-native:location '<azure-location>'
```

#### Organisation

```shell
pulumi config set organisation '<organisation>'
```

Organisation specifies the name of your organisation and is used on the API frontend.
For example, if your organisation is 'The University of Research Software', you would set this as the organisation name (including the 'The').
There are no restrictions of the length or characters for this.

#### Ticker

```shell
pulumi config set ticker '<ticker>'
```

Ticker is an identifier of your organisation that is between 2 and 6 characters in length.
This is used in the globally unique resource names on Azure to ensure your resources are easily linked to your organisation.
The inspiration for the ticker is the [stock ticker](https://www.investopedia.com/terms/s/stocksymbol.asp).

The ticker is combined with the stack name to provide globally unique resource names associated with a particular stack (_e.g._ prod, dev, main, _etc._).
One example is the domain of the api, which takes the form `rctab-{ticker}-{stack}.azurewebsites.net`.
The total length of these two constants must not be larger than 10 characters.

> **Warning**
Do not change the stack name or org ticker after deployment.
The stack name and org ticker are used to form the name of the database server.
If you change either after deployment, Pulumi will drop and recreate the database server but will not know to recreate the database user, leaving you with a broken deployment.

#### Primary IP

```shell
pulumi config set --secret primary_ip_address '<primary_ip_address>'
```

The Primary IP is the IP address from which people from within your organisation can access your instance of RCTab.
During deployment, we only allow a single IP address to be set (such as the public, static IP for your organisation's VPN).
Additional IP addresses can be specified within the Azure portal.

#### DB Root Cert Path

```shell
pulumi config set --secret db_root_cert_path '<path/to/x509.crt.pem>'
```

RCTab uses an Azure Database for PostgreSQL Flexible Server, which requires a copy of a trusted Certificate Authority (CA) certificate file to connect securely.
You will need to download the Microsoft RSA Root Certificate Authority 2017 certificate and convert it to PEM format:

1. You can download it using the `crt` link on <https://www.microsoft.com/pkiops/docs/repository.html>.
2. You should verify that the hash generated with the shasum command (e.g. `shasum -a 1 /path/to/your/downloaded/file.crt`) matches that shown on the webpage.
3. You can convert the `.crt` file to a `.pem` with `openssl x509 -inform DER -outform PEM -in /path/to/your/downloaded/file.crt -out x509.crt.pem`.

#### Active Directory Server Admin

```shell
pulumi config set --secret ad_server_admin '<ad-server-admin>'
```

A user, group or service principal who will be able to create or enable users for Azure AD-based authentication.
See [these](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-configure-sign-in-azure-ad-authentication) "Azure Database for PostgreSQL - Flexible Server" docs for more.

#### Active Directory Tenant ID

```shell
pulumi config set --secret ad_tenant_id '<ad-tenant-id>'
```

The Active Directory tenant ID is unique to your organisation and is a series of unique letters and numbers which identify your Azure Active Directory Tenant globally.
It is used for the authentication and resource management of RCTab.
Checkout [this guide](https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/how-to-find-tenant) for how to find the tenant ID for your organisation.

#### Active Directory Client ID and Client Secret

The client ID and client secret are credentials used by applications on Azure to authenticate and access resources protected by Azure AD, using Azure Active Directory and [OAuth 2.0 authentication](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow).
It allows a service to use its own credentials to gain access, rather than share a users credentials.

RCTab requires that the API and Status function are able to identify themselves in this way.

#### API

You will need to follow the API instructions for [application registration](https://rctab-api.readthedocs.io/en/latest/content/setup.html#application-registration).

```shell
pulumi config set --secret ad_api_client_id '<ad-api-client-id>'
pulumi config set --secret ad_api_client_secret '<ad-api-client-secret>'
```

#### Status Function

Ensure you have first followed the Status function [service principal setup instructions](https://rctab-functions.readthedocs.io/en/latest/content/status.html#creating-a-service-principal-with-graph-permissions).

```shell
pulumi config set --secret ad_status_client_id '<ad-status-client-id>'
pulumi config set --secret ad_status_client_secret '<ad-status-client-secret>'
```

#### Usage Management Group

```shell
pulumi config set usage_mgmt_group '<mgmt-group-id>'
```

The ID of the management group that the Usage function app will collect data for.
The Usage function app should have enough permissions over this management group to be able to collect billing data.

### Example Minimal Configuration

An example minimal configuration is provided below.
It should pass any local validity checks but is not intended to be used for production.
You will need to replace the IP address with your own and provide a valid path to the certificate file.

```shell
pulumi stack init 'dev'
pulumi config set azure-native:location 'UkSouth'
pulumi config set organisation 'My Organisation'
pulumi config set ticker 'myorg'
pulumi config set --secret primary_ip_address '123.123.123.123'  # Replace
pulumi config set --secret db_root_cert_path '/home/me/DigiCertGlobalRootCA.crt.pem' # Replace
pulumi config set --secret ad_server_admin 'me@my.org'
pulumi config set --secret ad_tenant_id '00000000-0000-0000-0000-000000000000'
pulumi config set --secret ad_api_client_id '00000000-0000-0000-0000-000000000001'
pulumi config set --secret ad_api_client_secret 'the-api-secret'
pulumi config set --secret ad_status_client_id '00000000-0000-0000-0000-000000000002'
pulumi config set --secret ad_status_client_secret 'the-status-secret'
pulumi config set --secret usage_mgmt_group 'my-management-group'
```

### Optional Config Variables

The following config variables are not required for RCTab deployment.
They come with default options specified, but you can overwrite these to provide your own values should you want to.

#### Notifiable Roles

```shell
pulumi config set notifiable_roles '<role1>, <role2>'
```

Notifiable Roles are the roles which will receive email notifications about a subscription.
These should be provided as a comma delimited list in quotes (_e.g._ 'Contributor, Reader').

For defaults, see the API [settings.py](https://github.com/alan-turing-institute/rctab-api/blob/main/rctab/settings.py) file.

#### Roles Filter

```shell
pulumi config set roles_filter '<role1, role2>'
```

Roles filter specifies what role changes should other members be notified of.
For example, if this is set to "Contributor", Notifiable Role users will be emailed when another "Contributor" is added or removed from the subscription's RBAC list.

For defaults, see the API [settings.py](https://github.com/alan-turing-institute/rctab-api/blob/main/rctab/settings.py) file.

#### Admin Email Recipients

```shell
pulumi config set admin_email_recipients '<email-address1>, <email-address2>'
```

Admin email recipients specifies a list of emails to notify about admin alerts relating to the running of RCTab.

By default, nobody will receive the emails.

#### Expiry Email Frequency

```shell
pulumi config set expiry_email_freq '<day1>, <day2>,...,<dayn>'
```

Frequency in which the email recipients receive notification of subscription expiry. Specified as a list of days (integers). Each specified day signifies the number of days before the subscription expires (e.g., 21 indicates to send an email 21 days before a subscription expiry).

By default, the frequency is set as '1, 7, 30', which translates to sending an email 1 day, 7 days, and 30 days before a subscription expires.

#### Whitelist

```shell
pulumi config set whitelist '<subscription1-uuid>, <subscription2-uuid>'
```

By default, RCTab will only manage whitelisted subscriptions.
To list the subscriptions that RCTab should manage, set the whitelist as a comma-delimited list of subscription UUIDs.

```shell
pulumi config set ignore_whitelist '<true/false>'
```

Alternatively, you can ignore the whitelist all together to manage everything (limited only by the roles assigned to the function apps' identities).

#### SendGrid Variables

RCTab uses [SendGrid](https://docs.sendgrid.com/for-developers/partners/microsoft-azure-2021) to send emails (e.g. status changes, usage alerts and daily summaries).
You will need to set up a SendGrid account and configure an API key that will be set as an environment variable.
You will also need to specify a SendGrid sender email address for the email notifications to be sent from.

```shell
pulumi config set sendgrid_api_key '<sendgrid-api-key>'
pulumi config set sendgrid_sender_email '<sendgrid-sender-email>'
```

#### Log Level

```shell
pulumi config set log_level '<log-level>'
```

Sets the logging level for logs created by RCTab.
Must be one of "CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", or "NOTSET".

For defaults, see the API [settings.py](https://github.com/alan-turing-institute/rctab-api/blob/main/rctab/settings.py) file.

#### Database Server SKU

```shell
pulumi config set db_sku_type 'test'
```

By default, RCTab will use `'prod'` as the SKU type, which deploys a production-ready database server.
For development purposes, you can set the SKU to `test`, which will use a cheaper option with less memory and fewer CPU cores.

### Docker Images

The function apps and API that make up RCTab are deployed from Docker images stored in a public DockerHub repository.
By default, RCTab points at the latest images for the API and function apps.
This is labelled `x.latest`, where 'x' represents the major version number.
This image is updated when a new release of the source code is made.
_E.g._ if the following versions are available: `[1.1, 1.2, 1.3, 1.latest]` `1.latest` is the same as `1.3`.
When a new version is released, `1.4`, `1.latest` will be updated to be the same as `1.4`.

Unless an alternative image source is specified (see [Custom Docker Images](#custom-docker-images)), or the image is pinned to a specific version (see [Pinning Versions](#pinning-the-rctab-version)), whenever new source code is released, deployed instances of the RCTab API and function apps will update automatically.
When a non-backwards compatible change is made, the major version number is incremented.
Upgrading to the latest version will then require the infrastructure code to be updated and rebuilt by re-running `pulumi up`.

#### Custom Docker Images

To deploy RCTab from your own images you will need to set the Docker registry URL, your Docker registry username and a PAT as config secrets.

If you want to deviate from our image naming scheme, you will also need to set the image name variables and the tag.

```shell
pulumi config set docker_api_image 'myorg/my-api-image'
pulumi config set docker_usage_image 'myorg/my-usage-image'
pulumi config set docker_status_image 'myorg/my-status-image'
pulumi config set docker_api_image 'myorg/my-api-image'
pulumi config set docker_usage_image 'myorg/my-usage-image'
pulumi config set docker_status_image 'myorg/my-status-image'
pulumi config set docker_controller_image 'myorg/my-controller-image'
pulumi config set rctab_tag '2.3'
```

To save time with debugging and redeployment, it is advisable to should check that the images and tag work with the Docker CLI before running `pulumi up`.

By default, the API and Functions will create web hooks that you can use to receive notifications whenever there are changes to your images.
Azure calls this setting, [Continuous Deployment](https://learn.microsoft.com/en-us/azure/app-service/deploy-ci-cd-custom-container?tabs=acr&pivots=container-linux#4-enable-cicd).
If you wish, you can disable it `pulumi config set auto_deploy 'false'`.

> **Note**
If you are using our images, your app and functions will not receive web hook triggers whenever we push a new version and will only update to the latest version of an image when restarted.

##### DockerHub

```shell
pulumi config set --secret docker_registry_server_username '<username>'
pulumi config set --secret docker_registry_server_password '<PAT>'
```

No need to set the `docker_registry_server_url` as it is already set for DockerHub.

```shell
pulumi config set docker_usage_image '<owner>/<usage-function-image-name>:<tag>'
pulumi config set docker_controller_image '<owner>/<controller-function-image-name>:<tag>'
pulumi config set docker_status_image '<owner>/<status-function-image-name>:<tag>'
pulumi config set docker_api_image '<owner>/<api-image-name>:<tag>'
```

Note that, except for DockerHub "official" images, the image name will be proceeded by the image owner (e.g. `turingrc/rctab-api`) and that the `rctab_tag` setting will now be ignored as the tag should be provided as part of the `xyz_image` setting.

Check that you can pull the images

```shell
docker login
docker pull <owner>/<image-name>:<tag>
```

##### Azure Container Registry

```shell
pulumi config set --secret docker_registry_server_username '<username>'
pulumi config set --secret docker_registry_server_password '<password>'
pulumi config set --secret docker_registry_server_url 'https://<registry-name>.azurecr.io'
```

Set the secrets needed to authenticate with your Azure Container Registry (ACR) instance.

```shell
pulumi config set docker_usage_image '<registry-url>/<usage-function-image-name>:<tag>'
pulumi config set docker_controller_image '<registry-url>/controller-function-image-name>:<tag>'
pulumi config set docker_status_image '<registry-url>/<status-function-image-name>:<tag>'
```

Using ACR requires us to prepend the registry URL (typically `<registry-name>.azurecr.io`) to the image name.

```shell
docker login azure
docker pull <registry-url>/my-usage-image:2.3
```

#### Pinning the RCTab Version

```shell
pulumi config set rctab_tag '1.3'
```

If you want to set RCTab to a specific version, use the config variable `rctab_tag` to specify the exact version you wish to use.
The app will then point at that specific image and only redeploy if there are changes to that image.
Note that if you select a tag that doesn't exist, the infrastructure will still build successfully but will not deploy.
This setting will pin all the versions to the same value but will be overwritten by specific image settings such as `docker_api_image`, `docker_usage_image`, _etc._, which ignore the tag setting.
Consequently, it is possible, if not advisable, to set different versions for each component (API and each function).

## Post Pulumi Deployment

Once `pulumi up` has run without errors, all the resources required to run RCTab will have been created on Azure.
You can see them in the Azure Portal by navigating to the subscription previously chosen with `az account set`.
The function apps and API will automatically pull their images from DockerHub and start running.
However, there are some additional settings you need to configure to get RCTab working fully.

### Give the Usage App a Role on Azure

You will need to give the Usage app's [managed identity](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview) the [Billing Reader Role](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/manage-billing-access#give-read-only-access-to-billing) over the management group you set as the [config variable](#usage-management-group).

#### In the Azure Portal

1. Navigate to the [Azure portal](https://portal.azure.com/#home) and select the management group you selected as the [config variable](#usage-management-group).
2. Select the `Access control (IAM)` blade.
3. Select `Add` and then `Add role assignment`.
4. Select `Billing Reader` from the `Role` dropdown.
5. Select the Usage app's managed identity from the `Assign access to` dropdown.

#### Using the Azure CLI

```shell
az role assignment create --assignee-object-id '<usage-app-managed-identity-object-id>' --role '<insert-role-name-here>' --scope '<management-group-id>'
```

### Give the Controller App a Role on Azure

The Controller app needs a role assignment on Azure to be able to turn on or turn off subscriptions.

You can either use the `Owner` role or a custom role with `Microsoft.Authorization/*` and `Microsoft.Subscription/*` permissions.

You can either assign the role to subscriptions individually or to a management group.
This can be the same management group as the usage app or a child group of it, which
is useful if you want to monitor spending on subscriptions but only automatically turn off some subscriptions.

See above for instructions on role assignment via the Portal or CLI.

### Add the Web App's URL to the App Registration

Now that you know your RCTab web app's URL, you should add a redirect to the app registration you created for the [API](#api).

Your redirect URI will be something like `https://rctab-ticker-stack.azurewebsites.net/getAToken`.
See [add a redirect URI](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app#add-a-redirect-uri).

## Upgrades

If an infrastructure change requires a redeployment of the database, you will need to manually back up and restore the data.
The process will look something like this:

1. Before running `pulumi up`, back up the database with `pg_dump` or similar:

   ```shell
    pg_dump --host=<db-host> --username=rctabadmin --dbname=RCTab --file=rctab_backup --format d --data-only --jobs <parallel-tasks>
   ```

   We use `--exclude-databases` because Azure has some extra databases, used for internal purposes, which should not be included in the dump.
   We use `--data-only` because the RCTab server runs Alembic migrations on startup to create the schema.
1. Stop the web server.
1. Run `pulumi up` to redeploy the infrastructure.
1. To create the database schema (tables, stored procedures, etc.), either:
   1. Briefly restart the webserver, or
   1. Check out the RCTab API repository and run `alembic upgrade head` from it.
1. Restore the database from the backup with `psql`, `pg_restore` or similar:

   ```shell
   pg_restore -d RCTab -p 5432 -U rctabadmin -h <db-host> --data-only --strict-names --verbose rctab_backup
   ```

   Check the output for WARNINGs and ERRORs to ensure the restore was successful.
1. Restart the web server.
