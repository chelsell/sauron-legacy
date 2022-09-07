"""
Data frames describing the application of stimuli in assays.
"""
from __future__ import annotations

from binascii import hexlify

from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *


class InsightFrame(TypedDf):
    """
    A Pandas DataFrame that with one row per change to a stimulus over time.
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(_required_columns=["value", "start_ms", "end_ms"])


class AppFrame(TypedDf):
    """
    A DataFrame that stores the intersection of a stimulus and an assay as rows.
    For example, imagine a battery with two assays:
        - 'blue': a 1-second solid red light
        - 'red-tap': a red light with hard taps

    The AppFrame will have three rows:
        - assay: 'blue',      stimulus: 'blue LED',   start_ms:0
        - assay: 'red-tap',   stimulus: 'red LED',    start_ms:1000
        - assay: 'red-tap',   stimulus: 'solenoid',   start_ms:1000

    Has columns:
        - 'sf_id': stimulus_frames ID
        - 'ap_id': assay_positions ID
        - 'stimulus': name
        - 'color': hex
        - 'assay': name
        - 'simplified_name': a simplified name of the assay
        - 'start_ms'
        - 'end_ms'
        - 'n_ms'
        - 'start_stimframe'
        - 'end_stimframe'
        - 'frames_sha1':
        - 'frames': A numpy array of uint8s

    """

    @classmethod
    def of(cls, battery: Union[AppFrame, Batteries, int, str, pd.DataFrame]) -> AppFrame:
        if isinstance(battery, AppFrame):
            return battery
        if isinstance(battery, pd.DataFrame):
            battery.__class__ = AppFrame
            # noinspection PyTypeChecker
            return battery
        return AppFrame(AppFrame._frame_df(battery))

    @classmethod
    def get_typing(cls) -> DfTyping:
        DfTyping(
            _required_columns=[
                "sf_id",
                "ap_id",
                "stimulus",
                "color",
                "assay",
                "simplified_name",
                "start_ms",
                "end_ms",
                "n_ms",
                "start_stimframe",
                "end_stimframe",
                "frames_sha1",
                "frames",
            ]
        )

    def ms_off(self, any_of_stimuli: Union[str, Sequence[str]]) -> Sequence[int]:
        return self.ms_on(any_of_stimuli, lambda x: x == 0)

    def ms_on(
        self,
        any_of_stimuli: Union[str, Sequence[str]],
    ) -> Sequence[int]:
        return self._ms_on(any_of_stimuli, lambda x: x > 0)

    def _ms_on(
        self, any_of_stimuli: Union[str, Sequence[str]], accept_value: Callable[[int], bool]
    ) -> Sequence[int]:
        if isinstance(any_of_stimuli, str):
            any_of_stimuli = [any_of_stimuli]
        bits = []
        for i, row in enumerate(self.itertuples()):
            if row.stimulus in any_of_stimuli:
                insight = self.insight_at_index(i)
                for r in insight.itertuples():
                    if accept_value(r.value):
                        bits.append(range(r.start_ms, r.end_ms))
        return [i for j in bits for i in j]

    def by_stimulus(self, stimulus: Union[str, int, Stimuli]) -> AppFrame:
        stimulus = stimulus if isinstance(stimulus, str) else Stimuli.fetch(stimulus).name
        return AppFrame.of(self[self["stimulus"] == stimulus].reset_index(drop=True))

    def by_start_ms(self, start_ms: int) -> AppFrame:
        return AppFrame.of(self[self["start_ms"] == start_ms].reset_index(drop=True))

    def by_assay(self, assay: Union[str, int, Assays]) -> AppFrame:
        assay = assay if isinstance(assay, str) else Assays.fetch(assay).name
        return AppFrame.of(self[self["assay"] == assay].reset_index(drop=True))

    def slice_ms(self, start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> AppFrame:
        if start_ms is None:
            start_ms = 0
        if end_ms is None:
            end_ms = self["end_ms"].max()
        z = self[self["start_ms"] >= start_ms]
        z = z[z["end_ms"] <= end_ms]
        return AppFrame.of(z.reset_index(drop=True))

    def insight_at_index(self, index: int) -> InsightFrame:
        """
        Generates something like template_stimulus_frames for legacy protocols and assays.

        Args:
            index: A row index, starting at 0

        Returns:
          A DataFrame of start, end, and value for changes

        """
        z = self.iloc[index]
        return AppFrame._insight(z).sort_values("start_ms")

    def insight(self) -> InsightFrame:
        """
        Generates something like template_stimulus_frames for legacy or SauronX batteries and assays.

        Returns:
            A DataFrame of start, end, and value for changes
        """
        concat = pd.concat([AppFrame._insight(z) for z in self.itertuples()], sort=False)
        return InsightFrame(InsightFrame.convert(concat.sort_values("start_ms")))

    @classmethod
    def _insight(cls, frames_row: pd.Series) -> InsightFrame:
        ms_per_stimframe = ValarTools.assay_ms_per_stimframe(frames_row.assay)
        df = pd.DataFrame(AppFrame._provide(frames_row, ms_per_stimframe))
        df["value"] = df["value"].astype(np.int32)
        df["start_ms"] = df["start_ms"].astype(np.int32)
        df["end_ms"] = df["end_ms"].astype(np.int32)
        df["n_ms"] = df["end_ms"] - df["start_ms"]
        # df['ap_id'] = df['ap_id'].astype(np.int32)
        # df['sf_id'] = df['sf_id'].astype(np.int32)
        return InsightFrame(InsightFrame.convert(df))

    @classmethod
    def _provide(cls, frames_row: pd.Series, ms_per_stimframe: int) -> Iterator[pd.Series]:
        insight = AppFrame._frames_insight(frames_row.frames, 1 / ms_per_stimframe)
        for i in range(0, len(insight)):
            prev = int(insight["start_ms"].iloc[i] + frames_row.start_ms)
            if i == len(insight) - 1:
                nxt = len(frames_row.frames) * ms_per_stimframe + frames_row.start_ms
            else:
                nxt = int(insight["start_ms"].iloc[i + 1] + frames_row.start_ms)
            s = pd.Series(
                {
                    "stimulus": frames_row.stimulus,
                    "assay": frames_row.assay,
                    "sf_id": int(frames_row.sf_id),
                    "ap_id": int(frames_row.ap_id),
                    "start_ms": prev,
                    "end_ms": nxt,
                    "value": insight["value"].iloc[i],
                }
            )
            yield s

    @classmethod
    def _frames_insight(cls, arr: np.array, framerate: float) -> pd.DataFrame:
        last_v = -1
        changes = []
        for i, v in enumerate(arr):
            if v != last_v:
                changes.append((i, v))
                last_v = v
        df = pd.DataFrame(
            [pd.Series({"start_ms": int(i / framerate), "value": v}) for i, v in changes]
        )
        return UntypedDf(df).cfirst(["start_ms", "value"])

    @classmethod
    def _frame_df(cls, battery: Union[int, str, Batteries]) -> pd.DataFrame:
        battery = Batteries.fetch(battery)
        positions = list(
            AssayPositions.select(AssayPositions, Assays)
            .join(Assays)
            .where(AssayPositions.battery_id == battery.id)
        )
        assays = {ap.assay_id for ap in positions}
        stimframes = list(
            StimulusFrames.select(StimulusFrames, Stimuli, Assays)
            .join(Stimuli)
            .switch(StimulusFrames)
            .join(Assays)
            .where(Assays.id << assays)
        )
        assays_to_stimframes = {a: [] for a in assays}
        for sf in stimframes:
            assays_to_stimframes[sf.assay_id].append(sf)
        lst = []
        for ap in positions:
            a = ap.assay
            for sf in assays_to_stimframes[ap.assay_id]:
                s = sf.stimulus
                lst.append(
                    [
                        sf.id,
                        ap.id,
                        s.name,
                        ValarTools.stimulus_display_color(s),
                        a.name,
                        ValarTools.simplify_assay_name(a.name),
                        ValarTools.assay_ms_per_stimframe(a.name) * ap.start,
                        ValarTools.assay_ms_per_stimframe(a.name) * (ap.start + a.length),
                        ValarTools.assay_ms_per_stimframe(a.name) * a.length,
                        ap.start,
                        ap.start + a.length,
                        hexlify(sf.frames_sha1).decode("utf8"),
                        Tools.jvm_sbytes_to_ubytes(sf.frames),
                    ]
                )
        df = pd.DataFrame(
            lst,
            columns=[
                "sf_id",
                "ap_id",
                "stimulus",
                "color",
                "assay",
                "simplified_name",
                "start_ms",
                "end_ms",
                "n_ms",
                "start_stimframe",
                "end_stimframe",
                "frames_sha1",
                "frames",
            ],
        )
        if len(df) == 0:
            logger.warning(f"Battery {battery.name} has no stimulus frames")
        return df.sort_values("start_ms").reset_index(drop=True)


__all__ = ["AppFrame"]
