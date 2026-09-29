import random
import sys
from datetime import datetime, timezone

from config import AlertError, AlertSettings, BackupReport, ConfigError
from config import settings as load_settings
from discord_alert import send_backup_alert as send_discord_alert
from telegram_alert import send_backup_alert as send_telegram_alert

FILENAME_PREFIX = "backup-produccion"
FILENAME_SUFFIX = ".tar.gz"
FILENAME_STAMP = "%Y%m%d-%H%M%S"
SIZE_RANGE_MB = (120.0, 980.0)
SIZE_PRECISION = 1
SIMULATED_CHECKSUM = "OK (SHA-256 Match)"
SIMULATED_UPLOAD = "200 OK (verificado en el destino simulado)"

HANDLED_ERRORS = (ConfigError, AlertError, OSError, ValueError)


def build_simulated_report(settings: AlertSettings) -> BackupReport:
    generated_at = datetime.now(timezone.utc)
    filename = f"{FILENAME_PREFIX}-{generated_at.strftime(FILENAME_STAMP)}{FILENAME_SUFFIX}"
    size_mb = round(random.uniform(*SIZE_RANGE_MB), SIZE_PRECISION)
    return BackupReport(
        filename=filename,
        size=f"{size_mb} MB",
        checksum_status=SIMULATED_CHECKSUM,
        upload_status=SIMULATED_UPLOAD,
        download_url=f"{settings.download_base_url}/{filename}",
        generated_at=generated_at,
    )


def enable_utf8_output() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")


def notify(label: str, action, report: BackupReport, settings: AlertSettings) -> bool:
    try:
        print(f"✅ {label}: {action(report, settings)}")
    except HANDLED_ERRORS as exc:
        print(f"❌ {label}: {exc}")
        return False
    return True


def main() -> int:
    enable_utf8_output()
    try:
        settings = load_settings()
    except HANDLED_ERRORS as exc:
        print(f"❌ Configuración: {exc}")
        return 1

    report = build_simulated_report(settings)
    print(f"🧪 Simulando un backup en {settings.server_name}")
    print(f"   Archivo:  {report.filename}")
    print(f"   Tamaño:   {report.size}")
    print(f"   Checksum: {report.checksum_status}")
    print(f"   Subida:   {report.upload_status}")
    print(f"   Descarga: {report.download_url}")
    print()

    results = [
        notify("Discord", send_discord_alert, report, settings),
        notify("Telegram", send_telegram_alert, report, settings),
    ]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
