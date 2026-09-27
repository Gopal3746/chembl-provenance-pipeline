from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonRecordCache:
    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self.path = Path(path)
        self.records: dict[str, dict[str, Any]] = {}

        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if isinstance(payload, dict):
            self.records = payload

    def get(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        return self.records.get(key)

    def set(
        self,
        key: str,
        value: dict[str, Any],
    ) -> None:
        self.records[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.path.with_suffix(
            f"{self.path.suffix}.tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.records,
                file,
                indent=2,
                sort_keys=True,
            )

        temporary_path.replace(self.path)

    def __len__(self) -> int:
        return len(self.records)
