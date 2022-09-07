from __future__ import annotations

import colorsys
import numbers

try:
    import ipywidgets as widgets
    from IPython.display import display
    from ipywidgets import Output
except ImportError:
    widgets = None
    display = None
    Output = None

from sauronlab.core.core_imports import *
from sauronlab.model.compound_names import *


class LayoutFrame(UntypedDf):
    def drug_cols(self):
        ii = 1
        while f"batch_{ii}" in self.columns:
            b, d = f"batch_{ii}", f"dose_{ii}"
            yield ii, b, d
            ii += 1

    def errors(self) -> None:
        """Complains about things."""
        raise NotImplementedError()

    def expand(self) -> LayoutFrame:
        """Replaces multi-well rows with row per well."""
        raise NotImplementedError()

    def show(self, *what) -> pd.DataFrame:
        """
        Pivots to get an 8-by-12 DataFrame where the values in the cell are from the column ``what``.
        If ``what`` has > 1 element, concatenates them separated by space.
        Uses Pandas colors for doses and Ns.
        """

    @classmethod
    def from_tp(cls) -> LayoutFrame:
        """Fetches a template plate as a LayoutFrame."""
        raise NotImplementedError()


class LayoutChecker:
    @classmethod
    def warn_wells(cls, template_plate: Union[TemplatePlates, int, str]) -> None:
        template_plate = TemplatePlates.fetch(template_plate)
        plate_type = template_plate.plate_type
        wb1 = ParsingWB1(plate_type.n_rows, plate_type.n_columns)
        ranges = [
            w.well_range_expression
            for w in TemplateWells.select().where(TemplateWells.template_plate == template_plate)
        ]
        all_wells = set()
        for wrange in ranges:
            for well in wb1.parse(wrange):
                if well in all_wells:
                    logger.warning(f"Well {well} specified twice")
                all_wells.add(well)
        for well in wb1.all_labels():
            if well not in all_wells:
                logger.error(f"Well {well} missing")


