import json
from http import HTTPStatus
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from config import AlertError, AlertSettings, BackupReport

CAPTION_TITLE = "✅ <b>BACKUP COMPLETADO</b>"
CAPTION_ORIGIN = "🧪 <i>Simulación</i>"
PARSE_MODE = "HTML"
SEND_PHOTO = "sendPhoto"
SEND_MESSAGE = "sendMessage"
BANNER_FAILURE_STATUSES = (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND)
DOWNLOAD_BUTTON_TEXT = "⬇️ Descargar Backup"


def build_caption(report: BackupReport, settings: AlertSettings) -> str:
    return "\n".join(
        (
            CAPTION_TITLE,
            CAPTION_ORIGIN,
            "",
            f"📦 <code>{report.filename}</code>",
            f"⚖️ Tamaño: {report.size}",
            f"🔍 Checksum: {report.checksum_status}",
            f"☁️ Almacenamiento: {report.upload_status}",
            f"🖥️ Servidor: {settings.server_name}",
            "",
            f"⬇️ {report.download_url}",
        )
    )


def _call(settings: AlertSettings, method: str, payload: dict) -> dict:
    url = f"{settings.telegram_api_base}/bot{settings.telegram_token}/{method}"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": settings.user_agent,
        },
        method="POST",
    )
    with urlopen(request, timeout=settings.timeout) as response:
        body = response.read().decode("utf-8")

    result = json.loads(body) if body.strip() else {}
    if not result.get("ok"):
        raise AlertError(
            f"Telegram {method}: {result.get('description', 'respuesta sin ok=true')}"
        )
    return result


def _is_banner_failure(exc: Exception) -> bool:
    if isinstance(exc, AlertError):
        return True
    return getattr(exc, "code", None) in BANNER_FAILURE_STATUSES


def send_backup_alert(report: BackupReport, settings: AlertSettings) -> str:
    keyboard = {
        "inline_keyboard": [
            [{"text": DOWNLOAD_BUTTON_TEXT, "url": report.download_url}]
        ]
    }
    caption = build_caption(report, settings)
    photo_payload = {
        "chat_id": settings.telegram_chat_id,
        "photo": settings.banner_url,
        "caption": caption,
        "parse_mode": PARSE_MODE,
        "reply_markup": keyboard,
    }
    try:
        _call(settings, SEND_PHOTO, photo_payload)
        return "foto enviada con botón de descarga"
    except (AlertError, HTTPError) as exc:
        if not _is_banner_failure(exc):
            raise
        _call(
            settings,
            SEND_MESSAGE,
            {
                "chat_id": settings.telegram_chat_id,
                "text": caption,
                "parse_mode": PARSE_MODE,
                "reply_markup": keyboard,
                "disable_web_page_preview": True,
            },
        )
        return "banner caído, enviada solo como texto"
