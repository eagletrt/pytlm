# E-Agle Telemetry Importer

Python package to ease the import of telemetry track sessions

## Usage

Import the package

```python
import tlmimporter
```

Load a log folder

```python
data = LogSession('2022_09_26_Vadena')
```

Track sessions are the different telemetry sessions

```python
print(data.track.sessions)

# [Straight line [2-step throttle + hard brake] 004, Straight line [2-step throttle + hard brake] 006, ...]
```

Each track session has a `log` array of Pandas DataFrames for each CSV

```python
print(l.track_sessions[0].logs['HV_CELLS_TEMP'])

#            _timestamp  start_index     temp_0     temp_1     temp_2     temp_3     temp_4     temp_5
# 0    1664196134689841          198  28.235294  27.843138  28.627451  28.235294  28.627451  28.235294
# 1    1664196134739434          204  27.843138  27.843138  27.058823  27.843138  28.235294  28.235294
# 2    1664196134789407          210  26.666666  27.058823  27.058823  27.450981  27.450981  27.450981
# 3    1664196134839336            0  28.235294  27.843138  27.843138  27.450981  27.450981  27.058823
# 4    1664196134889344            6  28.235294  28.627451  27.843138  28.235294  28.627451  28.235294
# ..                ...          ...        ...        ...        ...        ...        ...        ...
# 139  1664196141639534          168  27.843138 -20.000000 -20.000000  27.843138  27.843138  27.843138
# 140  1664196141689538          174 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000
# 141  1664196141739542          180 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000
# 142  1664196141840020          192 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000 -20.000000
# 143  1664196141889891          198  28.235294  27.843138  28.627451  28.235294  28.627451  28.235294
# 
# [144 rows x 8 columns]
```

## To Do

- Allow to load only a selected set of logs and not the entire folder tree