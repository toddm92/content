import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

''' IMPORTS '''
from typing import Dict, Tuple, List, AnyStr, Union, Optional
import urllib3

# Disable insecure warnings
urllib3.disable_warnings()

"""GLOBALS/PARAMS
Attributes:
    INTEGRATION_NAME:
        Name of the integration as shown in the integration UI, for example: Microsoft Graph User.

    INTEGRATION_COMMAND_NAME:
        Command names should be written in all lower-case letters,
        and each word separated with a hyphen, for example: msgraph-user.

    INTEGRATION_CONTEXT_NAME:
        Context output names should be written in camel case, for example: MSGraphUser.
"""
INTEGRATION_NAME = 'CyberArk Vault Integration'
INTEGRATION_COMMAND_NAME = 'cyberark-pas'
INTEGRATION_CONTEXT_NAME = 'CyberArk.Vault'


class Client(BaseClient):
    def __init__(self, base_url, verify, proxy, auth_method, credentials):
        base_url = urljoin(base_url, "/PasswordVault/API/")
        self._username = credentials.get("identifier")
        self._password = credentials.get("password")
        super().__init__(base_url, verify=verify, proxy=proxy)
        self._logon(auth_method)
        headers = {
            "Content Type": "application/json",
            "Authorization": self._auth_code
        }
        self._headers = headers

    def __del__(self):
        self._logoff()

    def _logon(self, auth_method):
        body = {
            "username": self._username,
            "password": self._password
        }
        suffix = f"auth/{auth_method}/Logon"
        res = self._http_request("POST", suffix, json_data=body, resp_type="Text")
        # Remove `{` and }` from response
        auth_code = res.replace("{", "").replace("}", "")
        self._auth_code = auth_code

    def _logoff(self):
        suffix = f"Auth/Logoff"
        self._http_request("POST", suffix)

    def create_user(
            self,
            username,
            email,
            first_name,
            last_name,
            change_password_on_the_next_logon,
            expiry_date,
            enable_user,
            vault_location,
            authentication_method,
            initial_password=None,
            **kwargs
    ):
        suffix = "/Users"
        body = {
            "username": username,
            "initialPassword": initial_password,
            "enableUser": argToBoolean(enable_user),
            "changePassOnNextLogon": argToBoolean(change_password_on_the_next_logon),
            "location": vault_location,
            "authenticationMethod": authentication_method,
            "personalDetails": {
                "firstName": first_name,
                "lastName": last_name
            },
            "internet": {
                "businessEmail": email
            }
        }
        if expiry := self.get_expiry_epoch(expiry_date):
            body.update({
                "expiryDate": expiry
            })

        return self._http_request("POST", suffix, json_data=body)

    def update_user(self, user_id: str) -> dict:
        """This method updates an existing Vault user.
        You must have the following authorizations:
        * Add/Update Users
        * In order to edit changePassOnNextLogon , you must have the Reset Password authorization.

        Args:
            user_id: UserID to delete

        Returns:
            response dict
        """
        suffix = f"Users/{user_id}/"
        method = "PUT"
        body = {}
        return self._http_request(method, suffix, json_data=body)

    def delete_user(self, user_id: str) -> dict:
        """This method deletes a specific user in the Vault.
        You must have the following authorizations:
        * Add/Update Users

        Args:
            user_id: UserID to delete
        """
        suffix = f"Users/{user_id}/"
        method = "DELETE"
        return self._http_request(method, suffix)

    def get_user(self):
    @staticmethod
    def get_expiry_epoch(expiry_date: Optional[str]) -> Optional[int]:
        if expiry_date:
            return date_to_timestamp(expiry_date, "%Y-%m-%dT%H:%M")
        return None


''' COMMANDS MANAGER / SWITCH PANEL '''


def main():  # pragma: no cover
    params = demisto.params()
    base_url = params.get('url', '')
    verify = not params.get('insecure', False)
    proxy = argToBoolean(params.get('proxy'))
    auth_method = params.get("auth_method")
    credentials = params.get("credentials")
    client = Client(base_url, verify=verify, proxy=proxy, auth_method=auth_method, credentials=credentials)
    command = demisto.command()
    demisto.info(f'Command being called is {command}')

    # Switch case
    commands = {
        'test-module': test_module_command,
        f'{INTEGRATION_COMMAND_NAME}-create-user': list_accounts_command,
        f'{INTEGRATION_COMMAND_NAME}-update-user': lock_account_command,
        f'{INTEGRATION_COMMAND_NAME}-delete-user': unlock_account_command,
        f'{INTEGRATION_COMMAND_NAME}-reset-account': reset_account_command,
        f'{INTEGRATION_COMMAND_NAME}-lock-vault': lock_vault_command,
        f'{INTEGRATION_COMMAND_NAME}-unlock-vault': unlock_vault_command,
        f'{INTEGRATION_COMMAND_NAME}-list-vaults': list_vaults_command
    }
    try:
        return_outputs(*commands[command](client, demisto.args()))
    # Log exceptions
    except Exception as e:
        err_msg = f'Error in {INTEGRATION_NAME} - [{e}]'
        return_error(err_msg, error=e)


if __name__ == 'builtins':  # pragma: no cover
    main()
