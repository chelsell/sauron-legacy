from __future__ import annotations

from clana.optimize import simulated_annealing
from matplotlib.figure import Figure
from typeddfs.matrix_dfs import MatrixDf

from sauronlab.core.core_imports import *
from sauronlab.viz.confusion_plots import *

logger = logging.getLogger("sauronlab")


class ConfusionMatrix(MatrixDf):
    """
    A wrapper around a confusion matrix as a Pandas DataFrame.
    The rows are the correct labels, and the columns are the predicted labels.
    """

    def _repr_html_(self) -> str:

        return "<strong>{}: {} {}</strong>\n{}".format(
            self.__class__.__name__,
            self._dims(),
            Chars.check if self.rows == self.cols else Chars.x,
            pd.DataFrame._repr_html_(self),
            len(self),
        )

    def symmetrize(self) -> ConfusionMatrix:
        """
        Averages with its transpose, forcing it to be symmetric.

        Returns:
            A copy
        """
        return ConfusionMatrix(0.5 * (self + self.T))

    def sort(self, **kwargs) -> ConfusionMatrix:
        """
        Sorts this confusion matrix to show clustering. The same ordering is applied to the rows and columns.
        Call this first. Do not call symmetrize(), log(), or triagonalize() before calling this.
        Returns a copy.

        Returns:
            A dictionary mapping class names to their new positions (starting at 0)

        """
        permutation = self.permutation(**kwargs)
        return self.sort_with(permutation)

    def permutation(self, **kwargs) -> Mapping[str, int]:
        """
        Sorts this confusion matrix to show clustering. The same ordering is applied to the rows and columns.
        Returns the sorting. Does not alter this ConfusionMatrix.

        Returns:
            A dictionary mapping class names to their new positions (starting at 0)

        """
        if not self.is_symmetric():
            raise AmbiguousRequestError(
                f"Can't sort because rows {self.rows} and columns {self.columns} differ"
            )
        optimized = simulated_annealing(self.values, **kwargs)
        perm = list(reversed(optimized.perm))
        perm = {name: perm.index(i) for i, name in enumerate(self.rows)}
        logger.info(f"Permutation for rows {self.rows}: {perm}")
        return perm

    def sort_with(self, permutation: Union[Sequence[str], Mapping[str, int]]) -> ConfusionMatrix:
        """
        Sorts this ConfusionMatrix's rows and columns by a predefined ordering. Returns a copy.

        Args:
            permutation: Maps names (strings) to their 0-indexed positions (integers)
                         If a mapping, takes as-is; these are returned by permutation()
                         If a DataFrame, must have 2 columns 'key' (name) and 'value' (position), and 1 row per name
                         If a str, tries to read a CSV file at that path into a DataFrame; uses Tools.csv_to_dict

        Returns:
            A new ConfusionMatrix with sorted rows and columns

        """
        if not self.is_symmetric():
            raise AmbiguousRequestError(
                f"Cannot sort because rows {self.rows} and columns {self.columns} differ"
            )
        if isinstance(permutation, Sequence):
            if set(permutation) != set(self.rows):
                permutation = {name: i for i, name in enumerate(permutation)}
            else:
                raise RefusingRequestError(
                    f"{len(permutation)} permutation elements instead of {len(self)}. See sort_first."
                )
        data = self.reindex(sorted(self.rows, key=lambda s: permutation[s]), axis=1)
        xx = [permutation[name] for name in self.rows]
        data["__sort"] = xx
        data = data.sort_values("__sort").drop("__sort", axis=1)
        return ConfusionMatrix(data)

    def sort_first(self, first: Sequence[str]) -> ConfusionMatrix:
        """
        Put these elements first.
        """
        first = [*first, *[r for r in self.rows if r not in first]]
        permutation = {name: i for i, name in enumerate(first)}
        return self.sort_with(permutation)

    @property
    def length(self) -> int:
        """
        Gets a safe length, verifying that the ``len(rows) == len(cols)``.
        """
        if len(self.rows) != len(self.cols):
            raise LengthMismatchError(f"{len(self.rows)} rows != {len(self.cols)} cols")
        return len(self.rows)

    def __repr__(self) -> str:
        return f"ConfusionMatrix({len(self.rows)} labels @ {hex(id(self))})"

    def __str__(self) -> str:
        return repr(self)

    def heatmap(
        self,
        vmin: float = 0,
        vmax: float = 1,
        runs: Optional[Sequence[int]] = None,
        renamer: Union[None, Mapping[str, str], Callable[[str], str]] = None,
        label_colors: Union[bool, Mapping[str, str]] = False,
    ) -> Figure:
        """
        Generates a heatmap.

        Args:
            vmin: Set this as the minimum accuracy (white on the colorbar)
            vmax: Set this as the maximum accuracy (black on the colorbar)
            runs: Run stamps in the upper-left corner with these runs (not verified)
            renamer: A function that maps the class names to new names for plotting
            label_colors: Mapping from names to colors for the labels; or a string for all control colors

        Returns:
            The figure, which was not displayed
        """
        return ConfusionPlots.plot(
            self, vmin=vmin, vmax=vmax, renamer=renamer, runs=runs, label_colors=label_colors
        )


