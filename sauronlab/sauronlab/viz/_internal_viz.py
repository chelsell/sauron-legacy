import matplotlib
from matplotlib.axes import Axes
from matplotlib.colors import Colormap
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from sauronlab.core.core_imports import *
from sauronlab.core.tools import *
from sauronlab.viz import plt
from sauronlab.viz.kvrc import *

FigureSeqLike = Union[Figure, Iterator[Figure], Iterator[Tup[str, Figure]], Mapping[str, Figure]]


class InternalVizTools:
    """"""

    @classmethod
    def preferred_units_per_sec(cls, mark_every_ms: int, total_ms: float) -> Tup[str, float]:
        """


        Args:
            mark_every_ms: int:
            total_ms: float:

        Returns:

        """
        if sauronlab_rc.trace_force_time_units is not None:
            return (
                sauronlab_rc.trace_force_time_units.abbrev,
                1 / sauronlab_rc.trace_force_time_units.n_ms,
            )
        if total_ms >= sauronlab_rc.trace_min_cutoff and mark_every_ms >= 1000 * 60 * 60:
            return "hour", 1 / 60 / 60
        if total_ms >= sauronlab_rc.trace_sec_cutoff and mark_every_ms >= 1000 * 60:
            return "min", 1 / 60
        elif total_ms >= sauronlab_rc.trace_ms_cutoff and mark_every_ms >= 1000:
            return "s", 1
        else:
            return "ms", 1000

    @classmethod
    def preferred_tick_ms_interval(cls, n_ms_total):
        """


        Args:
            n_ms_total:

        Returns:

        """
        alloweds = sauronlab_rc.trace_pref_tick_ms_interval
        n_ms = n_ms_total / sauronlab_rc.trace_pref_n_ticks
        closest_choice, closest_val = None, 100000000000
        for a in alloweds:
            e = abs(a - n_ms) / a
            if e < closest_val:
                closest_choice, closest_val = a, e
        return closest_choice

    @classmethod
    def assign_colors(cls, categories: Sequence[str]) -> Sequence[str]:
        """


        Args:
            categories:

        Returns:

        """
        dct = InternalVizTools.assign_color_dict(categories)
        return [dct[c] for c in categories]

    @classmethod
    def assign_colors_x(
        cls, names: Sequence[str], controls: Sequence[Optional[str]], recycle_ok: bool = False
    ) -> Sequence[str]:
        """


        Args:
            names:
            controls:
            recycle_ok:

        Returns:

        """
        dct = InternalVizTools.assign_color_dict_x(names, controls, recycle_ok=recycle_ok)
        return [dct[c] for c in names]

    @classmethod
    def assign_color_dict_x(
        cls, names: Sequence[str], controls: Sequence[Optional[str]], recycle_ok: bool = False
    ) -> Mapping[str, str]:
        """


        Args:
            names:
            controls:
            recycle_ok:

        Returns:

        """
        dct = {}
        if len(names) != len(controls):
            raise LengthMismatchError(f"{len(names)} names but {len(controls)} controls")
        pref = iter(sauronlab_rc.pref_treatment_colors)
        control_colors = iter(sauronlab_rc.pref_control_colors)
        for name, control in Tools.zip_list(names, controls):
            if name in dct:
                continue
            if Tools.is_empty(control):
                try:
                    dct[name] = next(pref)
                except StopIteration:
                    if not recycle_ok:
                        logger.warning("Not enough treatment names. Recycling.")
                    pref = iter(sauronlab_rc.pref_treatment_colors)
                    dct[name] = next(pref)
            elif control in sauronlab_rc.pref_control_color_dict:
                dct[name] = sauronlab_rc.pref_control_color_dict[control]
            else:
                try:
                    dct[name] = next(control_colors)
                except StopIteration:
                    if not recycle_ok:
                        logger.warning("Not enough control names. Recycling.")
                    control_colors = iter(sauronlab_rc.pref_control_colors)
                    dct[name] = next(control_colors)
        dct.update({k: v for k, v in sauronlab_rc.pref_name_color_dict.items() if k in dct})
        return dct

    @classmethod
    def assign_color_dict(cls, categories: Sequence[str]) -> Mapping[str, str]:
        """


        Args:
            categories:

        Returns:

        """
        return InternalVizTools.assign(categories, sauronlab_rc.pref_treatment_colors)

    @classmethod
    def assign_markers(cls, categories: Sequence[str]) -> Sequence[str]:
        """


        Args:
            categories:

        Returns:

        """
        dct = InternalVizTools.assign_marker_dict(categories)
        return [dct[c] for c in categories]

    @classmethod
    def assign_marker_dict(cls, categories: Sequence[str]) -> Mapping[str, str]:
        """


        Args:
            categories:

        Returns:

        """
        return InternalVizTools.assign(categories, sauronlab_rc.pref_markers)

    @classmethod
    def assign(cls, categories: Sequence[str], available: Sequence[str]) -> Mapping[str, str]:
        """


        Args:
            categories:
            available:

        Returns:

        """
        unique = Tools.unique(categories)
        if len(unique) > len(available):
            logger.warning(
                f"There are {len(unique)} categories but only {len(available)} choices available"
            )
        z = OrderedDict()
        for u, m in zip(unique, itertools.cycle(available)):
            z[u] = m
        return z


class KvrcPlotting:
    """"""

    pass


__all__ = [
    "plt",
    "Axes",
    "Figure",
    "GridSpec",
    "Colormap",
    "matplotlib",
    "InternalVizTools",
    "sauronlab_rc",
    "KvrcPlotting",
    "FigureSeqLike",
]
