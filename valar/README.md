
## Database information

### database organization

The database itself is split into a few pieces. To learn more about the structure, see the ERDs.
- the core behavioral tables
- the chemical annotation tables, names beginning with _mandos\__

Assay frames and features (such as MI) are stored as MySQL binary
``blob``\ s.

Each frame in ``assay_frames`` is represented as a single big-endian
unsigned byte. To convert back, use ``utils.blob_to_byte_array(blob)``,
where ``blob`` is the Python ``bytes`` object returned directly from the
database.

Each value in ``well_features`` (each value is a frame for features like
MI) is represented as 4 consecutive bytes that constitute a single
big-endian unsigned float (IEEE 754 ``binary32``). Use
``utils.blob_to_float_array(blob)`` to convert back.

There shouldn’t be a need to insert these data from Python, so there’s
no way to convert in the forwards direction.
## legacy data

You can determine which runs were run with SauronX: They have `runs.submission` set.
Data prior to this have some quirks.

- `plates.datetime_plated` will be null.
- `runs.datetime_dosed` might be null.
- `runs.datetime_run` might be wrong. Although unlikely, it could be off by a day.
- Different sensor and timing information will be available.
- Raw data is stored in a different format and under a different path.
- SauronX assays are defined for a fixed length of time, and their stimulus frames are defined in milliseconds.
  In pre-SauronX assays bytes in `stimulus_frames.frames` correspond to frames sampled at a particular framerate.
  The sampling might for a plate run might be defined in `sensor_data` for sensor `legacy-assay-milliseconds`.
  