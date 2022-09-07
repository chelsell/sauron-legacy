from sauronlab.core.core_imports import *
from sauronlab.model.audio import Waveform


class WaveformEmbedding:
    """"""

    @classmethod
    def expand(
        cls,
        stimseries: pd.Series,
        stim: Union[Stimuli, str, int],
        waveform: Waveform,
        is_legacy: bool,
    ) -> np.array:
        """
        Embeds a waveform into a stimframes array.

        Args:
            stimseries:
            stim:
            waveform:
            is_legacy:

        Returns:

        """
        stim = Stimuli.fetch(stim)
        logger.info(f"Expanding audio on {stim.name}{'(legacy)' if is_legacy else ''}")
        form = (
            waveform.standardize(50.0, 200.0, ms_freq=ValarTools.LEGACY_STIM_FRAMERATE)
            if is_legacy
            else waveform.standardize(50.0, 200.0, ms_freq=1000)
        )
        if isinstance(stimseries, pd.Series):
            # https://github.com/numpy/numpy/issues/15555
            # https://github.com/pandas-dev/pandas/issues/35331
            stimseries = stimseries.values
        # noinspection PyTypeChecker
        starts = np.argwhere(stimseries > 0)
        built = []
        # TODO this could definitely be sped up
        i = 0
        for start in starts:
            # if the audio is a block format, start will often be less than i, which is OK
            if i == 0 or start >= i:
                if start < i:
                    raise AlgorithmError(f"Frame {start} went off the edge")
                built.append(np.zeros(start - i))
                built.append(form.data)
                i = start + len(form.data)
        built.append(np.zeros(len(stimseries) - i))
        return np.concatenate(built)


__all__ = ["WaveformEmbedding"]