class LayoutParser:
    def parse(
        self,
        df: Union[PathLike, pd.DataFrame],
        n_rows: int = 8,
        n_columns: int = 12,
        check_vals: bool = True,
        replace_nans: bool = False,
    ) -> LayoutFrame:
        if (isinstance(df, str) or isinstance(df, PurePath)) and df.endswith(".xlsx"):
            df = pd.read_excel(df)
        elif (isinstance(df, str) or isinstance(df, PurePath)) and df.endswith(".csv"):
            df = pd.read_csv(df)
        EL = ParsingWB1(n_rows, n_columns)
        new_df = []
        labels_to_lines = {}
        for line_number, series_row in enumerate(df.itertuples()):
            for label in EL.parse(series_row.well):
                if label in labels_to_lines:
                    raise AlreadyUsedError(
                        f"{label} was included in spreadsheet rows {labels_to_lines[label]} and {line_number}"
                    )
                labels_to_lines[label] = line_number
                r, c = EL.label_to_rc(label)
                series = [
                    EL.label_to_index(label),
                    r,
                    c,
                    label,
                    series_row.control,
                    series_row.name,
                    series_row.n,
                    series_row.variant,
                    series_row.dpf,
                    series_row.group,
                ]
                series_dict = {
                    "i": series[0],
                    "row_i": series[1],
                    "col_j": series[2],
                    "well": series[3],
                    "control": series[4],
                    "name": series[5],
                    "n": series[6],
                    "variant": series[7],
                    "dpf": series[8],
                    "group": series[9],
                }
                series_dict.update(self._drugs_flat(df, series_row))
                new_df.append(series_dict)
        if len(new_df) != n_rows * n_columns:
            raise XValueError(f"Expected {n_rows * n_columns} wells but got {len(new_df)}")
        df = pd.DataFrame(new_df, columns=self._cols(df))
        df[["dpf", "n"]] = df[["dpf", "n"]].apply(pd.to_numeric)
        df = df.astype({"dpf": "Int64", "n": "Int64"})
        if check_vals:
            self._check(df)
        self._duplicates(df)
        if check_vals:
            for line_number, b, new_df in self._drug_cols(df):
                df[new_df] = df[new_df].map(float)
        df["control"] = df["control"].map(
            lambda q: None
            if Tools.is_empty(q) or q.strip() == "not a control"
            else ControlTypes.fetch(q).name
        )
        if replace_nans:
            df.replace(np.nan, "-", inplace=True)
        return LayoutFrame(df.sort_values("i"))

    def _check(self, df) -> None:
        batches = set()
        for drug_col, batch_series, dose_series in self._drug_cols(df):
            for row_number, dose_float in enumerate(df[dose_series]):
                try:
                    float(dose_float)
                except ValueError:
                    raise XValueError(
                        f"Dose of '{dose_float}'  in column {dose_series} on row {row_number} is invalid"
                    ) from None
            df[dose_series].map(float)
            for batch in df[batch_series]:
                batches.add(batch)
        for batch in batches:
            if not Tools.is_empty(batch):
                Batches.fetch(batch)

    def _duplicates(self, df) -> None:
        for i, row in enumerate(df.itertuples()):
            batches = set()
            for batch, dose in self._drugs(df, row):
                if batch in batches:
                    raise AlreadyUsedError(f"Batch {batch} is duplicated in row {i}")
                if not Tools.is_empty(batch):
                    batches.add(batch)

    def _cols(self, df) -> Sequence[str]:
        return ["i", "row_i", "col_j", *df.columns]

    def _drugs_flat(self, df, row):
        cols = {}
        for i, b, d in self._drug_cols(df):
            cols[b] = getattr(row, b)
            cols[d] = getattr(row, d)
        return cols

    def _drugs(self, df, row) -> Generator[Tup[Union[int, str], Union[int, str]], None, None]:
        for i, b, d in self._drug_cols(df):
            yield getattr(row, b), getattr(row, d)

    def _drug_cols(self, df):
        ii = 1
        while f"batch_{ii}" in df.columns:
            b, d = f"batch_{ii}", f"dose_{ii}"
            yield ii, b, d
            ii += 1

    def insert(
        self,
        df: LayoutFrame,
        name: str,
        description: str,
        plate_type: Union[PlateTypes, int, str],
        whoami: Union[int, str, Users],
    ) -> TemplatePlates:
        plate = TemplatePlates(
            name=name, description=description, plate_type=plate_type, author=Users.fetch(whoami)
        )
        plate.save()

        def nq(q):
            return "" if Tools.is_empty(q) else q

        for row in df.itertuples():
            TemplateWells(
                age_expression=nq(row.dpf),
                control_type=Tools.or_null(row.control, ControlTypes.fetch),
                group_expression=nq(row.group),
                n_expression=nq(row.n),
                template_plate=plate,
                variant_expression=nq(row.variant),
                well_range_expression=row.well,
            ).save()
            for batch, dose in self._drugs(df, row):
                # Only insert templateTreatments if batch and dose are NOT empty.
                if not (Tools.is_empty(batch)) and not (Tools.is_empty(dose)):
                    TemplateTreatments(
                        well_range_expression=nq(row.well),
                        template_plate=nq(plate),
                        dose_expression=nq(dose),
                        batch_expression=nq(batch),
                    ).save()
        return plate

    def update(
        self,
        df: LayoutFrame,
        name: str,
        description: str,
        plate_type: Union[PlateTypes, int, str],
        whoami: Union[int, str, Users],
    ) -> TemplatePlates:
        plate = TemplatePlates.select().where(TemplatePlates.name == name).first()
        TemplatePlates.update(
            name=name, description=description, plate_type=plate_type, author=Users.fetch(whoami)
        ).where(TemplatePlates.name == name).execute()

        def nq(q):

            return "" if Tools.is_empty(q) else q

        ftw_row = TemplateWells.select().where(TemplateWells.template_plate == nq(plate.id)).first()
        ftt_row = (
            TemplateTreatments.select()
            .where(TemplateTreatments.template_plate == nq(plate.id))
            .first()
        )
        for i, row in enumerate(df.itertuples()):
            TemplateWells.update(
                age_expression=nq(row.dpf),
                control_type=None
                if Tools.is_empty(row.control)
                else ControlTypes.fetch(row.control),
                group_expression=nq(row.group),
                n_expression=nq(row.n),
                template_plate=nq(plate.id),
                variant_expression=nq(row.variant),
                well_range_expression=row.well,
            ).where(TemplateWells.template_plate == nq(plate.id)).where(
                TemplateWells.id == ftw_row.id + i
            ).execute()
            for batch, dose in self._drugs(df, row):
                TemplateTreatments.update(
                    well_range_expression=nq(row.well),
                    template_plate=nq(plate.id),
                    dose_expression=nq(dose),
                    batch_expression=nq(batch),
                ).where(TemplateTreatments.template_plate == nq(plate.id)).where(
                    TemplateTreatments.id == ftt_row.id + i
                ).execute()
        return plate

    def update_run(
        self,
        df: LayoutFrame,
        run: Union[int, str, Runs, Submissions],
        dry: bool,
        discard_solvents: bool = False,
    ) -> None:
        batch_dose_cols = [(batch_col, dose_col) for _, batch_col, dose_col in self._drug_cols(df)]
        run = Tools.run(run)
        plate_type = run.plate.plate_type
        EL = ParsingWB1(plate_type.n_rows, plate_type.n_columns)
        if not dry:
            for wt in (
                WellTreatments.select(WellTreatments, Wells)
                .join(Wells)
                .where(Wells.run_id == run.id)
            ):
                wt.delete_instance()
        total_n_wells, total_n_treatments = 0, 0
        unique_bids, unique_variants, unique_controls, unique_groups, unique_ns = (
            set(),
            set(),
            set(),
            set(),
            set(),
        )
        for row in df.itertuples():
            n_wells, n_treatments = 0, 0
            for well_index in (EL.label_to_index(w) for w in EL.parse(row.well)):
                well = (
                    Wells.select()
                    .where(Wells.run == run)
                    .where(Wells.well_index == well_index)
                    .first()
                )  # type: Wells
                well.control_type = Tools.or_null(row.control, ControlTypes.fetch)
                unique_controls.add(well.control_type)
                well.n = Tools.or_null(well.n, int)
                unique_ns.add(well.n)
                well.variant = Tools.or_null(well.variant, GeneticVariants.fetch)
                unique_variants.add(well.variant)
                well.well_group = row.group
                unique_groups.add(well.well_group)
                if not dry:
                    well.save()
                n_wells += 1
                for batch_col, dose_col in batch_dose_cols:
                    batch = Tools.or_null(getattr(row, batch_col), Batches.fetch)
                    dose = Tools.or_null(getattr(row, dose_col), float)
                    if (
                        discard_solvents
                        and well.control_type is not None
                        and batch.compound_id in ValarTools.known_solvent_names().keys()
                    ):
                        logger.debug(
                            f"Skipping solvent {ValarTools.known_solvent_names()[batch.compound_id]} for well {well.id}"
                        )
                        continue
                    unique_bids.add(batch)
                    logger.debug(
                        f"Adding batch {batch} (dose {dose}) for well {well.id} and control type {row.control}"
                    )
                    wt = WellTreatments(well=well, batch=batch, micromolar_dose=dose)
                    if not dry:
                        wt.save()
                    n_treatments += 1
            total_n_wells += n_wells
            total_n_treatments += n_treatments
            logger.debug(f"Added {n_wells} wells and {n_treatments} treatments for row {row.well}")
        logger.notice(
            f"Added {total_n_wells} total wells and {total_n_treatments} treatments for run r{run.id}"
        )
        logger.info("Added batch IDs: " + Tools.join(unique_bids, ","))


