"""
from blacksheep import Application

from app.settings import Settings

def configure_authentication(app: Application, settings: Settings):
    \"""
    Configure authentication as desired. For reference:
    https://www.neoteroi.dev/blacksheep/authentication/
    \"""
    
"""

class Authentication:
    auth_type = None


class UserPass(Authentication):
    # Regular username & password authentication, check against SQL database, generating a JWT
    auth_type = "userpass"


class SSO(Authentication):
    # SSO / SAML authentication
    auth_type = "sso"
