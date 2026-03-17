#!/usr/bin/env python3
"""Create an outbound phone call with Twilio to a FastAPI voice endpoint."""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from twilio.base.exceptions import TwilioException
from twilio.rest import Client


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    account_sid: str
    auth_token: str
    twilio_phone_number: str
    user_phone_number: str
    base_url: str

    @property
    def twiml_url(self) -> str:
        """Build the TwiML webhook URL for the outbound call."""
        return f"{self.base_url.rstrip('/')}/twilio/incoming"


def _get_env(name: str) -> Optional[str]:
    """Read and normalize environment values."""
    value = os.getenv(name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def load_settings() -> Settings:
    """Load and validate required environment variables."""
    required = {
        "TWILIO_ACCOUNT_SID": _get_env("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": _get_env("TWILIO_AUTH_TOKEN"),
        "TWILIO_PHONE_NUMBER": _get_env("TWILIO_PHONE_NUMBER"),
        "USER_PHONE_NUMBER": _get_env("USER_PHONE_NUMBER"),
        "BASE_URL": _get_env("BASE_URL"),
    }

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(
            "Missing required environment variable(s): "
            + ", ".join(sorted(missing))
        )

    return Settings(
        account_sid=required["TWILIO_ACCOUNT_SID"],
        auth_token=required["TWILIO_AUTH_TOKEN"],
        twilio_phone_number=required["TWILIO_PHONE_NUMBER"],
        user_phone_number=required["USER_PHONE_NUMBER"],
        base_url=required["BASE_URL"],
    )


def create_call(
    client: Client,
    settings: Settings,
    *,
    max_retries: int = 3,
    base_delay_seconds: float = 1.5,
) -> str:
    """Create outbound call with simple exponential backoff retries."""
    for attempt in range(1, max_retries + 1):
        try:
            call = client.calls.create(
                to=settings.user_phone_number,
                from_=settings.twilio_phone_number,
                url=settings.twiml_url,
            )
            return call.sid
        except TwilioException as exc:
            is_last_attempt = attempt == max_retries
            logging.exception(
                "Twilio API call attempt %d/%d failed.",
                attempt,
                max_retries,
            )
            if is_last_attempt:
                raise RuntimeError(
                    f"Unable to create call after {max_retries} attempts"
                ) from exc
            sleep_seconds = base_delay_seconds * (2 ** (attempt - 1))
            logging.warning("Retrying in %.1f seconds...", sleep_seconds)
            time.sleep(sleep_seconds)

    # Defensive fallback; loop should return or raise before this.
    raise RuntimeError("Unexpected error while creating Twilio call")


def main() -> int:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        settings = load_settings()
        client = Client(settings.account_sid, settings.auth_token)
        logging.info(
            "Creating outbound call to %s via %s (webhook: %s)",
            settings.user_phone_number,
            settings.twilio_phone_number,
            settings.twiml_url,
        )
        call_sid = create_call(client, settings)
        print(f"Call initiated successfully. SID: {call_sid}")
        return 0
    except ValueError as exc:
        logging.error("Configuration error: %s", exc)
        return 1
    except RuntimeError as exc:
        logging.error("Call creation failed: %s", exc)
        return 1
    except Exception:
        logging.exception("Unexpected error occurred while making outbound call")
        return 1


if __name__ == "__main__":
    sys.exit(main())
