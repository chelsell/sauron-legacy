from sauronlab.caches.caching_wfs import *
from sauronlab.caches.datasets import Dataset, Datasets
from sauronlab.caches.sensor_caches import *
from sauronlab.caches.wf_caches import *
from sauronlab.core.core_imports import *
from sauronlab.model.compound_names import *
from sauronlab.model.features import FeatureTypes
from sauronlab.model.treatment_names import *
from sauronlab.model.well_frames import *
from sauronlab.model.well_names import *


class SauronlabDatasetTools:
    """"""

    @classmethod
    def filter_fewer(cls, df: WellFrame, cutoff: int) -> WellFrame:
        """
        For any compound with fewer than ``cutoff`` wells containing exactly that compound, filters the corresponding wells.

        Args:
            df: A WellFrame with 0 or 1 compounds per well
            cutoff: Minimum

        Returns:
            The filtered WellFrame
        """
        if np.any(df["c_ids"].map(len) > 1):
            raise RefusingRequestError(
                "Won't run filter_fewer because some wells contain more than 1 compound."
                "The results are too likely to be different than you want."
                "You should implement a more general function instead."
            )
        for c in df.unique_compound_ids():
            m = len(df[df["c_ids"] == (c,)])
            if m < cutoff:
                df = df[df["c_ids"] != (c,)]
                logger.info(f"Discarded c{c} with {m}<{cutoff} replicates")
                m = len(df[df["c_ids"] == (c,)])
                assert m == 0, f"{m} left"
        return df


@abcd.auto_eq()
@abcd.auto_hash()
@abcd.auto_repr_str()
class OptisepDataset(Dataset, metaclass=abc.ABCMeta):
    """ """

    def __init__(self, training_experiment: int, is_test_set: bool):
        self.training_experiment = training_experiment
        self.is_test_set = is_test_set

    @abcd.overrides
    def _download(self):
        """ """
        today = datetime(2019, 6, 17)
        sep = datetime(2018, 3, 24)
        # noinspection PyTypeChecker
        if self.is_test_set:
            wheres = [Experiments.id == self.test, Runs.datetime_run > sep]
        else:
            wheres = [Experiments.id == self.training_experiment, Runs.datetime_run < sep]
        namer = (
            WellNamers.builder()
            .control_type()
            .treatments("${name/lower}", if_missing_col="control_type")
            .build()
        )
        return Datasets.create(
            name="QC-OPT",
            feature=FeatureTypes.cd_10_i,
            wheres=wheres,
            namer=namer,
            compound_namer=CompoundNamers.tiered(as_of=today),
            today=today,
            post_process=lambda df: df.before_first_nan().slice_ms(0, 1000000).sort_by(),
        ).fetch()


class LeoDataset1(Dataset):
    """ """

    def _download(self):
        """ """
        today = datetime(2019, 6, 17)
        wheres = [Projects.name == "reference :: Leo BIOMOL", ~(Runs.id << [5315, 6315])]
        return Datasets.create(
            name="Leo-Biomol",
            feature=FeatureTypes.cd_10,
            wheres=wheres,
            namer=WellNamers.large_refset(),
            compound_namer=CompoundNamers.chembl(today),
            today=today,
        ).fetch()


class Nt650Flames(Dataset):
    """ """

    def _download(self):
        """ """
        pattern = regex.compile(r".*BM ([0-9]{1,2})\.([1-9]{1,2}).*", flags=regex.V1)
        today = datetime(2019, 10, 30)
        cache = WellCache("cd(10)-i", sensor_cache=SensorCache())
        bad_runs = {
            7631,
            7646,
            7650,
            7680,
            7684,
            7708,
            7732,
            7742,
            7756,
            7761,
            8029,
            8193,
            8205,
        }
        filters = ~(Runs.id << bad_runs)
        df = (
            CachingWellFrameBuilder(cache, today)
            .with_feature("cd(10)-i")
            .where(Projects.id == 780)
            .where(filters)
            .with_compound_names(CompoundNamers.chembl(today))
            .with_names(WellNamers.large_refset())
            .build()
        )
        original_length = df.feature_length()
        df = df.after_last_nan().before_first_nan()
        logger.trace(
            f"Lost {original_length - df.feature_length()} features: {original_length} → {df.feature_length()}"
        )
        return (
            df.sort_values(["run", "well_index"])
            .subset(1, None)
            .without_controls({"no drug transfer"})
        )


