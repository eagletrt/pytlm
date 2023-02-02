# PyTLM - E-Agle Telemetry Importer

Python package to ease the import of telemetry track sessions

## Installation

For now, clone the repo and from inside it install as a local package

```shell
pip install --user .
```

## Usage

Import the package

```python
import pytlm
```

Load a log folder

```python
data = LogSession('2022_09_26_Vadena')
```

Track sessions are the different telemetry sessions

```python
print(data.track_sessions)

# [Straight line [2-step throttle + hard brake] 004, Straight line [2-step throttle + hard brake] 006, ...]
```

Each track session has a `name` string and a `logs` array of Pandas DataFrames, one for each CSV

```python
print(l.track_sessions[0].logs['STEERING_ANGLE'])

#                                 angle
# _timestamp
# 2022-12-12 13:10:17.887097  21.710159
# 2022-12-12 13:10:17.897410  21.710159
# 2022-12-12 13:10:17.907743  21.710159
# 2022-12-12 13:10:17.918736  21.710159
# 2022-12-12 13:10:17.928678  21.710159
# ...                               ...
# 2022-12-12 13:11:51.148411   7.647659
# 2022-12-12 13:11:51.159656   7.647659
# 2022-12-12 13:11:51.170396   7.647659
# 2022-12-12 13:11:51.181272   7.647659
# 2022-12-12 13:11:51.192226   7.647659
```

## Features

- [x] Allow to load only a selected set of logs and not the entire folder tree
- [x] Use timestamps as dataframe indexes, parsed as a DateTimeIndex instead of Int64Index
- [ ] Resample dataframes at a specified frequency
- [ ] Align dataframes if first/last timestamps do not match