class ConfusionMatrices:
    """ """

    @classmethod
    def average(cls, matrices: Sequence[ConfusionMatrix]) -> ConfusionMatrix:
        """
        Averages a list of confusion matrices.

        Args:
            matrices: An iterable of ConfusionMatrices (does not need to be a list)

        Returns:
            A new ConfusionMatrix
        """
        if len(matrices) < 1:
            raise EmptyCollectionError("Cannot average 0 matrices")
        matrices = [m.unsort() for m in matrices]
        rows, cols, mx0 = matrices[0].rows, matrices[0].columns, matrices[0]
        if any((not m.is_symmetric() for m in matrices)):
            raise RefusingRequestError(
                "Refusing to average matrices because"
                "for at least one matrix the rows and columns are different"
            )
        for m in matrices[1:]:
            if m.rows != rows:
                raise RefusingRequestError(
                    "At least one confusion matrix has different rows than another"
                    "(or different columns than another)"
                )
            mx0 += m
        # noinspection PyTypeChecker
        return ConfusionMatrix((1.0 / len(matrices)) * mx0)

    @classmethod
    def agg_matrices(
        cls,
        matrices: Sequence[ConfusionMatrix],
        aggregation: Callable[[Sequence[pd.DataFrame]], None],
    ) -> ConfusionMatrix:
        """
        Averages a list of confusion matrices.

        Args:
            matrices: An iterable of ConfusionMatrices (does not need to be a list)
            aggregation: to perform, such as np.mean

        Returns:
            A new ConfusionMatrix
        """
        if len(matrices) < 1:
            raise EmptyCollectionError("Cannot aggregate 0 matrices")
        matrices = [mx.unsort() for mx in matrices]
        rows, cols, mx = matrices[0].rows, matrices[0].columns, matrices[0]
        if rows != cols:
            raise RefusingRequestError(
                "Refusing to aggregate matrices because for at least one matrix the rows and columns are different"
            )
        ms = []
        for m in matrices[1:]:
            if m.rows != rows or m.columns != cols:
                raise RefusingRequestError(
                    "At least one confusion matrix has different rows than another (or different columns than another)"
                )
            ms.append(m)
        return ConfusionMatrix(aggregation(ms))

    @classmethod
    def zeros(cls, classes: Sequence[str]) -> ConfusionMatrix:
        return ConfusionMatrix(
            pd.DataFrame(
                [pd.Series({"class": r, **{c: 0.0 for c in classes}}) for r in classes]
            ).set_index("class")
        )

    @classmethod
    def perfect(cls, classes: Sequence[str]) -> ConfusionMatrix:
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 if r == c else 0.0 for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )

    @classmethod
    def uniform(cls, classes: Sequence[str]) -> ConfusionMatrix:
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 / len(classes) for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )


__all__ = ["ConfusionMatrix", "ConfusionMatrices"]
