from __future__ import annotations

from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *
from sauronlab.ml.accuracy_frames import AccuracyFrame
from sauronlab.ml.confusion_matrices import ConfusionMatrix


class DecisionFrame(TypedDf):
    """
    An n × m matrix of probabilities (or scores) from a classifier.
    The n rows are samples, and the m columns are predictions. The values are the confidence or pobability of prediction.
    The single index column is named 'correct_label', and the single column name is named 'label'.
    Practically, this is a Pandas wrapper around a scikit-learn decision_function
    that also has the predicted and correct class labels.
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(_required_columns=["label", "sample_id"])

    @classmethod
    def of(
        cls,
        correct_labels: Sequence[str],
        labels: Sequence[str],
        decision_function: np.array,
        sample_ids: Sequence[Any],
    ) -> DecisionFrame:
        """
        Wraps a decision function numpy array into a DecisionFrame instance complete with labels as names and columns.

        Args:
            correct_labels: A length-n list of the correct labels for each of the n samples
            labels: A length-m list of class labels matching the predictions (columns) on ``probabilities``
            decision_function: An n × m matrix of probabilities (or scores) from the classifier.
                               The rows are samples, and the columns are predictions.
                               scikit-learn decision_functions (ex model.predict_proba) will output this.
            sample_ids: IDs (or names) of training examples for later reference; should be unique

        Returns:
            A DecisionFrame
        """
        decision_function = pd.DataFrame(decision_function)
        decision_function.index = [correct_labels, sample_ids]
        decision_function.columns = labels
        decision_function.index.names = ["label", "sample_id"]
        return cls.convert(decision_function)

    def confusion(self) -> ConfusionMatrix:
        labels = self.columns
        correct_labels = self.index.get_level_values("label")
        if self.shape[0] != len(correct_labels):
            raise LengthMismatchError(
                f"N decision function rows of shape {self.shape} != N correct labels {len(correct_labels)}"
            )
        if self.shape[1] != len(labels):
            raise LengthMismatchError(
                "N decision function columns of shape {self.shape} != N class labels {len(labels)}"
            )
        correct_confused_with = {c: {p: 0.0 for p in labels} for c in labels}
        for r, row in enumerate(self.index):
            correct_name = correct_labels[r]
            for c, column in enumerate(self.columns):
                confused_name = labels[c]
                correct_confused_with[correct_name][confused_name] += self.iat[r, c]
        correct_confused_with = pd.DataFrame(correct_confused_with)
        correct_confused_with /= correct_confused_with.sum()
        return ConfusionMatrix(correct_confused_with)

    def accuracy(self) -> AccuracyFrame:
        actual_labels = self.index.get_level_values("label").values
        sample_ids = self.index.get_level_values("sample_id").values
        stripped = self.reset_index().drop("sample_id", axis=1).set_index("label")
        predicted_labels = stripped.idxmax(axis=1).values
        predicted_probs = stripped.max(axis=1).values
        actual_probs = stripped.apply(lambda r: r.loc[r.name], axis=1).values
        return AccuracyFrame(
            {
                "label": actual_labels,
                "sample_id": sample_ids,
                "prediction": predicted_labels,
                "score": actual_probs * 100.0,
                "score_for_prediction": predicted_probs * 100.0,
            }
        )


__all__ = ["DecisionFrame"]
