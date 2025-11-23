import json
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from ticts.utils import NO_DEFAULT


class TictsIOMixin:
    def serialize(
        self,
        date_format: Literal["epoch", "iso", "isoformat"] = "epoch",
    ) -> dict[str, Any]:
        if date_format.lower() == "epoch":
            keys = [key.value for key in self.index]
        elif date_format.lower() in ["iso", "isoformat"]:
            keys = [key.isoformat() for key in self.index]
        else:
            msg = "Date serealize with date_format equal to '{}' is not implemented"
            raise NotImplementedError(msg.format(date_format))

        return {
            "data": dict(zip(keys, self.values())),
            "default": self.default if self.default != NO_DEFAULT else "no_default",
            "name": self.name,
        }

    serealize = serialize  # legacy (mispelled beforehand)

    def to_json(self, path_or_buf, date_format="epoch", compression="infer"):
        stringify_path = (
            pd.io.common._stringify_path
            if hasattr(pd.io.common, "_stringify_path")
            else pd.io.common.stringify_path
        )
        path_or_buf = stringify_path(path_or_buf)

        s = json.dumps(self.serealize())

        if isinstance(path_or_buf, str):
            if hasattr(pd.io.common, "_get_handle"):
                fh, _ = pd.io.common._get_handle(
                    path_or_buf, "w", compression=compression
                )
                try:
                    fh.write(s)
                finally:
                    fh.close()

            else:
                fh = pd.io.common.get_handle(path_or_buf, "w", compression=compression)
                try:
                    fh.handle.write(s)
                finally:
                    fh.close()

        elif path_or_buf is None:
            return s
        else:
            path_or_buf.write(s)

    @classmethod
    def from_json(cls, path):
        if not hasattr(path, "read"):
            path = Path(path)
            if not path.exists():
                raise Exception(f"'{path}' does not exists.")
            path = open(path)

        content = json.load(path)
        return cls(**content)
