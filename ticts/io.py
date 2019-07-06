import json
from pathlib import Path

import pandas as pd

from .utils import NO_DEFAULT


class TictsIOMixin:
    def serealize(self, date_format='epoch'):
        if date_format.lower() == 'epoch':
            keys = [key.value for key in self.keys()]
        elif date_format.lower() in ['iso', 'isoformat']:
            keys = [key.isoformat() for key in self.keys()]
        else:
            msg = "Date serealize with date_format equal to '{}' is not implemented"
            raise NotImplementedError(msg.format(date_format))

        return {
            'data': {key: val
                     for key, val in zip(keys, self.values())},
            'default': self.default
            if self.default != NO_DEFAULT else 'no_default',
            'name': self.name,
        }

    def to_json(self, path_or_buf, date_format='epoch', compression='infer'):
        path_or_buf = pd.io.common._stringify_path(path_or_buf)

        s = json.dumps(self.serealize())

        if isinstance(path_or_buf, str):
            fh, handles = pd.io.common._get_handle(
                path_or_buf, 'w', compression=compression)
            try:
                fh.write(s)
            finally:
                fh.close()
        elif path_or_buf is None:
            return s
        else:
            path_or_buf.write(s)

    @classmethod
    def from_json(cls, path):
        if not hasattr(path, 'read'):
            path = Path(path)
            if not path.exists():
                raise Exception("'{}' does not exists.".format(path))
            path = open(path, mode="r")

        content = json.load(path)
        return cls(**content)
