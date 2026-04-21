from __future__ import annotations

import subprocess

from browser_automation.domain.exceptions import ChromeLaunchError
from browser_automation.domain.zalo_launcher import ChromeLaunchConfig


class SubprocessChromeProcessLauncher:
    def build_command(self, config: ChromeLaunchConfig) -> list[str]:
        command = [
            str(config.chrome_executable),
        ]
        if config.new_window:
            command.append("--new-window")
        if config.window_placement is not None:
            command.extend(
                [
                    f"--window-position={config.window_placement.left},{config.window_placement.top}",
                    f"--window-size={config.window_placement.width},{config.window_placement.height}",
                ]
            )
        command.extend(
            [
            f"--user-data-dir={config.user_data_dir}",
            config.target_url,
            ]
        )
        if config.profile_directory:
            command.insert(-1, f"--profile-directory={config.profile_directory}")
        return command

    def launch(self, config: ChromeLaunchConfig) -> None:
        command = self.build_command(config)
        popen_kwargs: dict[str, object] = {
            "args": command,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }

        detached_process = getattr(subprocess, "DETACHED_PROCESS", 0)
        new_process_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if detached_process or new_process_group:
            popen_kwargs["creationflags"] = detached_process | new_process_group

        try:
            subprocess.Popen(**popen_kwargs)
        except OSError as exc:
            raise ChromeLaunchError(f"Could not start Google Chrome: {exc}") from exc
