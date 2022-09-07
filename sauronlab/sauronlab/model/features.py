from dataclasses import dataclass

from sauronlab.calc.feature_interpolation import *
from sauronlab.core.core_imports import *


@dataclass(frozen=True)
class FeatureType:
    """

    Attributes:
        valar_feature: The Features row instance in Valar
        time_dependent: Whether the feature corresponds to frames in the video (possibly differing by a constant)
        stride_in_bytes: The number of bytes (in the poorly named features.floats) per value, such as 8 for a double value
        recommended_scale: A multiplier of the values for display, such as 1000 for values on that order
        recommended_unit: An arbitrary string to label units with; should account for the recommended_scale
        is_interpolated: For time-dependent features, whether the feature is interpolated to align with the timesamps.
                         This is generally a good idea for PointGrey+ features, and a bad idea for cameras with less accurate timestamps.
        generations: Generations of video data this feature can apply to.
    """

    valar_feature: Features
    time_dependent: bool
    stride_in_bytes: int
    recommended_scale: int
    recommended_unit: str
    is_interpolated: bool
    generations: Set[DataGeneration]

    @property
    def internal_name(self):
        return self.valar_feature.name + ("-i" if self.is_interpolated else "")

    @property
    def external_name(self):
        return self.valar_feature.name + ("[⌇]" if self.is_interpolated else "")

    @property
    def dtype(self):
        """
        The data type of the *final* calculated feature; e.g. ``np.float32``.
        """
        raise NotImplementedError()

    def calc(
        self,
        wf: WellFeatures,
        frame_timestamps: Optional[np.array],
        stim_timestamps: Optional[np.array],
        well: Union[Wells, int],
        stringent: bool = False,
    ) -> np.array:
        """
        Calculates the feature values.

        Args:
            wf: WellFeatures:
            frame_timestamps: Required if is_interpolated
            stim_timestamps: Required if is_interpolated
            well:
            stringent:

        Returns:

        """
        if self.is_interpolated and (frame_timestamps is None or stim_timestamps is None):
            raise ValueError(
                f"frame_timestamps and stim_timestamps must be non-None for interpolated feature ${self.internal_name}"
            )
        if well is None and wf is not None:
            well = wf.well
        elif well is not None and wf is None:
            wf = (
                WellFeatures.select()
                .where(WellFeatures.well == well)
                .where(WellFeatures.type == self.valar_feature)
                .first()
            )
            if wf is None:
                raise ValarLookupError(f"No feature {self.valar_feature.name} for well {well}")
        return self.from_blob(
            wf.floats, frame_timestamps, stim_timestamps, well, stringent=stringent
        )

    @abcd.abstractmethod
    def to_blob(self, arr: np.array) -> None:
        """"""
        raise NotImplementedError()

    @abcd.abstractmethod
    def from_blob(
        self,
        blob: bytes,
        frame_timestamps: np.array,
        stim_timestamps: np.array,
        well: Union[Wells, int],
        stringent: bool = False,
    ) -> np.array:
        """
        Converts a blob from the database into a numpy array.

        Args:
            blob: byte
            well: Preferably the ``Wells`` instance; but can be a well ID (performs a query in that case)
            frame_timestamps: The timestamps from the camera
            stim_timestamps: The timestamps of the stimuli
            stringent: Raises an error for minor problems, rather than warning

        Returns:
            A numpy array
        """
        raise NotImplementedError()

    def __repr__(self):
        return self.valar_feature.name + ("[⌇]" if self.is_interpolated else "")

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return isinstance(other, FeatureType) and other.internal_name == self.internal_name

    def __hash__(self):
        return hash(self.internal_name)


