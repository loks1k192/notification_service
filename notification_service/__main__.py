"""Entry point for running the notification service as a module."""

import asyncio

from notification_service.consumer import main

if __name__ == "__main__":
    asyncio.run(main())