class LayoutVisualizer:
    """
    Takes in a spreadsheet that contains layout parameters and returns a visualization of the layout.
    """

    def __init__(self, dfs: Union[str, pd.DataFrame, Sequence[Union[str, pd.DataFrame]]]):
        if not isinstance(dfs, list):
            self._labels = [dfs]
        else:
            self._labels = dfs
        if isinstance(dfs, str) or isinstance(dfs, pd.DataFrame):
            self._layout_dfs = [LayoutParser().parse(dfs, check_vals=False, replace_nans=True)]
        else:
            self._layout_dfs = [
                LayoutParser().parse(df, check_vals=False, replace_nans=True) for df in dfs
            ]

    @property
    def layout_dfs(self) -> List[pd.DataFrame]:
        return self._layout_dfs

    def _get_N_HexCol(self, num_of_colors: int):
        hsv_tuples = [(x * 1.0 / num_of_colors, 0.25, 1) for x in range(num_of_colors)]
        hex_out = []
        for rgb in hsv_tuples:
            rgb = list(map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*rgb)))
            hex_out.append("#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2]))
        return hex_out

    def _pivot(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        new_df = df.pivot("row_i", "col_j", column).reset_index()
        new_df["row_i"] = new_df["row_i"].map(lambda i: chr(64 + i))
        new_df = new_df.set_index("row_i")
        return new_df

    def _find_treatments(self, df: pd.DataFrame):
        lower_cols = [k.lower() for k in df.columns.tolist()]
        batch_cols = []
        valid_b = set()
        # Find all batch Columns
        for c in lower_cols:
            if c.startswith("batch"):
                batch_cols.append(c)
        # Verify that the batch columns each have dose counterparts
        for b in batch_cols:
            num = b.split("_")[1]
            dose = f"dose_{num}"
            if dose in lower_cols:
                valid_b.add((b, dose))
        return valid_b

    def _add_color_scheme(self, df: pd.DataFrame, df2: pd.DataFrame = None):
        """
        Adds color scheme to single dataframe.
        If df2 is provided, adds color scheme to df based on values of df2.
        """
        if df2 is not None:
            chosen_df = df2
        else:
            chosen_df = df
        unique_vals = pd.unique(chosen_df.values.ravel("K"))
        colors = self._get_N_HexCol(len(unique_vals))
        color_map = dict(zip(unique_vals, colors))

        def change_bg_cell(s):
            return ["background-color: " + color_map[val] for val in s]

        def style_helper_df(c):
            df1 = pd.DataFrame("", index=c.index, columns=c.columns)
            for x in df1.index:
                for y in df1.columns:
                    df1.loc[x, y] = "background-color: " + color_map[df2.loc[x, y]]
            return df1

        if df2 is not None:
            colored_df = df.style.apply(style_helper_df, axis=None)
        else:
            colored_df = df.style.apply(change_bg_cell)
        return colored_df, color_map

    def _fix_batch_dict(self, color_map):
        batch_hashes = [c.replace('"', "") for c in color_map if ("$" not in c) and (c != "-")]
        batch_dict = BatchNamerWrapping(CompoundNamers.tiered_fallback(), True).fetch(batch_hashes)
        treat_dict = {}
        for cp in color_map:
            if ("$" not in cp) and (cp != "-"):
                batch_id = Batches.fetch(cp.replace('"', "")).id
                if batch_id in batch_dict:
                    treat_dict[batch_dict[batch_id] + f" (b{batch_id})"] = color_map[cp]
                else:
                    treat_dict[cp] = color_map[cp]
            else:
                treat_dict[cp] = color_map[cp]
        return treat_dict

    def _create_treatment_df(self, num: int, df: pd.DataFrame):
        # Color the batch_df first then overwrite with dose values
        batch_df = self._pivot(df, f"batch_{num}")
        dose_df = self._pivot(df, f"dose_{num}")
        colored_df, color_map = self._add_color_scheme(dose_df, batch_df)
        fixed_color_map = self._fix_batch_dict(color_map)
        return colored_df, fixed_color_map

    def _create_color_legend(self, col_map):
        button_list = []
        for cm in col_map:
            if isinstance(cm, numbers.Number):
                cm_desc = str(cm)
            else:
                cm_desc = cm
            b = widgets.Button(description=cm_desc)
            b.style.button_color = col_map[cm]
            button_list.append(b)
        return widgets.VBox(button_list)

    def _display_single(self, df: pd.DataFrame, label: str = None):
        tab = widgets.Tab()
        num_t = len(self._find_treatments(df))
        tab_titles = [f"Treatment {i + 1}" for i in range(num_t)]
        tab_titles += ["Variant", "Control", "Dpf", "Group", "N"]
        tab_dfs = [self._create_treatment_df(t + 1, df) for t in range(num_t)]
        tab_dfs += [
            self._add_color_scheme(self._pivot(df, j.lower()))
            for j in ["Variant", "Control", "Dpf", "Group", "N"]
        ]
        tab_labels = [f"Treatment {k + 1}: Dose(µM) & Batches" for k in range(num_t)]
        tab_labels += [
            "Genetic Variants",
            "Control Types",
            "Dpf(Days Post-Fertilization)",
            "Well Group",
            "Number of Fish",
        ]
        all_outputs = [Output() for i in range(len(tab_titles))]
        children = []
        for m in range(len(tab_titles)):
            color_leg = self._create_color_legend(tab_dfs[m][1])
            children.append(
                widgets.VBox(
                    [
                        widgets.Label("Layout for " + label),
                        widgets.Label(tab_labels[m]),
                        widgets.HBox([all_outputs[m], color_leg]),
                    ]
                )
            )
        tab.children = children
        for k in range(len(children)):
            with all_outputs[k]:
                display(tab_dfs[k][0])
        # Set the title of each Tab
        for i in range(len(tab_titles)):
            tab.set_title(i, tab_titles[i])
        return tab

    def display_all(self):
        """ """
        for i in range(len(self._layout_dfs)):
            display(self._display_single(self._layout_dfs[i], str(self._labels[i])))


class TemplateLayoutVisualizer(LayoutVisualizer):
    """Takes in a TemplatePlate and returns out a LayoutVisualizer."""

    def __init__(
        self, template_plates: Union[int, TemplatePlates, Collection[Union[int, TemplatePlates]]]
    ):
        if isinstance(template_plates, Collection):
            tps = [TemplatePlates.fetch(tp) for tp in template_plates]
        else:
            tps = [TemplatePlates.fetch(template_plates)]
        self._dfs = [self._generate_df(tp) for tp in tps]
        super().__init__(self._dfs)
        self._labels = [tp.id for tp in tps]

    def _generate_df(self, template_plate: TemplatePlates) -> pd.DataFrame:
        """
        Generates df that can be used in LayoutParser.
        """
        template_wells = {
            w for w in TemplateWells.select().where(TemplateWells.template_plate == template_plate)
        }
        template_treatments = {
            t
            for t in TemplateTreatments.select().where(
                TemplateTreatments.template_plate == template_plate
            )
        }
        n_rows = template_plate.plate_type.n_rows
        n_cols = template_plate.plate_type.n_columns
        well_parser = ParsingWB1(n_rows, n_cols)
        all_wells = {}
        for tw in template_wells:
            well_labels = well_parser.parse(tw.well_range_expression)
            # Add template_well information for every single well available
            for l in well_labels:
                all_wells[l] = {
                    "name": "",
                    "well": l,
                    "variant": tw.variant_expression,
                    "dpf": tw.age_expression,
                    "group": tw.group_expression,
                    "n": tw.n_expression,
                }
                if tw.control_type:
                    all_wells[l]["control"] = ControlTypes.fetch(tw.control_type.id).name
        for wt in template_treatments:
            well_labels = well_parser.parse(wt.well_range_expression)
            # Add template_treatment information for every single well available
            for l in well_labels:
                well_dict = all_wells[l]
                all_keys = list(well_dict.keys())
                # Assume dose is one-to-one mapping with batch
                dose_list = [int(s.split("_")[1]) for s in all_keys if "dose" in s]
                if dose_list:
                    num = max(dose_list) + 1
                else:
                    num = 1
                well_dict[f"dose_{num}"] = wt.dose_expression
                well_dict[f"batch_{num}"] = wt.batch_expression
        return pd.DataFrame(list(all_wells.values()))


class SubmissionLayoutVisualizer(TemplateLayoutVisualizer):
    """
    Takes in a Submission ID or Lookup_hash and returns out a TemplateLayoutVisualizer.
    """

    def __init__(self, submissions: Union[int, str, Sequence[Union[int, str, Submissions]]]):
        if isinstance(submissions, int) or isinstance(submissions, str):
            submissions = [submissions]
        submission_ids = [Submissions.fetch(s).id for s in submissions]
        sub_list = (
            Submissions.select(Submissions, Experiments)
            .join(Experiments)
            .where(Submissions.id << submission_ids)
        )
        tp_list = [sub.experiment.template_plate_id for sub in sub_list]
        super().__init__(tp_list)
        self._labels = submissions


class RunLayoutVisualizer(LayoutVisualizer):
    """
    Takes in a Run ID or Run object and returns a LayoutVisualizer.
    """

    def __init__(self, runs: Union[int, Runs, Sequence[Union[int, Runs]]]):
        if isinstance(runs, Collection):
            rs = [Runs.fetch(run) for run in runs]
        else:
            rs = [Runs.fetch(runs)]
        self._dfs = [self._generate_df(r) for r in rs]
        super().__init__(self._dfs)
        self._labels = [r.id for r in rs]

    def _generate_df(self, run: Runs) -> pd.DataFrame:
        """
        Generates df that can be used in LayoutParser.
        """
        wells = {w for w in Wells.select().where(Wells.run == run)}
        treatments = {t for t in WellTreatments.select().where(WellTreatments.well << wells)}
        pt = PlateTypes.fetch(run.experiment.template_plate.plate_type)
        n_rows = pt.n_rows
        n_cols = pt.n_columns
        well_parser = ParsingWB1(n_rows, n_cols)
        all_wells = {}
        for w in wells:
            label = well_parser.index_to_label(w.well_index)
            if w.variant is not None:
                v_name = w.variant.name
            else:
                v_name = None
            if w.control_type is not None:
                ct_name = w.control_type.name
            else:
                ct_name = None
            all_wells[label] = {
                "name": "",
                "well": label,
                "variant": v_name,
                "dpf": w.age,
                "group": w.well_group,
                "n": w.n,
                "control": ct_name,
            }
        for wt in treatments:
            label = well_parser.index_to_label(wt.well.well_index)
            well_dict = all_wells[label]
            all_keys = list(well_dict.keys())
            # Assume dose is one-to-one mapping with batch
            dose_list = [int(s.split("_")[1]) for s in all_keys if "dose" in s]
            if dose_list:
                num = max(dose_list) + 1
            else:
                num = 1
            well_dict[f"dose_{num}"] = wt.micromolar_dose
            well_dict[f"batch_{num}"] = wt.batch.lookup_hash
        return pd.DataFrame(list(all_wells.values()))


@abcd.auto_str()
@abcd.auto_repr()
@abcd.auto_eq()
class BatchGetter:
    """
    Useful for external batch sets.
    Maps structured names to batches rows from a regex pattern.
    """

    def __init__(self, pattern: str, prefix: str, controls: Mapping[str, Union[str, int, Batches]]):
        self._pattern = regex.compile(pattern, flags=regex.V1)
        self._prefix = prefix
        self._controls = {name: Batches.fetch(batch) for name, batch in controls}

    def get(self, name: str) -> Batches:
        name = name.lower()
        if name in self._controls[name]:
            return self._controls[name]
        s = self._pattern.match(name)
        assert s is not None, f"None for {name}"
        s = s.group(1)
        assert s is not None, f"None for {name}"
        return Batches.fetch(self._prefix + "." + str(s))


class DoseColumnIterator:
    """
    A weird class for the case where each batch has the same list of doses,
    which appear in order except for controls.
    For example, the initial Olson Lab set had a single compound per column,
    with doses from 100 down to 1.5625, but with one control per column in a semi-random row.
    """

    def __init__(self, dose_range: Iterable[float], ignore: set):
        self.dose_range = dose_range
        self._iters = defaultdict(lambda: iter(dose_range))
        self._numbers = defaultdict(lambda: 0)
        self._ignore = ignore

    def get(self, batch):
        if batch in self._ignore:
            return None
        try:
            x = next(self._iters[batch])
            self._numbers[batch] += 1
            return x
        except StopIteration:
            raise ValueError(
                f"Out of range on {batch} with {self._numbers[batch]} queries"
            ) from None


class LiteralImporter:
    """ """

    @classmethod
    def replace_run(cls, run: Union[Runs, int, str]) -> None:
        """
        Replaces Wells and WellTreatments.
        Does so according to their template_well and template_well treaments specified by the
        template_plate associated with its experiment.
        """
        run = Tools.run(run)
        Wells.delete().where(Wells.run == run).execute()
        plate = run.experiment.template_plate
        # all_well_labels = set()
        wb1 = ParsingWB1(plate.plate_type.n_rows, plate.plate_type.n_columns)
        for w in TemplateWells.select().where(TemplateWells.template_plate == plate):
            for w0 in wb1.parse(w.well_range_expression):
                new_well = Wells(
                    age=w.age_expression,
                    run=run,
                    well_index=wb1.label_to_index(w0),
                    control_type=w.control_type,
                    n=w.n_expression,
                    variant=GeneticVariants.fetch(w.variant_expression),
                    well_group=None,
                )
                new_well.save()
        for t in TemplateTreatments.select().where(TemplateTreatments.template_plate == plate):
            for w0 in wb1.parse(t.well_range_expression):
                new_wt = WellTreatments(
                    batch=Batches.fetch(t.batch_expression),
                    micromolar_dose=t.dose_expression,
                    well=Wells.select()
                    .where((Wells.run_id == run) & (Wells.well_index == wb1.label_to_index(w0)))
                    .first(),
                )
                new_wt.save()
        logger.notice(f"{run} has been replaced.")


__all__ = [
    "LayoutParser",
    "LayoutFrame",
    "LayoutVisualizer",
    "ParsingWB1",
    "LiteralImporter",
    "TemplateLayoutVisualizer",
    "SubmissionLayoutVisualizer",
    "RunLayoutVisualizer",
]
