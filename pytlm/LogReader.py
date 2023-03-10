from __future__ import annotations
from typing import Iterator, List, Any
from itertools import chain
import pandas as pd
from pathlib import Path


class LogSession:
    def __init__(self, path: str, options: dict = None) -> None:
        p = Path(path)

        if p.is_dir():
            self.path = p
            self.name = self.path.resolve().name
        else:
            raise FileNotFoundError("Not a directory: %s" % path)
        
        self.__set_options(options)

        print("[pytlm] Loading log session from disk: %s" % self.name)
        self.track_sessions = list(self.__get_track_sessions())


    def __set_options(self, usr_o: dict) -> None:
        o = {}

        def set_o(key: str, def_val: Any) -> None:
            o[key] = usr_o[key] if key in usr_o else def_val

        set_o('subset', None)
        set_o('resample', False)
        set_o('resample_interval_us', 1000)
        set_o('align', False)
        self.options = o

    def __get_track_sessions(self) -> Iterator[TrackSession]:
        subset = self.options['subset']

        for x in self.path.iterdir():
            if x.is_dir() and (subset is None or x.name in subset):
                ts = TrackSession(x.resolve(), self.options)
                yield ts

    def __repr__(self) -> str:
        return self.name
    
    def __str__(self) -> str:
        return self.name


class TrackSession:
    def __init__(self, path: str, options: dict) -> None:
        p = Path(path)

        if p.is_dir():
            self.path = p
            self.name = self.path.resolve().name
        else:
            raise FileNotFoundError("Not a directory: %s" % path)

        self.options = options

        print("[pytlm]    Loading track session from disk: %s" % self.name)
        self.logs = self.__get_logs_data()

        if self.options['align']:
            self.__align_dfs()

    def __align_dfs(self):
        min_ts = max(l.index.min() for l in self.logs.values())
        max_ts = min(l.index.max() for l in self.logs.values())
        print("[pytlm] Aligning data frames only at the start. The ending timestamp is buggy.")
        self.logs = {k: l[min_ts:] for (k, l) in self.logs.items()}
        
    def __get_logs_data(self) -> dict[str, Iterator[pd.DataFrame]]:

        def csv_to_df(fname):
            df = pd.read_csv(csv_log)
            df['_timestamp'] = pd.to_datetime(df['_timestamp'], unit='us')
            df = df.drop_duplicates(subset=['_timestamp'])
            df = df.set_index('_timestamp')

            if self.options['resample']:
                ri = self.options['resample_interval_us']
                df = df.resample(str(ri) + 'us').mean().interpolate()

            return df

        result = {}
        folder_pri = self.path / 'Parsed' / 'primary'
        folder_sec = self.path / 'Parsed' / 'secondary'
        folder_gps = self.path / 'Parsed' / 'GPS'
        ignore_files = ['GPS_GGA.csv', 'GPS_NAV_HPPOSECEF.csv'] # Files with bugs/deformations

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
