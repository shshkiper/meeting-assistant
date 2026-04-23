"""
Optional Jira integration service.
Creates issues from extracted meeting tasks.
"""

from typing import Optional
from loguru import logger

from app.core.config import settings


class JiraService:
    """Thin wrapper around the Jira Python client."""

    def __init__(self):
        self._client = None

    def get_client(self):
        if not settings.JIRA_ENABLED:
            return None
        if self._client is None:
            try:
                from jira import JIRA
                self._client = JIRA(
                    server=settings.JIRA_URL,
                    token_auth=settings.JIRA_TOKEN,
                )
                logger.info(f"Jira connected: {settings.JIRA_URL}")
            except Exception as e:
                logger.error(f"Jira connection failed: {e}")
        return self._client

    def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "Medium",
        assignee_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a Jira issue and return its key (e.g. MTG-42).
        Returns None if Jira is disabled or call fails.
        """
        client = self.get_client()
        if not client:
            return None
        try:
            fields: dict = {
                "project": {"key": settings.JIRA_PROJECT_KEY},
                "summary": title[:255],
                "description": description or "",
                "issuetype": {"name": "Task"},
                "priority": {"name": priority.capitalize()},
            }
            issue = client.create_issue(fields=fields)
            logger.info(f"Jira issue created: {issue.key}")
            return issue.key
        except Exception as e:
            logger.error(f"Jira issue creation failed: {e}")
            return None

    def transition_issue(self, issue_key: str, status: str) -> bool:
        """Move issue to a target status by name."""
        client = self.get_client()
        if not client:
            return False
        try:
            transitions = client.transitions(issue_key)
            match = next((t for t in transitions if t["name"].lower() == status.lower()), None)
            if match:
                client.transition_issue(issue_key, match["id"])
                return True
        except Exception as e:
            logger.error(f"Jira transition failed: {e}")
        return False


jira_service = JiraService()
