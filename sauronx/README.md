# SauronX

Second-generation Sauron drivers written in Python and a little C++.

**⚠  WARNING:** This is a port that is currently missing components and needs updating.
It will not function correctly yet.

[See the docs](https://sauronx.readthedocs.io/en/stable/) for more info.
[New issues](https://github.com/dmyersturnbull/sauronx/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/sauronx/blob/master/CONTRIBUTING.md).
Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).


### Available commands

Run `sauronx` in a terminal to see this list of commands:


```
Submission subcommands:
	submit       Submit a job to SauronX
	continue     Continue an incomplete SauronX run
Special submission commands:
	incubate     Incubate a plate with SauronX locked (notifies Goldberry when done)
	prototype    Run Arduino commands interactively
	repeat       Clone a submission and run the clones at intervals
Preview subcommands:
	preview      Show a live feed from the camera with overlaid ROI
	snapshot     Capture a single frame and overlay the ROI
Test commands:
	test         Run a test battery
	check        Run hardware checks
Data/cleanup subcommands:
	data         Show the local output data with history/status info
	clean        Same as 'data', but prompt to delete each directory
	ls           Simply list the local output dirs
Lookup/status subcommands:
	lookup       List something from Valar
	identify     Identify a submission and show its history
	log          See SauronX run history for this Sauron
	status       Return info about running SauronX jobs
	version      Just show the SauronX version
	info         Show extended info about SauronX, including config
Other subcommands:
	modify       Record changes to SauronX hardware or camera settings
	update       Update the SauronX codebase to the latest stable release
	unlock       Forcibly unlocks SauronX
	clear        Forcibly removes items from the list of submissions being processed
```

 If you need help with a particular command, run it with `--help`. For example:

 ```
 sauronx repeat --help
 ```


### How data progresses

After you start your submission with `sauronx submit`, your data goes through these stages:
1. An output directory is made under `~/sauronx-output`.
2. The camera connects, and the ROI is shown. (~1 minute)
3. The frames are captured and saved to `.raw` files. (length of battery)
4. Timing information (when the frames were captured) is extracted. (~1 minute)
5. The camera is disconnected, releasing the SauronX lock (described below).
6. The frames are trimmed to the exact bounds of the battery and converted to an HEVC `.mkv` video, and the raw
   frames are deleted. (~5 minutes)
7. The data are uploaded to Valinor (the server). (~5 minutes)
8. [Valar-dagger](https://github.com/dmyersturnbull/valar-dagger) queues the job.
9. When ready, it inserts the data as a _run_ into Valar. (~1 minute)
10. Features are automatically calculated on the data. (~10 minutes)
11. Valar-dagger transfers the data to the archive server.

You’ll see an error message within 30 seconds if your submission doesn’t start. If it fails or was cancelled before the
camera was disconnected, the data is probably not usable. If it failed after that but before it was uploaded,
you can fix it with `sauronx continue`. If it failed on insertion, ask Goldberry or Douglas.


### The SauronX lock

SauronX has a locking mechanism to prevent conflicts between concurrent tasks that use the camera, sound, or Arduino.

You’ll see this message in bright black when the lock is engaged:

> SauronX lock acquired. You cannot run submit, prototype, or preview until it’s released.

Only some tasks are locking: A lock is needed to submit a run, preview, take a snapshot, or prototype.
When the lock is engaged, you cannot re-engage it until it’s unlocked. When it’s unlocked you can submit another
locking job.

For submissions, the lock is acquired when you start a job and maintained through dark acclimation, running the battery,
and extracting camera timestamps.
After this finishes, the lock is released. A lock is not required for extracting or compressing frames, or uploading
the results and is never used by `sauronx continue`.
An advantage is that you can run a new job as soon as you see this message:

> SauronX lock released. You can now run any SauronX command.

However, until SauronX completely finishes and exists, you must run a new job in a new tab. **Pressing `CTRL-C` will
cancel the job, potentially losing data.**
Specifically, _data will be unrecoverable if you cancel before the lock is released._ You shouldn’t usually need to
cancel because SauronX will exit if it encounters an error.

If you confirm that SauronX is incorrectly locked, you can run `sauronx unlock`.

Along with the global lock are per-submission locks that prevent running two commands simultaneously on a single
submission (notably `submit` and `continue`).
You can remove incorrect submission locks with `sauronx clear`.


### Monitoring runs

Although SauronX does not require confirming the ROI, you need to monitor the progress of submitted jobs.
You don’t need to watch the whole run, but take note of errors:
_If SauronX exits or unlocks before the lock is both acquired and released, your job did not complete._
Red text will be shown if there was an error, and green text if it completed.


### Making changes to hardware

**If you make ANY HARDWARE CHANGE, you MUST run `sauronx modify`** to reflect the changes.

The punishment for failing to do this is a warning followed by the death penalty.
This includes changes to hardware settings in the TOML file, particularly camera settings.
It’s trivial:

```
sauronx modify "I rotated the stage counterclockwise."
```


### Submitting SauronX jobs

1. Visit https://valinor.ucsf.edu and create a SauronX run, which will give you a unique 12-digit hexadecimal number
called a SauronX _submission hash_.
2. Close the door and run `sauronx submit 03c6f1da951e`, filling in your hexadecimal number.
3. You should confirm that the image shown looks fine and has the correct ROI. Cancel the job if it doesn’t.

You can show the ROI preview without submitting a job to SauronX using `sauronx preview`.
After the submission has completed, please flip the notecard back.


### Fixing mistakes

This section assumes you have [valar-bot](https://github.com/dmyersturnbull/valar-bot) installed.

If you leave the plate in before running, you can use `sauronx submit <hash> --dark "2min"` to force SauronX to use
2 minutes of dark acclimation instead.
In this case, the original value for dark acclimation will be stored in Valar.

If you made a mistake dosing or really anywhere else, find your submission on Valinor’s homepage and
add an appropriate concern: A _to_fix_ concern for resolvable issues or an appropriate level for unresolvable ones.

If the concern is resolvable (_to_fix_), then anytime (before, during, or after the run, or during or after the insertion):

1. Make a fixed submission on valinor.ucsf.edu.

2. Ask [Goldberry](https://github.com/dmyersturnbull/valar-bot) to replace the old submission with the new one:

    > @goldberry replace 39ca0d0bh342 with 03c93740a37c

This will rename _39ca0d0bh342_ (old) to _see:0d0bh342_ and _03c93740a37c_ (new) to _39ca0d0bh342_.
For certain serious issues, you may also want to hold off inserting your data and calculating features first:

    > @goldberry hold off on 39ca0d0bh342
    > some time goes by...
    > @goldberry replace 39ca0d0bh342 with 03c93740a37c
    > @goldberry resume 03c93740a37c

Note: You can also use SauronX has a `--todo` argument, which is now deprecated. Feel free to use it,
but you must also add a concern on Valinor.

### Cleaning

SauronX stores data locally and then uploads. The local data can take a lot of storage if they’re not periodically removed.
A good tool for this is `sauronx clean`. In the simplest use, just type `sauronx clean` and follow the instructions.
For each submission, you’ll:
1. Be asked how to handle any warnings.
2. Be asked how to handle the whole submission itself.

The following will always be shown, in order:
- some metadata
- warnings about disk usage or unnecessary data
- what data are stored in the directory
- a history of running that submission
- a _verdict_
- a _recommendation_

The default action (pressing enter) is always to ignore. Here is example output for an entry that is best to deal with
immediately because it won’t be inserted and is using 45G of disk space.

```
Length (s)      0h, 28m, 40s
User            darya
Best stage      cancelled
Path            /Users/user/sauronx-output/S1/712b95df036a
Run             -
Project         darya: retest: x-31
Warning: The compression failed, leaving raw frames. This is using 45 GB of disk space.
+local storage------+--------------+
| stage             | file exists? |
+-------------------+--------------+
| checksum          |              |
| compressed frames |              |
| extracted frames  |              |
| timing info       | ✔            |
| raw video         | ✔            |
+-------------------+--------------+
+full run history----+---------------------+
| status    | sauron | run datetime        |
+-----------+--------+---------------------+
| cancelled | 1      | 2017-12-15 14:55:36 |
+-----------+--------+---------------------+

The verdict: SauronX failed, but the capture completed successfully.
Fix it by running 'sauronx continue /Users/davidkokel/sauronx-output/S1/779b9f34036a'

[Enter nothing to ignore, 'fix' (RECOMMENDED), 'trash', or 'mv' <dir>] ►►
```

Make sure to empty the trash if you need the storage immediately. You can also show only some data. For example:

```
sauronx clean --user douglas --status failed
```

Run `sauronx clean --help` to see all of the options. If you’re confident, you can run `sauronx clean --auto` to
automatically handle the outputs with the recommended actions.

Fixing an issue by writing _fix_ is equivalent to running `sauronx continue` on that submission.
When a raw AVI file exists, this will temporarily nearly double the storage that the submission uses.
SauronX does not make sure that you have sufficient storage to run `continue` and `submit` simultaneously or multiple
`continue` commands simultaneously.
You need to check this, and failing to do so can cause data loss if `submit` is being run and can render the Sauron
unresponsive until data is deleted.
You can check which SauronX commands are running (even from remote users) using `sauron status`.
If a Sauron iMac runs out of storage completely, you can copy data to an external drive, delete the original data
after the transfer, and run `sauronx clean` on the path on the external drive.


### The TOML file

The configuration for each Sauron is stored in a [TOML](https://github.com/toml-lang/toml) file under
`config/sauron<id>.toml`
You can type `subl $SAURONX_CONFIG` to open it in Sublime or `atom $SAURONX_CONFIG` to open it in Atom.
Most sections will not be changed. The camera configuration is under `[sauron.hardware.camera]`.
You can change the exposure, framerate, or ROI here.

**If you make ANY CHANGE HERE (or any hardware change), you MUST run `sauronx modify`.**

In addition to inserting a `sauron_config` into Valar, `sauronx modify` edits these two definitions:
- `last_modification_datetime`
- `most_recent_modification_description`


### Fixing the ROI

If the ROI looks wrong, you should run `sauronx preview`. If you are using a nonstandard plate type,
find the ID of the correct plate type with `sauronx lookup plate_types`.
Then run `sauronx --plate-type 1`, replacing `1` with your plate type ID or name.
Then open the appropriate TOML file in a text editor (see the section on TOML files above).
Scroll down to the section labeled `[sauron.roi.1]`, replacing `.1` with your plate type ID for nonstandard plates.
Edit the values `x0`, `x1`, `y0`, `y1`, `padx` and `pady` as needed†.
The preview should update as soon as you save the file.
If the full image is out of bounds, edit the section `[sauron.hardware.camera.plate.1]` (replacing the plate type ID).

† These values must contain a decimal point. Add _.0_ for round numbers.

The plate type you’re running with must be defined in the TOML, or SauronX will fail.
If you’re running with a new plate type, add these new sections and fix them with `sauronx preview` (as above):

- `[sauron.hardware.camera.plate.plate_type_id]`
- `[sauron.roi.plate_type_id]`

The `plate_type_id` must match the ID of the `plate_types` row in Valar. To find it, run `sauronx lookup plate_types`.


### Testing

SauronX has two main testing commands:
- `sauronx test` runs a ~1 minute test battery that uses each stimulus and stores the data locally.
- `sauronx check` uses sensors to check that stimuli cause expected changes in the readings.


### Ad-hoc assays

You can run ad-hoc assays with `sauronx prototype`. This will give you a console with commands like:

- `set pLED 0`
- `set pLED 255`
- `pulse rLED 10`
- `strobe rLED 1 10 255`
- `play soft_tap`
- `run battery "test: short comprehensive"`
- `run assay "test: single tap"`
- `fiat lux`
