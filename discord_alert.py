import json
from http import HTTPStatus
from urllib.request import Request, urlopen

from config import AlertError, AlertSettings, BackupReport

WEBHOOK_USERNAME = "ALERTAS DC"
EMBED_TITLE = "✅ BACKUP COMPLETADO"
EMBED_DESCRIPTION = "Respaldo generado, verificado y transferido correctamente."
FOOTER_LABELS = ("Servidor", "Origen")
ORIGIN_LABEL = "SIMULACIÓN"
DOWNLOAD_TEXT = "⬇️ Descargar Backup"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ACCEPTED_STATUSES = (HTTPStatus.OK, HTTPStatus.NO_CONTENT)


def build_payload(report: BackupReport, settings: AlertSettings) -> dict:
    embed = {
        "title": EMBED_TITLE,
        "description": (
            f"{EMBED_DESCRIPTION}\n\n"
            f"**{DOWNLOAD_TEXT}** → {report.download_url}"
        ),
        "color": settings.embed_color,
        "image": {"url": settings.banner_url},
        "fields": [
            {"name": "📦 Archivo", "value": f"`{report.filename}`", "inline": True},
            {"name": "⚖️ Tamaño", "value": report.size, "inline": True},
            {"name": "🔍 Checksum", "value": f"`{report.checksum_status}`", "inline": True},
            {"name": "☁️ Almacenamiento", "value": f"`{report.upload_status}`", "inline": False},
        ],
        "footer": {
            "text": f"{FOOTER_LABELS[0]}: {settings.server_name} | "
            f"{FOOTER_LABELS[1]}: {ORIGIN_LABEL}"
        },
        "timestamp": report.generated_at.strftime(TIMESTAMP_FORMAT),
    }
    payload = {"username": WEBHOOK_USERNAME, "embeds": [embed]}
    # if settings.discord_avatar_url:
    #     payload["avatar_url"] = settings.discord_avatar_url
    return payload


def send_backup_alert(report: BackupReport, settings: AlertSettings) -> str:
    request = Request(
        settings.discord_webhook_url,
        data=json.dumps(build_payload(report, settings)).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": settings.user_agent,
        },
        method="POST",
    )
    with urlopen(request, timeout=settings.timeout) as response:
        status = response.status
    if status not in ACCEPTED_STATUSES:
        raise AlertError(f"Discord respondió {status}.")
    return f"embed enviado (HTTP {status})"