class _ConsecutiveFrameFeature(FeatureType, metaclass=abcd.ABCMeta):
    """"""

    @classmethod
    def finalize_floats(cls, floats: np.array) -> np.array:
        """
        Performs last-minute modifications to the floats the end of ``calc``, right before it returns.
        Args:
            floats: Raw data converted from the blob; could be float16, float32, int32, ..., whatever.

        Returns:
            A numpy array, possibly rescaled and converted to a different dtype.
        """
        raise NotImplementedError()

    @classmethod
    def definalize_floats(cls, floats: np.array) -> np.array:
        """
        Inverts ``finalize_floats``; called in ``to_blob``.
        """
        raise NotImplementedError()

    def from_blob(
        self,
        blob: bytes,
        frame_timestamps: Optional[np.array],
        stim_timestamps: Optional[np.array],
        well: Union[Wells, int],
        stringent: bool = False,
    ) -> np.array:
        well = Wells.fetch(well)
        if len(blob) == 0:
            logger.warning(f"Empty {self.valar_feature.name} feature array for well {well.id}")
            # TODO: Is it fair to use float32 here?
            return np.empty(0, dtype=np.float32)
        floats = Tools.blob_to_signed_floats(blob)
        floats.setflags(write=1)  # blob_to_floats gets read-only arrays
        # Previously, MI at t=0 was defined to be 0. Since Valar2, it's defined to be NaN.
        # This won't affect visualization but could affect analysis, so let's always set it to be 0.
        floats[0] = 0.0
        if self.is_interpolated:
            return FeatureInterpolation(self.valar_feature).interpolate(
                floats, frame_timestamps, stim_timestamps, well, stringent=stringent
            )
        return self.__class__.finalize_floats(floats)


class _Float16Div8Cff(_ConsecutiveFrameFeature):
    """
    These have a pretty specific property: they can be converted to float16 by dividing by 8.
    These are float32 in the database but can be encoded in float16 by division by 8.0.
    So, we perform that division to save memory and size of cached data.
    """

    @property
    def dtype(self):
        return np.float16

    @classmethod
    def finalize_floats(cls, floats: np.array) -> np.array:
        return (floats / 8.0).astype(np.float16)

    @classmethod
    def definalize_floats(cls, floats: np.array) -> np.array:
        return floats.astype(np.float32) * 8.0

    def to_blob(self, arr: np.array) -> bytes:
        rescaled = self.__class__.definalize_floats(arr)
        return Tools.signed_floats_to_blob(rescaled)


class _Mi(_Float16Div8Cff):
    """"""

    def __init__(self, interpolated: bool):
        v = Features.select().where(Features.name == "MI").first()
        super().__init__(v, True, 4, 1000, "(10³)", interpolated, DataGeneration.all_generations())


class _Diff(_Float16Div8Cff):
    """"""

    def __init__(
        self, name: str, tau: int, recommended_scale: int, recommended_unit: str, interpolated: bool
    ):
        v = Features.select().where(Features.name == f"{name}({tau})").first()
        generations = (
            DataGeneration.pointgrey_generations()
            if interpolated
            else DataGeneration.all_generations()
        )
        super().__init__(
            v, True, 4, recommended_scale, recommended_unit, interpolated, generations=generations
        )


class FeatureTypes:
    """
    The feature types in valar.features.
    """

    MI = _Mi(False)
    cd_10 = _Diff("cd", 10, 1, "", False)
    MI_i = _Mi(True)
    cd_10_i = _Diff("cd", 10, 1, "", True)
    known = [MI, cd_10, MI_i, cd_10_i]

    @classmethod
    def of(cls, f: Union[FeatureType, str]) -> FeatureType:
        """
        Fetches a feature from its **internal** name.

        Args:
            f: A value in FeatureType.internal_name in one of the FeatureType entries in ``FeatureTypes.known``

        Returns:
            The FeatureType

        """
        if isinstance(f, Features):
            raise TypeError(
                "Can't get FeatureType by Valar Features row because it's ambiguous."
                "Get the feature type explicitly using FeatureTypes._ ."
            )
        if not isinstance(f, (FeatureType, str)):
            raise TypeError(f"Can't get FeatureType by type {type(f)}")
        if isinstance(f, FeatureType):
            return f
        for v in FeatureTypes.known:
            if v.internal_name == f:
                return v
        raise ValarLookupError(f"No feature {f}")


__all__ = ["FeatureType", "FeatureTypes"]
