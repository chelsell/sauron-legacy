from __future__ import annotations

import matplotlib.legend as mlegend
from matplotlib import patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pocketutils.plotting.color_schemes import FancyCmaps, FancyColorSchemes

# from pocketutils.plotting.corners import Corner, Corners # Can't be found -CH
from pocketutils.plotting.fig_savers import FigureSaver
from pocketutils.plotting.fig_tools import FigureTools as _FigureTools

from sauronlab.core.core_imports import *
from sauronlab.viz._internal_viz import *


class FigureTools(_FigureTools):

    darken_palette = FancyColorSchemes.darken_palette
    darken_color = FancyColorSchemes.darken_color

    @classmethod
    @contextmanager
    def using(cls, *args, **kwargs) -> Generator[None, None, None]:
        """
        Provided for convenience as a shorthand to using both sauronlab_rc.using, Figs.hiding, and Figs.clearing.

        Args:
            args: Passed to sauronlab_rc.using
            kwargs: Passed to sauronlab_rc.using, except for 'path', 'hide', and 'clear'

        Yields:
            A context manager
        """
        path, hide, clear, reload = (
            str(kwargs.get("path")),
            bool(kwargs.get("hide")),
            bool(kwargs.get("clear")),
            bool(kwargs.get("reload")),
        )
        kwargs = {k: v for k, v in kwargs.items() if k not in {"path", "hide", "clear"}}
        with sauronlab_rc.using(*args, **kwargs):
            with cls.clearing(clear):
                with cls.hiding(hide):
                    yield

    @classmethod
    def save(
        cls,
        figure: FigureSeqLike,
        path: PathLike,
        names: Optional[Iterator[str]] = None,
        clear: bool = True,
        **kwargs,
    ) -> None:
        """
        Save a figure or sequence of figures to ``FigureSaver``.
        See that class for more info.
        """
        path = str(path).replace("/", os.sep)
        FigureSaver(clear=clear, **kwargs).save(figure, path, names=names)

    @classmethod
    def add_aligned_colorbar(
        cls, ax: Axes, mat, size: str = "5%", number_format: Optional[str] = None
    ):
        """
        Creates a colorbar on the right side of ``ax``.
        A padding of sauronlab_rc.general_colorbar_left_pad will be applied between ``ax`` and the colorbar.
        Technically description: Adds a new ``Axes`` on the right side with width ``size``%.
        If sauronlab_rc.general_colorbar_on is False, will add the colorbar and make it invisible.
        (This is weirdly necessary to work around a matplotlib bug.)

        Args:
            ax: The Axes, modified in-place
            mat: This must be the return value from ``matshow`` or ``imshow``
            size: The width of the colorbar
            number_format: Formatting string for the text labels on the colorbar (passed to ``ax.figure.colorbar``)
        """
        #
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        # This is crazy, but if we don't have a colorbar, save_fig errors about vmin not being less than vmax
        # So we'll make it and then remove it
        # BUT! We can't remove the cax, so we'll decrease its size
        # This is really important because if we skip the cbar, it's likely to save valuable space
        divider = make_axes_locatable(ax)
        if sauronlab_rc.general_colorbar_on:
            pad = sauronlab_rc.general_colorbar_left_pad
        else:
            size = "0%"
            pad = 0
        cax = divider.append_axes("right", size=size, pad=pad)
        cbar = ax.figure.colorbar(mat, cax=cax, format=number_format)
        if not sauronlab_rc.general_colorbar_on:
            cbar.remove()
        return cbar

    @classmethod
    def manual_legend(
        cls,
        ax: Axes,
        labels: Sequence[str],
        colors: Sequence[str],
        patch_size: float = sauronlab_rc.legend_marker_size,
        patch_alpha=1.0,
        **kwargs,
    ) -> mlegend.Legend:
        """
        Creates legend handles manually and adds them as the legend on the Axes.
        This is unfortunately necessary in cases where, for ex, only a handle per color is wanted -- not a handle per color and marker shape.
        Applies ``cls.fix_labels`` and applies sauronlab_rc defaults unless they're overridden in kwargs.
        """
        labels, colors = list(labels), list(colors)
        kwargs = copy(kwargs)
        kwargs["ncol"] = kwargs.get("ncol", sauronlab_rc.legend_n_cols)
        kwargs["bbox_to_anchor"] = kwargs.get("bbox_to_anchor", sauronlab_rc.legend_bbox)
        kwargs["mode"] = "expand" if sauronlab_rc.legend_expand else None
        kwargs["loc"] = kwargs.get("loc")
        if "patch_size" in kwargs:
            raise XValueError("patch_size cannot be passed as an argument and kwargs")
        if "patch_alpha" in kwargs:
            raise XValueError("patch_alpha cannot be passed as an argument and kwargs")
        handles = cls.manual_legend_handles(
            labels, colors, patch_size=patch_size, patch_alpha=patch_alpha
        )
        return ax.legend(handles=handles, **kwargs)

    @classmethod
    def manual_legend_handles(
        cls,
        labels: Sequence[str],
        colors: Sequence[str],
        patch_size: float = sauronlab_rc.legend_marker_size,
        patch_alpha=1.0,
        **patch_properties,
    ) -> Sequence[patches.Patch]:
        """
        Creates legend handles manually. Does not add the patches to the Axes.
        Also see ``cls.manual_legend``.
        This is unfortunately necessary in cases where, for ex, only a handle per color is wanted -- not a handle per color and marker shape.
        Applies ``cls.fix_labels``.
        """
        assert len(labels) == len(colors), f"{len(labels)} labels but {len(colors)} colors"
        legend_dict = {e: colors[i] for i, e in enumerate(labels)}
        patch_list = []
        for key in legend_dict:
            data_key = patches.Patch(
                color=legend_dict[key],
                label=cls.fix_labels(key),
                linewidth=patch_size,
                alpha=patch_alpha,
                **patch_properties,
            )
            patch_list.append(data_key)
        return patch_list

    @classmethod
    def fix_labels(
        cls, name: Union[Iterable[str], str], inplace: bool = False
    ) -> Union[Iterable[str], str]:
        """
        Fixes common issues with label names.
        Examples:
            - (-) gets a minus sign: (−)
            - 'uM' is changed to 'µM'
            - --> is changed to →
            - __a and __b are made nicer
            - math is escaped in TeX if necessary
        """

        # noinspection PyProtectedMember
        def fix_u(s: str) -> str:

            return (
                str(s)
                .replace("(-)", "(−)")
                .replace("killed (+)", "lethal (+)")
                .replace("-->", Chars.right)
                .replace("<--", Chars.left)
                .replace("uM", "µM")
                .replace("__a", ":" + Chars.angled("a"))
                .replace("__b", ":" + Chars.angled("b"))
            )

        def fix_ltext(s: str) -> str:

            # escape: # $ % & ~ _ ^ \ { } \( \) \[ \]
            return (
                Tools.strip_paired(s, [("$", "$")])
                .replace("killed (+)", "lethal (+)")
                .replace("__a", ":``a'")
                .replace("__b", ":``b'")
                .replace("_", r"\_")
                .replace("uM", r"\micro M")
                .replace(
                    Chars.micro, r"\micro "
                )  # always append a space to avoid 'undefined control sequence'
            )

        def fix_lmath(s: str) -> str:

            return (
                ("$" + Tools.strip_paired(s, [("$", "$")]) + "$")
                .replace("killed (+)", "lethal (+)")
                .replace("__a", r"\langle a \rangle")
                .replace("__b", r"\langle b \rangle")
                .replace("-->", r"\rightarrow")
                .replace("<--", r"\leftarrow")
                .replace("_", "\\_")
                .replace("uM", r"\micro M")
                .replace(
                    Chars.micro, r"\micro "
                )  # always append a space to avoid 'undefined control sequence'
            )

        def choose_fix(s: str) -> str:

            if not plt.rcParams["text.usetex"]:
                return fix_u(s)
            elif (
                sauronlab_rc.label_force_text_mode
                or not sauronlab_rc.label_force_math_mode
                and "$" not in s
            ):
                return fix_ltext(s)
            elif (
                sauronlab_rc.label_force_math_mode
                or s.startswith("$")
                and s.endswith("$")
                and s.count("$") == 2
            ):
                return fix_lmath(s)
            else:
                logger.error(f"Cannot fix mixed-math mode string {Chars.shelled(s)}")
                return s

        def fix(s0: str) -> str:

            is_label = hasattr(s0, "get_text")
            if is_label:
                # noinspection PyUnresolvedReferences
                s = s0.get_text()  # for matplotlib tick labels
            elif inplace:
                logger.caution("Cannot set inplace; type str")
                s = s0
            else:
                s = s0
            s = sauronlab_rc.label_replace_dict.get(s, s)
            r = choose_fix(s) if sauronlab_rc.label_fix else s
            r = sauronlab_rc.label_replace_dict.get(r, r)
            if inplace and is_label:
                # noinspection PyUnresolvedReferences
                s0.set_text(r)
            if r != s:
                logger.debug(f"Fixed {s} → {r}")
            return r

        if Tools.is_true_iterable(name):
            return (fix(s) for s in name)
        else:
            return fix(name)

    @classmethod
    def stamp_runs(cls, ax: Axes, run_ids: Iterable[int]) -> Axes:
        """
        Stamps the run ID(s) in the upper-left corner.
        Only shows if sauronlab_rc.stamp_on is True AND len(run_ids) <= sauronlab_rc.stamp_max_runs.
        """
        if sauronlab_rc.stamp_on:
            run_ids = InternalTools.fetch_all_ids_unchecked(Runs, run_ids)
            run_ids = Tools.unique(run_ids)
            if len(run_ids) <= sauronlab_rc.stamp_max_runs:
                text = Tools.join(run_ids, sep=", ", prefix="r")
                return cls.stamp(ax, text, Corners.TOP_LEFT)

    @classmethod
    def stamp_time(cls, ax: Axes) -> Axes:
        """
        If sauronlab_rc.stamp_on is on, stamps the datetime to the top right corner.
        """
        if sauronlab_rc.stamp_on:
            text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return cls.stamp(ax, text, Corners.TOP_RIGHT)


