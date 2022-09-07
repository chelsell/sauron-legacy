import scipy.interpolate as interp

from sauronlab.core.core_imports import *


class InterpolationFailedError(AlgorithmError):
    def __init__(self, msg: str, feature: str, well: int):
        super().__init__(msg)
        self.feature = feature
        self.well = well


class FeatureTimestampMismatchError(InterpolationFailedError):
    def __init__(self, feature: str, well: int, n_features: int, n_timestamps: int, n_ideal: int):
        feature = Features.fetch(feature).name
        msg = f"Could not interpolate {feature}: {n_features} features != {n_timestamps} timestamps; ideal is {n_ideal}"
        super().__init__(msg, feature, well)
        self.n_features = n_features
        self.n_timestamps = n_timestamps
        self.n_ideal = n_ideal


class FeatureInterpolation:
    def __init__(self, feature: Features):
        self.feature = feature

    def interpolate(
        self,
        feature_arr: np.array,
        frame_timestamps: np.array,
        stim_timestamps: np.array,
        well: Union[int, Wells],
        stringent: bool = False,
    ) -> np.array:
        """
        Interpolates a time-dependent, frame-by-frame feature for a well using timestamps.
        This is appropriate for PointGrey camera data or other data with nanosecond or microsecond-resolved timestamps from the image sensor.
        This is not appropriate if the timestamps are not when the image was captured, or are too poorly resolved.
        Calls TimeSeriesFeatureTools.interpolate_features; see that function for more info.

        Args:
            feature_arr: The array of the feature; not affected
            frame_timestamps:
            stim_timestamps:
            well: The well instance or ID
            stringent: Raise exceptions for small errors

        Returns:
            The interpolated features
        """
        run = Wells.fetch(well).run
        ideal_framerate = ValarTools.frames_per_second(run)
        battery = run.experiment.battery
        actual_battery_start_ms, actual_battery_stop_ms = stim_timestamps[0], stim_timestamps[-1]
        expected_stop_ms = actual_battery_start_ms + battery.length
        # differs by >= than 2 frames
        if abs(actual_battery_stop_ms - expected_stop_ms) >= 2 * 1000 / ideal_framerate:
            msg = "Run {} has recorded stop time {} but start time + battery length = {} + {} = {} (diff {}ms)".format(
                run,
                actual_battery_stop_ms,
                actual_battery_start_ms,
                battery.length,
                expected_stop_ms,
                actual_battery_stop_ms - expected_stop_ms,
            )
            if stringent:
                raise RefusingRequestError(msg)
            else:
                logger.debug(msg)
        frames_ms = frame_timestamps[
            (frame_timestamps >= actual_battery_start_ms) & (frame_timestamps <= expected_stop_ms)
        ]
        return self._interpolate(
            feature_arr,
            frames_ms,
            actual_battery_start_ms,
            expected_stop_ms,
            ideal_framerate,
            well,
            stringent,
        )

    def _interpolate(
        self,
        feature_arr: np.array,
        frames_ms: np.array,
        battery_start_ms: int,
        battery_stop_ms: int,
        ideal_framerate: int,
        well: int,
        stringent: bool,
    ) -> np.array:
        """
        Interpolates a time-dependent, frame-by-frame feature using timestamps.
        See exterior_interpolate_features for a simpler way to call this and for more info.
        Interpolates using scipy.interpolate.interp1d with kind='previous', fill_value='extrapolate', bounds_error=False, and assume_sorted=True

        Args:
            feature_arr: The array of the feature; not affected
            frames_ms: The millisecond timestamps, which can be float-typed.
                       This is NOT set to start with the battery start.
                       However, the milliseconds for battery_start, battery_end,
                       and frames_ms must all be with respect to a single (unspecified) start time.
                       This will normally be the the start time of the run.
            battery_start_ms: The millisecond at which the battery started (see ``frames_ms``)
            battery_stop_ms: The millisecond at which the battery finished (see ``frames_ms``)
            ideal_framerate: The framerate that was set in the camera config.
                             The interpolation will use this to determine the resulting number of frames.
            well: TODO
            stringent: TODO
        """
        # Later we want to have logic that checks that it makes sense to interpolate--we don't want to interpolate if there are problematic gaps
        # diffs = np.diff(frames_ms)
        # empirical_framerate = 1000 / np.mean(diffs)
        ideal_step = 1000 / ideal_framerate
        new_time = np.arange(start=battery_start_ms, stop=battery_stop_ms, step=ideal_step)

        # if len(new_time) == len(feature_arr):
        #     return feature_arr
        if abs(len(frames_ms) - len(feature_arr)) > (0 if stringent else 100 * ideal_step):
            raise FeatureTimestampMismatchError(
                self.feature, well, len(feature_arr), len(frames_ms), len(new_time)
            )
        elif abs(len(frames_ms) - len(feature_arr)) > 0:
            # if it's off by 1, let's trim either to fix it
            if len(frames_ms) < len(feature_arr):
                feature_arr = feature_arr[: len(frames_ms)]
            else:
                frames_ms = frames_ms[: len(feature_arr)]

        # this breaks with linear interpolation!
        try:
            feature_interp = interp.interp1d(
                frames_ms,
                feature_arr,
                kind="previous",
                fill_value=(np.NaN, np.NaN),
                bounds_error=False,
                assume_sorted=True,
            )
        except BaseException as e:
            raise InterpolationFailedError(
                f"Failed calling interp1d on {self.feature} for well {well}", self.feature, well
            ) from e
        return feature_interp(new_time)


__all__ = ["FeatureInterpolation", "InterpolationFailedError", "FeatureTimestampMismatchError"]