class SauronlabDatasets:
    """ """

    @classmethod
    @abcd.copy_docstring(LeoDataset1)
    def leo_biomol(cls) -> WellFrame:
        """ """
        return LeoDataset1().fetch()

    @classmethod
    @abcd.copy_docstring(Nt650Flames)
    def nt650_flames(cls) -> WellFrame:
        """ """
        return Nt650Flames().fetch()

    @classmethod
    def opti_train_a(cls) -> WellFrame:
        """ """
        return OptisepDataset(1231, False).fetch()

    @classmethod
    def opti_train_b(cls) -> WellFrame:
        """ """
        return OptisepDataset(1238, False).fetch()

    @classmethod
    def opti_test_a(cls) -> WellFrame:
        """ """
        return OptisepDataset(1238, True).fetch()

    @classmethod
    def opti_test_b(cls) -> WellFrame:
        """ """
        return OptisepDataset(1231, True).fetch()

    @classmethod
    def prestwick_flames(cls) -> WellFrame:
        today = datetime(2021, 1, 1)
        return Datasets.create(
            name="Prestwick",
            feature=FeatureTypes.cd_10_i,
            wheres=[Experiments.id == 1841],
            namer=WellNamers.large_refset(),
            compound_namer=CompoundNamers.chembl(today),
            today=today,
        ).fetch()

    @classmethod
    def diverset_flames(cls) -> WellFrame:
        today = datetime(2021, 1, 1)
        return Datasets.create(
            name="DIVERSet",
            feature=FeatureTypes.cd_10_i,
            wheres=[Experiments.id == 1548],
            namer=WellNamers.large_refset(),
            compound_namer=CompoundNamers.chembl(today),
            today=today,
        ).fetch()

    @classmethod
    def qc_opt_full(cls) -> WellFrame:
        """ """
        today = datetime(2019, 9, 1)
        namer = (
            WellNamers.builder()
            .control_type()
            .treatments("${name/lower}", if_missing_col="control_type")
            .build()
        )
        return Datasets.create(
            name="QC-OPT",
            feature=FeatureTypes.cd_10_i,
            wheres=[Experiments.id == 1578, ~(Runs.id << [1578, 7519, 7585, 7348, 7350])],
            namer=namer,
            compound_namer=CompoundNamers.tiered(as_of=today),
            today=today,
        ).fetch()

    @classmethod
    def qc_dr_full(cls) -> WellFrame:
        """ """
        today = datetime(2019, 9, 1)
        namer = (
            WellNamers.builder()
            .control_type()
            .treatments("${name/lower} ${dose}", if_missing_col="control_type")
            .build()
        )
        return Datasets.create(
            name="QC-OPT",
            feature=FeatureTypes.cd_10_i,
            wheres=[Experiments.id == 1575, Runs.id != 7034],
            namer=namer,
            compound_namer=CompoundNamers.tiered(as_of=today),
            today=today,
        ).fetch()

    @classmethod
    def _mi_ref(
        cls, name: str, experiment: int, namer: WellNamer = WellNamers.elegant()
    ) -> WellFrame:
        today = datetime(2020, 1, 1)
        return Datasets.create(
            name=name,
            feature=FeatureTypes.MI,
            wheres=[Experiments.id == experiment],
            namer=namer,
            compound_namer=CompoundNamers.tiered(as_of=today),
            today=today,
        ).fetch()

    @classmethod
    def ref_capria(cls) -> WellFrame:
        """"""
        return cls._mi_ref("capria", 6)

    @classmethod
    def ref_ashley(cls) -> WellFrame:
        """"""
        return cls._mi_ref("ashley", 936)

    @classmethod
    def ref_matt(cls) -> WellFrame:
        """ """
        return cls._mi_ref("matt", 842)

    @classmethod
    def hallucinogens(cls) -> WellFrame:
        """ """
        return cls._mi_ref("hallucinogens", 1037)

    @classmethod
    def cannabinoids_adam(cls) -> WellFrame:
        """ """
        return cls._mi_ref("cannabinoids-adam", 819)

    @classmethod
    def cannabinoids_reid(cls) -> WellFrame:
        """ """
        return cls._mi_ref("cannabinoids-reid", 1312)

    @classmethod
    def retest_mgh(cls) -> WellFrame:
        """ """
        return cls._mi_ref("retest-mgh", 1101, namer=WellNamers.large_refset())

    @classmethod
    def screen_mgh_main(cls) -> WellFrame:
        """ """
        return cls._mi_ref("screen-mgh-main", 580, namer=WellNamers.large_refset())

    @classmethod
    def dmt(cls) -> WellFrame:
        """Experiment 1744 with all concentrations excluding empty wells.."""
        today = datetime(2019, 1, 1)
        compound_namer = CompoundNamers.tiered(as_of=today)
        displayer = StringTreatmentNamer("${tag} ${um}")
        namer = (
            WellNamerBuilder()
            .control_type()
            .treatments(
                displayer,
                if_missing_col="control_type",
                transform=lambda s: s.replace("olson.", ""),
            )
            .build()
        )
        return Datasets.create(
            name="DMT-ALL",
            feature=FeatureTypes.cd_10_i,
            wheres=[Experiments.id == 1744],
            namer=namer,
            compound_namer=compound_namer,
            today=today,
        ).fetch()

    @classmethod
    def dmt_paper(cls) -> WellFrame:
        """
        DMT and isoDMT analogs at 200uM with solvent controls. Experiment 1744 with run ID 7887 dropped.
        Replaces low-volume wells with their intended treatments.
        What was used in the paper.
        """
        today = datetime(2019, 1, 1)
        compound_namer = CompoundNamers.tiered(as_of=today)
        displayer = StringTreatmentNamer("${tag}")
        namer = (
            WellNamerBuilder()
            .column("control_type", transform=lambda s: s.replace("solvent (-)", "vehicle"))
            .treatments(
                displayer,
                if_missing_col="control_type",
                transform=lambda s: s.replace("olson.", ""),
            )
        ).build()
        wheres = [
            Experiments.id == 1744,
            Runs.id != 7887,
            Compounds.id != 34261,
            (ControlTypes.name == "solvent (-)") | (WellTreatments.micromolar_dose == 200),
        ]
        return Datasets.create(
            name="DMT-PAPER",
            feature=FeatureTypes.cd_10_i,
            wheres=wheres,
            namer=namer,
            compound_namer=compound_namer,
            today=today,
        ).fetch()


__all__ = ["SauronlabDatasets", "SauronlabDatasetTools"]