class _Pub:
    """
    Functions to save figures as PDFs in a "publication" mode.
    Provides a context manager that yields a FigureSaver.
    Clears all figures (inc. pre-existing) before entering and on every save.
    Hides all display.
    """

    @contextmanager
    def __call__(
        self, width: str, height: str, save_under: PathLike = "", *args, **kwargs
    ) -> Generator[FigureSaver, None, None]:
        """
        A context manager with a ``FigureSaver``, non-interactive, auto-clearing, and optional sauronlab_rc params.

        Args:
            width: A string passed to ``sauronlab_rc``; ex: ``1/2 2_col`` (defined in sauronlab_rc params file)
            height: A string passed to ``sauronlab_rc``; ex: ``1/2 2_col`` (defined in sauronlab_rc params file)
            save_under: Save everything under this directory (but passing absolute paths will invalidate this)
            args: Functions of sauronlab_rc passed to ``sauronlab_rc.using``
            kwargs: Kwargs of sauronlab_rc and matplotlib params passed to ``sauronlab_rc.using``.
        """
        save_under = str(save_under).replace("/", os.sep)
        save_under = Tools.prepped_dir(save_under)
        # the_fn, kwargs = InternalTools.from_kwargs(kwargs, 'fn', None)
        # args = [*args, the_fn if the_fn is not None else copy(args)]
        pretty_dir = str(save_under) if len(str(save_under)) > 0 else "."
        logger.debug(f"::Entered:: saving environment {kwargs.get('scale', '')} under {pretty_dir}")
        FigureTools.clear()
        saver = FigureSaver(save_under=save_under, clear=lambda fig: FigureTools.clear())
        with FigureTools.hiding():
            with sauronlab_rc.using(
                width=width, height=height, *args, savefig_format="pdf", **kwargs
            ):
                yield saver
        logger.debug("::Left:: saving environment {kwargs.get('scale', '')} under {pretty_dir}")


Pub = _Pub()

__all__ = [
    "FigureTools",
    "FigureSaver",
    "Pub",
    "FancyColorSchemes",
    "FancyCmaps",
]
