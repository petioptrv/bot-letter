import logging
from typing import Optional


def log_for_newsletter_issue(
    level: int, issue_id: str, message: str, exc_info: Optional[Exception] = None
):
    logging.getLogger(__name__).log(
        level=level, msg=f"ni-{issue_id}: {message}", exc_info=exc_info
    )
