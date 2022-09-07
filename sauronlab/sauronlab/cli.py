import os
import random
import shutil
from pathlib import Path
from subprocess import DEVNULL, check_call
from typing import List

import orjson
import typer

from sauronlab.core import SauronlabResources, logger

MAIN_DIR = os.environ.get("SAURONLAB_DIR", Path.home() / ".sauronlab")
cli = typer.Typer()


class Installer:
    """"""

    def __init__(self):
        self.n_created = 0

    def init(self) -> None:
        """
        Initializes.
        """
        self._info("Setting up sauronlab configuration...")
        MAIN_DIR.mkdir(parents=True, exist_ok=True)
        conn_file = MAIN_DIR / "connection.json"
        config_file = MAIN_DIR / "sauronlab.config"
        ssh_config_file = Path.home() / ".ssh" / "config"
        tunneling = None
        if not conn_file.exists():
            self._bar()
            self._info("No connection.json detected.")
            self._notice("Asking for database connection information...")
            tunneling = typer.prompt("Will you be connecting over an SSH tunnel? [y/n]", type=bool)
            suggested_port = random.randint(49152, 65535) if tunneling else 3306
            conn = dict(
                database=typer.prompt("Database name", type=str, default="valar"),
                user=typer.prompt("Database username", type=str),
                password=typer.prompt("Database password", type=str),
                host=typer.prompt("Database hostname", type=str, default="127.0.0.1"),
                port=typer.prompt("Database port", type=int, default=suggested_port),
            )
            conn_file.write_text(orjson.dumps(conn).decode(encoding="utf8"), encoding="utf8")
            self.n_created += 1
            self._info(f"Wrote {conn_file}")
            # this is a bit confusing
            # if they want to set up a tunnel, we're not asking for info if the config file exists
            if tunneling and config_file.exists():
                self._info(f"{config_file} found. Edit it for SSH tunnel setup.")
            self._bar()
        if not config_file.exists():
            self._bar()
            self._info("No sauronlab.config detected.")
            self._notice("Asking for misc information...")
            if tunneling is None:
                # if we didn't find out before, we need to know now
                tunneling = typer.prompt("Will you be connecting over an SSH tunnel?", type=bool)
            if tunneling:
                tunnel_host = typer.prompt(
                    f"Remote hostname of SSH tunnel.\n"
                    f"This should match a hostname or alias in {ssh_config_file}",
                    default="valinor",
                )
                if not ssh_config_file.is_file() or tunnel_host not in ssh_config_file.read_text(
                    encoding="utf8"
                ):
                    self._error(f"NOTE: '{tunnel_host}' is not listed in {ssh_config_file}")
                    self._error(
                        "See https://dmyersturnbull.github.io/macos-setup/#security-ssh--gpg for an example."
                    )
                tunnel_port = typer.prompt(
                    "Port on the remote host. "
                    "Change this only if the database is configured differently.",
                    default="3306",
                )
            else:
                # we need some values
                tunnel_host = "3306"
                tunnel_port = "valinor"
            self._notice("Miscellaneous info...")
            user = typer.prompt("username in ``valar.users`` (e.g. 'john')", type=str)
            cache_path = MAIN_DIR / "cache"
            cache_path = Path(typer.prompt("path for local data cache", default=cache_path))
            datasets_path = cache_path / "datasets"
            datasets_path = typer.prompt("path for feather-format datasets", default=datasets_path)
            videos_path = cache_path / "videos"
            videos_path = typer.prompt("path for locally cached full videos", default=videos_path)
            if os.name == "nt":
                first_line = r"path with a (network) drive letter; e.g. ``\\192.234.342/my-share-name/my_data_dir/store``"
            else:
                first_line = r"path to a mounted share (e.g. ``/shire``)"
            shire_path = typer.prompt(
                "Path to video store."
                + "\n"
                + first_line
                + f"\na symlinked directory (e.g. ``{str(MAIN_DIR / 'shire')}``)"
                "\nan explicit Samba URI (e.g. ``/192.234.342/my-data/shire``),"
                "\nor a path over SSH (e.g. ``valinor:/shire``)."
                "\nIf provided, the data MUST be organized under /year/month/tag/ (refer to the docs)."
                "\nIf you do not have access, leave as ``none``.",
                default="none",
            )
            data = (
                SauronlabResources.path("templates", "sauronlab.config")
                .read_text(encoding="utf8")
                .replace("$${user}", user)
                .replace("$${shire}", str(shire_path))
                .replace("$${cache}", str(cache_path))
                .replace("$${datasets}", str(datasets_path))
                .replace("$${videos}", str(videos_path))
                .replace("$${tunnel_host}", tunnel_host)
                .replace("$${tunnel_port}", str(tunnel_port))
            )
            # remove the line completely
            if shire_path is None:
                data = data.replace("shire_path = none", "")
            config_file.write_text(data)
            self.n_created += 1
        self._copy_if(
            MAIN_DIR / "jupyter.txt",
            SauronlabResources.path("templates", "jupyter.txt"),
        )
        self._copy_if(
            MAIN_DIR / "sauronlab.mplstyle",
            SauronlabResources.path("styles", "default.mplstyle"),
        )
        self._copy_if(
            MAIN_DIR / "sauronlab_viz.properties",
            SauronlabResources.path("styles", "default.properties"),
        )
        if self.n_created > 0:
            self._info("Finished. Edit these files as needed.")
        else:
            self._info("Finished. You already have all required config files.")

    def _notice(self, msg: str) -> None:
        typer.echo(typer.style(msg, bold=True))

    def _bar(self) -> None:
        typer.echo(typer.style("-" * 100, bold=True))

    def _info(self, msg: str) -> None:
        typer.echo(msg)

    def _success(self, msg: str) -> None:
        typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))

    def _error(self, msg: str) -> None:
        typer.echo(typer.style(msg, fg=typer.colors.RED, bold=True))

    def _copy_if(self, dest: Path, source: Path) -> None:
        if dest.exists():
            self._info(f"Skipped {dest}")
            return
        # noinspection PyTypeChecker
        dest.parent.mkdir(parents=True, exist_ok=True)
        # noinspection PyTypeChecker
        shutil.copy(source, dest)
        self._info(f"Copied {source} → {dest}")
        self.n_created += 1


