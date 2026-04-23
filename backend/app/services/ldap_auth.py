"""
Corporate LDAP / Active Directory authentication.
Falls back to local DB auth if LDAP is disabled.
"""

from typing import Optional, Dict
from loguru import logger

from app.core.config import settings


class LDAPService:
    """Authenticate users against corporate AD/LDAP."""

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Try to bind with user credentials.
        Returns dict {email, full_name, dn} on success, None on failure.
        """
        if not settings.LDAP_ENABLED:
            return None
        try:
            import ldap
            conn = ldap.initialize(settings.LDAP_SERVER)
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 5)
            conn.set_option(ldap.OPT_REFERRALS, 0)

            # First bind as service account to find user DN
            conn.simple_bind_s(settings.LDAP_BIND_DN, settings.LDAP_BIND_PASSWORD)

            search_filter = f"(|(mail={username})(sAMAccountName={username}))"
            results = conn.search_s(
                settings.LDAP_BASE_DN,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ["mail", "displayName", "distinguishedName"],
            )
            if not results:
                return None

            dn, attrs = results[0]

            # Re-bind as the user to verify password
            conn.simple_bind_s(dn, password)

            email = attrs.get("mail", [b""])[0].decode()
            full_name = attrs.get("displayName", [username.encode()])[0].decode()

            conn.unbind_s()
            return {"email": email, "full_name": full_name, "dn": dn}

        except Exception as e:
            logger.warning(f"LDAP auth failed for {username}: {e}")
            return None


ldap_service = LDAPService()
