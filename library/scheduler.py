import logging
from django.utils import timezone


logger = logging.getLogger(__name__)


def auto_return_due_borrows():
    """Mark any borrows past due_at as returned.

    This runs server-side, so it still works even if the student's browser closes.
    """
    from .models import Borrow

    now = timezone.now()
    # Single UPDATE query for efficiency
    updated = Borrow.objects.filter(returned=False, due_at__lte=now).update(
        returned=True,
        returned_at=now,
    )
    if updated:
        logger.info("Auto-returned %s borrow(s) at %s", updated, now.isoformat())