class Commands:
    @staticmethod
    @cli.command()
    def init() -> None:
        Installer().init()

    @staticmethod
    @cli.command()
    def tunnel() -> None:
        from pocketutils.tools.filesys_tools import FilesysTools

        config = FilesysTools.read_properties_file(MAIN_DIR / "sauronlab.config")
        vpy = orjson.loads((MAIN_DIR / "connection.json").read_text(encoding="utf8"))
        if "tunnel_host" not in config or "tunnel_port" not in config:
            raise ValueError(f"Tunnel host or port in sauronlab.config missing")
        host, port = vpy["host"], vpy["port"]
        remote_host, remote_port = config["tunnel_host"], config["tunnel_port"]
        # ssh -L 53419:localhost:3306 valinor.ucsf.edu
        typer.echo("Tunneling into valar...")
        cmd = ["ssh", "-L", f"{port}:{host}:{remote_port}", remote_host]
        typer.echo(f"Running: {' '.join(cmd)}")
        try:
            check_call(cmd, stdout=DEVNULL)  # nosec
        finally:
            typer.echo("Closed tunnel to valar.")

    @staticmethod
    @cli.command()
    def dl(runs: List[str]) -> None:
        """
        Downloads runs with videos.

        Args:
            runs: Run IDs

        """
        from sauronlab.extras.video_caches import VideoCache

        cache = VideoCache()
        n_exists = sum([not cache.has_video(v) for v in runs])
        for arg in runs:
            cache.download(int(arg))
        logger.notice(f"Downloaded {n_exists} videos.")


if __name__ == "__main__":
    cli()


__all__ = ["Commands"]
