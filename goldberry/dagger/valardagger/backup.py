from pathlib import Path
import subprocess


class Backup:
    def __init__(self, path: Path, sensors: bool, features: bool, gzip_level: int):
        self._path = path
        self._sensors = sensors
        self._features = features
        self._gzip_level = gzip_level

    def backup(self) -> None:
        tables = subprocess.check_output(
            ["mysql", "-NBA", "-u", "root", "-D", "valar", "-e", "show tables"], encoding="utf8"
        ).splitlines()
        for table in tables:
            if (self._sensors or table != "sensor_data") and (
                self._features or table != "feature_data"
            ):
                self._backup_table(table)

    def _backup_table(self, table: str) -> None:
        ps = subprocess.Popen(
            [
                "mysqldump",
                "--single-transaction",
                "--max_allowed_packet=1073741824",
                "--hex-blob",
                "-P",
                "3306",
                "-u",
                "root",
                "valar",
                table,
            ],
            stdout=subprocess.PIPE,
        )
        subprocess.check_call(
            ["gzip", "-c", f"-{self._gzip_level}", str(self._path / f"{table}.sql.gz")],
            stdin=ps.stdout,
        )
