from __future__ import annotations
from typing import Iterator
import pandas as pd
from pathlib import Path


class LogSession:
    def __init__(self, path: str) -> None:
        p = Path(path)

        if p.is_dir():
            self.path = p
            self.name = self.path.resolve().name
        else:
            raise FileNotFoundError("Not a directory: %s" % path)
        
        print("Loading log session from disk: %s" % self.name)
        self.track_sessions = list(self.__get_track_sessions())

    def __get_track_sessions(self) -> Iterator[TrackSession]:
        for x in self.path.iterdir():
            if x.is_dir():
                ts = TrackSession(x.resolve())
                yield ts
                return

    def __repr__(self) -> str:
        return self.name
    
    def __str__(self) -> str:
        return self.name


class TrackSession:
    def __init__(self, path: str) -> None:
        p = Path(path)

        if p.is_dir():
            self.path = p
            self.name = self.path.resolve().name
        else:
            raise FileNotFoundError("Not a directory: %s" % path)

        print("    Loading track session from disk: %s" % self.name)
        self.logs = self.__get_logs_data()

    def __get_logs_data(self) -> dict[str, Iterator[pd.DataFrame]]:
        result = {}
        folder_pri = self.path / 'Parsed' / 'primary'
        folder_sec = self.path / 'Parsed' / 'secondary'

        # Note: if files are empty, Pandas will throw an error. For some reason,
        # empty files are larger than 0 bytes, as they probably contain a newline.

        for csv_log in folder_pri.iterdir():
            if csv_log.stat().st_size > 2:
                result[csv_log.stem] = pd.read_csv(csv_log)
        for csv_log in folder_sec.iterdir():
            if csv_log.stat().st_size > 2:
                result[csv_log.stem] = pd.read_csv(csv_log)
        return result

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name