import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
ENV_EXAMPLE_NAME = ".env.example"

DEFAULT_REQUEST_TIMEOUT = 10
DEFAULT_USER_AGENT = "SimuladorAlertas/1.0"
DEFAULT_EMBED_COLOR = 0x2ECC71

REQUIRED_KEYS = (
    "DISCORD_WEBHOOK_URL",
    "BANNER_IMAGE_URL",
    "EMBED_COLOR",
    "SERVER_NAME",
    "DOWNLOAD_BASE_URL",
    "TELEGRAM_API_BASE",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)


class ConfigError(RuntimeError):
    pass


class AlertError(RuntimeError):
    pass


@dataclass(frozen=True)
class AlertSettings:
    discord_webhook_url: str
    discord_avatar_url: str
    embed_color: int
    banner_url: str
    server_name: str
    download_base_url: str
    telegram_api_base: str
    telegram_token: str
    telegram_chat_id: str
    timeout: int
    user_agent: str


@dataclass(frozen=True)
class BackupReport:
    filename: str
    size: str
    checksum_status: str
    upload_status: str
    download_url: str
    generated_at: datetime


def _collect(*names: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        raw = os.getenv(name, "").strip()
        if raw:
            values[name] = raw
        else:
            missing.append(name)
    if missing:
        raise ConfigError(
            f"Faltan variables en {ENV_PATH.name}: {', '.join(missing)}. "
            f"Completalas en {ENV_PATH} o tomalas de {ENV_EXAMPLE_NAME}."
        )
    return values


def _optional(name: str, default: str) -> str:
    return os.getenv(name, "").strip() or default


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw, 0)
    except ValueError as exc:
        raise ConfigError(
            f"{name} debe ser un entero decimal o hexadecimal (ej. 0x2ECC71), no {raw!r}."
        ) from exc


def settings() -> AlertSettings:
    load_dotenv(ENV_PATH)
    values = _collect(*REQUIRED_KEYS)
    return AlertSettings(
        discord_webhook_url=values["DISCORD_WEBHOOK_URL"],
        discord_avatar_url=_optional("DISCORD_AVATAR_URL", ""),
        embed_color=_as_int("EMBED_COLOR", DEFAULT_EMBED_COLOR),
        banner_url=values["BANNER_IMAGE_URL"],
        server_name=values["SERVER_NAME"],
        download_base_url=values["DOWNLOAD_BASE_URL"].rstrip("/"),
        telegram_api_base=values["TELEGRAM_API_BASE"].rstrip("/"),
        telegram_token=values["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=values["TELEGRAM_CHAT_ID"],
        timeout=_as_int("REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT),
        user_agent=_optional("USER_AGENT", DEFAULT_USER_AGENT),
    )
