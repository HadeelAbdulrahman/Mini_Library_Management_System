import os
import sys
import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class LibraryConfig(AppConfig):
    name = 'library'

    def ready(self):
        """Start a lightweight scheduler for auto-return.

        - Runs only during `runserver`
        - Guarded to avoid double-start under Django autoreload
        """
        # Only run scheduler for the dev server.
        if 'runserver' not in sys.argv:
            return

        # Avoid duplicate scheduler instances with the autoreloader.
        # Django sets RUN_MAIN='true' in the reloaded process.
        if os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from .scheduler import auto_return_due_borrows

            scheduler = BackgroundScheduler(timezone=str(os.environ.get('TZ') or 'UTC'))
            scheduler.add_job(
                auto_return_due_borrows,
                trigger=IntervalTrigger(seconds=5),
                id='auto_return_due_borrows',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            scheduler.start()
            logger.info('Library auto-return scheduler started (every 5s).')
        except Exception:
            # Don't crash the app if scheduler fails.
            logger.exception('Failed to start auto-return scheduler')
