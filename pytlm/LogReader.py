from __future__ import annotations
from typing import Iterator, List
from itertools import chain
import pandas as pd
from pathlib import Path


class LogSession:
    def __init__(self, path: str, subset: List[str] = None) -> None:
        self.options = {

        }

        p = Path(path)

        if p.is_dir():
            self.path = p
            self.name = self.path.resolve().name
        else:
            raise FileNotFoundError("Not a directory: %s" % path)
        
        print("[pytlm] Loading log session from disk: %s" % self.name)
        self.track_sessions = list(self.__get_track_sessions(subset))

    def __get_track_sessions(self, subset: List[str] = None) -> Iterator[TrackSession]:
        for x in self.path.iterdir():
            if x.is_dir() and (subset is None or x.name in subset):
                ts = TrackSession(x.resolve())
                yield ts

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

        print("[pytlm]    Loading track session from disk: %s" % self.name)
        self.logs = self.__get_logs_data()

    def __get_logs_data(self) -> dict[str, Iterator[pd.DataFrame]]:

        def csv_to_df(fname):
            df = pd.read_csv(csv_log)
            df['_timestamp'] = pd.to_datetime(df['_timestamp'], unit='us')
            df = df.set_index('_timestamp')
            return df

        result = {}
        folder_pri = self.path / 'Parsed' / 'primary'
        folder_sec = self.path / 'Parsed' / 'secondary'
        folder_gps = self.path / 'Parsed' / 'GPS'
        ignore_files = ['GPS_GGA.csv']

        # Note: if files are empty, Pandas will throw an error. For some reason,
        # empty files are larger than 0 bytes, as they probably contain a newline.

        for csv_log in chain(folder_pri.iterdir(), folder_sec.iterdir(), folder_gps.iterdir()):
            if csv_log.stat().st_size > 2 and csv_log.name not in ignore_files:
                result[csv_log.stem] = csv_to_df(csv_log)

        return result

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


if __name__ == '__main__':
    logs = LogSession('../../CorneringSpeed/2022_12_12_Vadena', subset=['Half Skidpad CW [#1] 000']) # , 'Warmup m40 C0 [#1] 003'])
    resample_resolution_us = 1000
    print(logs.track_sessions[0].logs['STEERING_ANGLE'])
