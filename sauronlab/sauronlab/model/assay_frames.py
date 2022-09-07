"""
Dataframes listing assays in batteries.
"""

from __future__ import annotations

from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *


class AssayFrame(TypedDf):
    """
    A Pandas DataFrame that has one row per assay in a battery.

    Each row has:
        - assay_positions ID,
        - assay name
        - simplified assay name
        - start time
        - end time
    """

    @classmethod
    def of(cls, df, *args, **kwargs) -> AssayFrame:
        if isinstance(df, (Batteries, int, str)):
            return super().of(cls._assay_df(df))
        return super().of(df)

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(
            _required_columns=[
                "position_id",
                "assay_id",
                "name",
                "simplified_name",
                "start_ms",
                "end_ms",
                "n_ms",
                "start",
                "end",
                "duration",
            ]
        )

    @classmethod
    def _assay_df(cls, battery: Union[int, str]) -> pd.DataFrame:
        battery = Batteries.fetch(battery)
        query = (
            AssayPositions.select(AssayPositions, Assays, StimulusFrames, Stimuli, Batteries)
            .join(Assays)
            .join(StimulusFrames, JOIN.LEFT_OUTER)
            .join(Stimuli, JOIN.LEFT_OUTER)
            .switch(AssayPositions)
            .join(Batteries)
            .where(Batteries.id == battery.id)
        )
        assay_positions = pd.DataFrame(
            [
                pd.Series(
                    {
                        "position_id": ap.id,
                        "assay_id": ap.assay.id,
                        "name": ap.assay.name,
                        "simplified_name": ValarTools.simplify_assay_name(ap.assay.name),
                        "start_ms": ValarTools.assay_ms_per_stimframe(ap.assay) * ap.start,
                        "end_ms": ValarTools.assay_ms_per_stimframe(ap.assay)
                        * (ap.start + ap.assay.length),
                    }
                )
                for ap in query
            ]
        )
        df = assay_positions.drop_duplicates().sort_values("start_ms")
        df["start"] = df["start_ms"].map(Tools.ms_to_minsec)
        df["end"] = df["end_ms"].map(Tools.ms_to_minsec)
        df["n_ms"] = df["end_ms"] - df["start_ms"]
        df["duration"] = (df["end_ms"] - df["start_ms"]).map(Tools.ms_to_minsec)
        return df.reset_index()


__all__ = ["AssayFrame"]
