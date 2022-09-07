import os as __os
from datetime import datetime as __datetime
from pathlib import PurePath as __PurePath
from typing import Iterable as __Iterable
from typing import Sequence as __Sequence
from typing import Tuple as __Tup
from typing import Union as __Union

import peewee
from peewee import *

from valarpy.metamodel import BaseModel, EnumField

# for convenience with prior code
from valarpy.micromodels import (
    ValarTableTypeError,
    ValarLookupError,
    WriteNotEnabledError,
    UnsupportedOperationError,
)


class Suppliers(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(null=True)
    name = CharField(unique=True)

    class Meta:
        table_name = "suppliers"


class PlateTypes(BaseModel):  # pragma: no cover
    n_columns = IntegerField()
    n_rows = IntegerField()
    name = CharField(null=True)
    opacity = EnumField(choices=("opaque", "transparent"))  # auto-corrected to Enum
    part_number = CharField(index=True, null=True)
    supplier = ForeignKeyField(column_name="supplier_id", field="id", model=Suppliers, null=True)
    well_shape = EnumField(choices=("round", "square", "rectangular"))  # auto-corrected to Enum

    class Meta:
        table_name = "plate_types"
        indexes = ((("n_rows", "n_columns"), False),)


class Users(BaseModel):  # pragma: no cover
    bcrypt_hash = CharField(index=True, null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    first_name = CharField(index=True)
    last_name = CharField(index=True)
    username = CharField(unique=True)
    write_access = IntegerField(constraints=[SQL("DEFAULT 1")], index=True)

    class Meta:
        table_name = "users"


class Plates(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_plated = DateTimeField(index=True, null=True)
    person_plated = ForeignKeyField(column_name="person_plated_id", field="id", model=Users)
    plate_type = ForeignKeyField(
        column_name="plate_type_id", field="id", model=PlateTypes, null=True
    )

    class Meta:
        table_name = "plates"


class TransferPlates(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    creator = ForeignKeyField(column_name="creator_id", field="id", model=Users)
    datetime_created = DateTimeField()
    description = CharField(null=True)
    dilution_factor_from_parent = FloatField(null=True)
    initial_ul_per_well = FloatField()
    name = CharField(unique=True)
    parent = ForeignKeyField(column_name="parent_id", field="id", model="self", null=True)
    plate_type = ForeignKeyField(column_name="plate_type_id", field="id", model=PlateTypes)
    supplier = ForeignKeyField(column_name="supplier_id", field="id", model=Suppliers, null=True)

    class Meta:
        table_name = "transfer_plates"


class Batteries(BaseModel):  # pragma: no cover
    assays_sha1 = BlobField(index=True)  # auto-corrected to BlobField
    author = ForeignKeyField(column_name="author_id", field="id", model=Users, null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(null=True)
    hidden = IntegerField(constraints=[SQL("DEFAULT 0")])
    length = IntegerField(index=True)
    name = CharField(unique=True)
    notes = CharField(null=True)
    template = IntegerField(column_name="template_id", index=True, null=True)

    class Meta:
        table_name = "batteries"


class ProjectTypes(BaseModel):  # pragma: no cover
    description = TextField()
    name = CharField(unique=True)

    class Meta:
        table_name = "project_types"


class Projects(BaseModel):  # pragma: no cover
    active = IntegerField(constraints=[SQL("DEFAULT 1")])
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    creator = ForeignKeyField(column_name="creator_id", field="id", model=Users)
    description = CharField(null=True)
    methods = TextField(null=True)
    name = CharField(unique=True)
    reason = TextField(null=True)
    type = ForeignKeyField(column_name="type_id", field="id", model=ProjectTypes, null=True)

    class Meta:
        table_name = "projects"


class TemplatePlates(BaseModel):  # pragma: no cover
    author = ForeignKeyField(column_name="author_id", field="id", model=Users)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(null=True)
    hidden = IntegerField(constraints=[SQL("DEFAULT 0")])
    name = CharField(unique=True)
    plate_type = ForeignKeyField(column_name="plate_type_id", field="id", model=PlateTypes)
    specializes = ForeignKeyField(column_name="specializes", field="id", model="self", null=True)

    class Meta:
        table_name = "template_plates"


class Experiments(BaseModel):  # pragma: no cover
    active = IntegerField(constraints=[SQL("DEFAULT 1")])
    battery = ForeignKeyField(column_name="battery_id", field="id", model=Batteries)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    creator = ForeignKeyField(column_name="creator_id", field="id", model=Users)
    default_acclimation_sec = IntegerField()
    description = CharField(null=True)
    name = CharField(unique=True)
    notes = TextField(null=True)
    project = ForeignKeyField(column_name="project_id", field="id", model=Projects)
    template_plate = ForeignKeyField(
        column_name="template_plate_id", field="id", model=TemplatePlates, null=True
    )
    transfer_plate = ForeignKeyField(
        column_name="transfer_plate_id", field="id", model=TransferPlates, null=True
    )

    class Meta:
        table_name = "experiments"


class ExperimentTags(BaseModel):  # pragma: no cover
    name = CharField()
    experiment = ForeignKeyField(column_name="experiment_id", field="id", model=Experiments)
    value = CharField()

    class Meta:
        table_name = "experiment_tags"
        indexes = ((("experiment", "name"), True),)


class Saurons(BaseModel):  # pragma: no cover
    active = IntegerField(constraints=[SQL("DEFAULT 0")], index=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField(unique=True)

    class Meta:
        table_name = "saurons"


class SauronConfigs(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_changed = DateTimeField()
    description = TextField()
    sauron = ForeignKeyField(column_name="sauron_id", field="id", model=Saurons)

    class Meta:
        table_name = "sauron_configs"
        indexes = ((("sauron", "datetime_changed"), True),)


class Submissions(BaseModel):  # pragma: no cover
    acclimation_sec = IntegerField(null=True)
    continuing = ForeignKeyField(column_name="continuing_id", field="id", model="self", null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_dosed = DateTimeField(null=True)
    datetime_plated = DateTimeField()
    description = CharField()
    experiment = ForeignKeyField(column_name="experiment_id", field="id", model=Experiments)
    lookup_hash = CharField(unique=True)
    notes = TextField(null=True)
    person_plated = ForeignKeyField(column_name="person_plated_id", field="id", model=Users)
    user = ForeignKeyField(backref="users_user_set", column_name="user_id", field="id", model=Users)

    class Meta:
        table_name = "submissions"


class ConfigFiles(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    text_sha1 = BlobField(index=True)  # auto-corrected to BlobField
    toml_text = TextField()

    class Meta:
        table_name = "config_files"


class Runs(BaseModel):  # pragma: no cover
    acclimation_sec = IntegerField(index=True, null=True)
    config_file = ForeignKeyField(
        column_name="config_file_id", field="id", model=ConfigFiles, null=True
    )
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_dosed = DateTimeField(index=True, null=True)
    datetime_run = DateTimeField(index=True)
    description = CharField()
    experiment = ForeignKeyField(column_name="experiment_id", field="id", model=Experiments)
    experimentalist = ForeignKeyField(column_name="experimentalist_id", field="id", model=Users)
    incubation_min = IntegerField(index=True, null=True)
    name = CharField(null=True, unique=True)
    notes = TextField(null=True)
    plate = ForeignKeyField(column_name="plate_id", field="id", model=Plates)
    sauron_config = ForeignKeyField(column_name="sauron_config_id", field="id", model=SauronConfigs)
    submission = ForeignKeyField(
        column_name="submission_id", field="id", model=Submissions, null=True, unique=True
    )
    tag = CharField(constraints=[SQL("DEFAULT ''")], unique=True)

    class Meta:
        table_name = "runs"


class TemplateAssays(BaseModel):  # pragma: no cover
    author = ForeignKeyField(column_name="author_id", field="id", model=Users, null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(null=True)
    name = CharField(unique=True)
    specializes = ForeignKeyField(column_name="specializes", field="id", model="self", null=True)

    class Meta:
        table_name = "template_assays"


class Assays(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(null=True)
    frames_sha1 = BlobField(index=True)  # auto-corrected to BlobField
    hidden = IntegerField(constraints=[SQL("DEFAULT 0")])
    length = IntegerField()
    name = CharField(unique=True)
    template_assay = ForeignKeyField(
        column_name="template_assay_id", field="id", model=TemplateAssays, null=True
    )

    class Meta:
        table_name = "assays"
        indexes = ((("name", "frames_sha1"), True),)


class ControlTypes(BaseModel):  # pragma: no cover
    description = CharField()
    drug_related = IntegerField(constraints=[SQL("DEFAULT 1")], index=True)
    genetics_related = IntegerField(index=True)
    name = CharField(unique=True)
    positive = IntegerField(index=True)

    class Meta:
        table_name = "control_types"


class GeneticVariants(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    creator = ForeignKeyField(column_name="creator_id", field="id", model=Users)
    date_created = DateField(null=True)
    father = ForeignKeyField(column_name="father_id", field="id", model="self", null=True)
    fully_annotated = IntegerField(constraints=[SQL("DEFAULT 0")])
    lineage_type = EnumField(
        choices=("injection", "cross", "selection", "wild-type"), index=True, null=True
    )  # auto-corrected to Enum
    mother = ForeignKeyField(
        backref="genetic_variants_mother_set",
        column_name="mother_id",
        field="id",
        model="self",
        null=True,
    )
    name = CharField(unique=True)
    notes = TextField(null=True)

    class Meta:
        table_name = "genetic_variants"


class Wells(BaseModel):  # pragma: no cover
    age = IntegerField(null=True)
    control_type = ForeignKeyField(
        column_name="control_type_id", field="id", model=ControlTypes, null=True
    )
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    n = IntegerField(constraints=[SQL("DEFAULT 0")], index=True)
    run = ForeignKeyField(column_name="run_id", field="id", model=Runs)
    variant = ForeignKeyField(
        column_name="variant_id", field="id", model=GeneticVariants, null=True
    )
    well_group = CharField(index=True, null=True)
    well_index = IntegerField(index=True)

    class Meta:
        table_name = "wells"
        indexes = ((("run", "well_index"), True),)


class Annotations(BaseModel):  # pragma: no cover
    annotator = ForeignKeyField(column_name="annotator_id", field="id", model=Users)
    assay = ForeignKeyField(column_name="assay_id", field="id", model=Assays, null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = TextField(null=True)
    level = EnumField(
        choices=(
            "0:good",
            "1:note",
            "2:caution",
            "3:warning",
            "4:danger",
            "9:deleted",
            "to_fix",
            "fixed",
        ),
        constraints=[SQL("DEFAULT '1:note'")],
        index=True,
    )  # auto-corrected to Enum
    name = CharField(index=True, null=True)
    run = ForeignKeyField(column_name="run_id", field="id", model=Runs, null=True)
    submission = ForeignKeyField(
        column_name="submission_id", field="id", model=Submissions, null=True
    )
    value = CharField(null=True)
    well = ForeignKeyField(column_name="well_id", field="id", model=Wells, null=True)

    class Meta:
        table_name = "annotations"


class AssayParams(BaseModel):  # pragma: no cover
    assay = ForeignKeyField(column_name="assay_id", field="id", model=Assays)
    name = CharField()
    value = FloatField()

    class Meta:
        table_name = "assay_params"
        indexes = ((("name", "assay"), True),)


class AssayPositions(BaseModel):  # pragma: no cover
    assay = ForeignKeyField(column_name="assay_id", field="id", model=Assays)
    battery = ForeignKeyField(column_name="battery_id", field="id", model=Batteries)
    start = IntegerField(index=True)

    class Meta:
        table_name = "assay_positions"
        indexes = ((("battery", "assay", "start"), True),)


class AudioFiles(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    creator = ForeignKeyField(column_name="creator_id", field="id", model=Users, null=True)
    data = BlobField()  # auto-corrected to BlobField
    filename = CharField(unique=True)
    n_seconds = FloatField()
    notes = CharField(null=True)
    sha1 = BlobField(unique=True)  # auto-corrected to BlobField

    class Meta:
        table_name = "audio_files"


class Locations(BaseModel):  # pragma: no cover
    active = IntegerField(constraints=[SQL("DEFAULT 1")])
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = CharField(constraints=[SQL("DEFAULT ''")])
    name = CharField(unique=True)
    part_of = ForeignKeyField(column_name="part_of", field="id", model="self", null=True)
    purpose = CharField(constraints=[SQL("DEFAULT ''")])
    temporary = IntegerField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = "locations"


class Refs(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_downloaded = DateTimeField(null=True)
    description = CharField(null=True)
    external_version = CharField(index=True, null=True)
    name = CharField(unique=True)
    url = CharField(index=True, null=True)

    @property
    def sstring(self) -> str:
        """Short string of the ID. This can be overridden."""
        return "ref." + str(self.id)

    class Meta:
        table_name = "refs"


class Compounds(BaseModel):  # pragma: no cover
    chembl = CharField(column_name="chembl_id", index=True, null=True)
    chemspider = IntegerField(column_name="chemspider_id", null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    inchi = CharField()
    inchikey = CharField(unique=True)
    inchikey_connectivity = CharField(index=True)
    smiles = CharField(null=True)

    class Meta:
        table_name = "compounds"


class Batches(BaseModel):  # pragma: no cover
    amount = CharField(null=True)
    box_number = IntegerField(index=True, null=True)
    compound = ForeignKeyField(column_name="compound_id", field="id", model=Compounds, null=True)
    concentration_millimolar = FloatField(null=True)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    date_ordered = DateField(index=True, null=True)
    legacy_internal = CharField(column_name="legacy_internal_id", index=True, null=True)
    location = ForeignKeyField(column_name="location_id", field="id", model=Locations, null=True)
    location_note = CharField(null=True)
    lookup_hash = CharField(unique=True)
    made_from = ForeignKeyField(column_name="made_from_id", field="id", model="self", null=True)
    molecular_weight = FloatField(null=True)
    notes = TextField(null=True)
    person_ordered = ForeignKeyField(
        column_name="person_ordered", field="id", model=Users, null=True
    )
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs, null=True)
    solvent = IntegerField(column_name="solvent_id", index=True, null=True)
    # hide to make queries easier
    # solvent = ForeignKeyField(backref='compounds_solvent_set', column_name='solvent_id', field='id', model=Compounds, null=True)
    supplier_catalog_number = CharField(null=True)
    supplier = ForeignKeyField(column_name="supplier_id", field="id", model=Suppliers, null=True)
    tag = CharField(null=True, unique=True)
    well_number = IntegerField(index=True, null=True)

    class Meta:
        table_name = "batches"
        indexes = ((("box_number", "well_number"), True),)


class BatchLabels(BaseModel):  # pragma: no cover
    batch = ForeignKeyField(column_name="batch_id", field="id", model=Batches)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField(index=True)
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "batch_labels"


class Sensors(BaseModel):  # pragma: no cover
    blob_type = EnumField(
        choices=(
            "assay_start",
            "protocol_start",
            "every_n_milliseconds",
            "every_n_frames",
            "arbitrary",
        ),
        null=True,
    )  # auto-corrected to Enum
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    data_type = EnumField(
        choices=(
            "byte",
            "short",
            "int",
            "float",
            "double",
            "unsigned_byte",
            "unsigned_short",
            "unsigned_int",
            "unsigned_float",
            "unsigned_double",
            "utf8_char",
            "long",
            "unsigned_long",
            "other",
        )
    )  # auto-corrected to Enum
    description = CharField(null=True)
    n_between = IntegerField(null=True)
    name = CharField(unique=True)

    class Meta:
        table_name = "sensors"


class Stimuli(BaseModel):  # pragma: no cover
    analog = IntegerField(constraints=[SQL("DEFAULT 0")])
    audio_file = ForeignKeyField(
        column_name="audio_file_id", field="id", model=AudioFiles, null=True, unique=True
    )
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    default_color = CharField()
    description = CharField(null=True)
    name = CharField(unique=True)
    rgb = BlobField(null=True)  # auto-corrected to BlobField
    wavelength_nm = IntegerField(null=True)

    @property
    def sstring(self) -> str:
        """Short string of the ID. This can be overridden."""
        return "stim." + str(self.id)

    class Meta:
        table_name = "stimuli"


class CompoundLabels(BaseModel):  # pragma: no cover
    compound = ForeignKeyField(column_name="compound_id", field="id", model=Compounds)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField()
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "compound_labels"


class Features(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    data_type = EnumField(
        choices=(
            "byte",
            "short",
            "int",
            "float",
            "double",
            "unsigned_byte",
            "unsigned_short",
            "unsigned_int",
            "unsigned_float",
            "unsigned_double",
            "utf8_char",
        ),
        constraints=[SQL("DEFAULT 'float'")],
    )  # auto-corrected to Enum
    description = CharField()
    dimensions = CharField()
    name = CharField(unique=True)

    class Meta:
        table_name = "features"


class LogFiles(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    run = ForeignKeyField(column_name="run_id", field="id", model=Runs)
    text = TextField()
    text_sha1 = BlobField(index=True)  # auto-corrected to BlobField

    class Meta:
        table_name = "log_files"


class MandosInfo(BaseModel):  # pragma: no cover
    compound = ForeignKeyField(column_name="compound_id", field="id", model=Compounds)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField(index=True)
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)
    value = CharField(index=True)

    class Meta:
        table_name = "mandos_info"
        indexes = ((("name", "ref", "compound"), True),)


class MandosObjects(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    external = CharField(column_name="external_id", index=True)
    name = CharField(null=True)
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "mandos_objects"
        indexes = ((("ref", "external_id"), True),)


class MandosObjectLinks(BaseModel):  # pragma: no cover
    child = ForeignKeyField(column_name="child_id", field="id", model=MandosObjects)
    parent = ForeignKeyField(
        backref="mandos_objects_parent_set",
        column_name="parent_id",
        field="id",
        model=MandosObjects,
    )
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "mandos_object_links"


class MandosObjectTags(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField()
    object = ForeignKeyField(column_name="object", field="id", model=MandosObjects)
    ref = ForeignKeyField(column_name="ref", field="id", model=Refs)
    value = CharField(index=True)

    class Meta:
        table_name = "mandos_object_tags"
        indexes = ((("object", "ref", "name", "value"), True),)


class MandosPredicates(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    external = CharField(column_name="external_id", index=True, null=True)
    kind = EnumField(choices=("target", "class", "indication", "other"))  # auto-corrected to Enum
    name = CharField(index=True)
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "mandos_predicates"
        indexes = (
            (("external_id", "ref"), True),
            (("name", "ref"), True),
        )


class MandosRules(BaseModel):  # pragma: no cover
    compound = ForeignKeyField(column_name="compound_id", field="id", model=Compounds)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    external = CharField(column_name="external_id", index=True, null=True)
    object = ForeignKeyField(column_name="object_id", field="id", model=MandosObjects)
    predicate = ForeignKeyField(column_name="predicate_id", field="id", model=MandosPredicates)
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)

    class Meta:
        table_name = "mandos_rules"
        indexes = ((("ref", "compound", "object", "predicate"), True),)


class MandosRuleTags(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField()
    ref = ForeignKeyField(column_name="ref", field="id", model=Refs)
    rule = ForeignKeyField(column_name="rule", field="id", model=MandosRules)
    value = CharField(index=True)

    class Meta:
        table_name = "mandos_rule_tags"
        indexes = ((("rule", "ref", "name", "value"), True),)


class Rois(BaseModel):  # pragma: no cover
    ref = ForeignKeyField(column_name="ref_id", field="id", model=Refs)
    well = ForeignKeyField(column_name="well_id", field="id", model=Wells)
    x0 = IntegerField()
    x1 = IntegerField()
    y0 = IntegerField()
    y1 = IntegerField()

    @property
    def sstring(self) -> str:
        """Short string of the ID. This can be overridden."""
        return "roi." + str(self.id)

    class Meta:
        table_name = "rois"


class RunTags(BaseModel):  # pragma: no cover
    name = CharField()
    run = ForeignKeyField(column_name="run_id", field="id", model=Runs)
    value = CharField()

    class Meta:
        table_name = "run_tags"
        indexes = ((("run", "name"), True),)


class SauronSettings(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    name = CharField(index=True)
    sauron_config = ForeignKeyField(column_name="sauron_config_id", field="id", model=SauronConfigs)
    value = CharField()

    class Meta:
        table_name = "sauron_settings"
        indexes = ((("sauron_config", "name"), True),)


class SensorData(BaseModel):  # pragma: no cover
    floats = BlobField()  # auto-corrected to BlobField
    floats_sha1 = BlobField(index=True)  # auto-corrected to BlobField
    run = ForeignKeyField(column_name="run_id", field="id", model=Runs)
    sensor = ForeignKeyField(column_name="sensor_id", field="id", model=Sensors)

    class Meta:
        table_name = "sensor_data"


class StimulusFrames(BaseModel):  # pragma: no cover
    assay = ForeignKeyField(column_name="assay_id", field="id", model=Assays)
    frames = BlobField()  # auto-corrected to BlobField
    frames_sha1 = BlobField(index=True)  # auto-corrected to BlobField
    stimulus = ForeignKeyField(column_name="stimulus_id", field="id", model=Stimuli)

    class Meta:
        table_name = "stimulus_frames"
        indexes = ((("assay", "stimulus"), True),)


class SubmissionParams(BaseModel):  # pragma: no cover
    name = CharField()
    param_type = EnumField(
        choices=("n_fish", "compound", "dose", "variant", "dpf", "group")
    )  # auto-corrected to Enum
    submission = ForeignKeyField(column_name="submission_id", field="id", model=Submissions)
    value = CharField()

    class Meta:
        table_name = "submission_params"
        indexes = ((("submission", "name"), True),)


class SubmissionRecords(BaseModel):  # pragma: no cover
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    datetime_modified = DateTimeField()
    sauron = ForeignKeyField(column_name="sauron_id", field="id", model=Saurons)
    status = CharField(index=True)
    submission = ForeignKeyField(column_name="submission_id", field="id", model=Submissions)

    class Meta:
        table_name = "submission_records"
        indexes = ((("submission", "status", "datetime_modified"), True),)


class TemplateStimulusFrames(BaseModel):  # pragma: no cover
    range_expression = CharField()
    stimulus = ForeignKeyField(column_name="stimulus_id", field="id", model=Stimuli)
    template_assay = ForeignKeyField(
        column_name="template_assay_id", field="id", model=TemplateAssays
    )
    value_expression = CharField()

    class Meta:
        table_name = "template_stimulus_frames"


class TemplateTreatments(BaseModel):  # pragma: no cover
    batch_expression = CharField()
    dose_expression = CharField()
    template_plate = ForeignKeyField(
        column_name="template_plate_id", field="id", model=TemplatePlates
    )
    well_range_expression = CharField()

    class Meta:
        table_name = "template_treatments"


class TemplateWells(BaseModel):  # pragma: no cover
    age_expression = CharField()
    control_type = ForeignKeyField(
        column_name="control_type_id", field="id", model=ControlTypes, null=True
    )
    group_expression = CharField()
    n_expression = CharField()
    template_plate = ForeignKeyField(
        column_name="template_plate_id", field="id", model=TemplatePlates
    )
    variant_expression = CharField()
    well_range_expression = CharField()

    class Meta:
        table_name = "template_wells"


class WellFeatures(BaseModel):  # pragma: no cover
    floats = BlobField()  # auto-corrected to BlobField
    sha1 = BlobField(index=True)  # auto-corrected to BlobField
    type = ForeignKeyField(column_name="type_id", field="id", model=Features)
    well = ForeignKeyField(column_name="well_id", field="id", model=Wells)

    class Meta:
        table_name = "well_features"


class WellTreatments(BaseModel):  # pragma: no cover
    batch = ForeignKeyField(column_name="batch_id", field="id", model=Batches)
    micromolar_dose = FloatField(null=True)
    well = ForeignKeyField(column_name="well_id", field="id", model=Wells)

    class Meta:
        table_name = "well_treatments"
        indexes = ((("well", "batch"), True),)


class BatchAnnotations(BaseModel):  # pragma: no cover
    annotator = ForeignKeyField(column_name="annotator_id", field="id", model=Users)
    batch = ForeignKeyField(column_name="batch_id", field="id", model=Batches, null=False)
    created = DateTimeField(constraints=[SQL("DEFAULT current_timestamp()")])
    description = TextField(null=True)
    level = EnumField(
        choices=("0:good", "1:note", "2:caution", "3:warning", "4:danger", "9:deleted"),
        constraints=[SQL("DEFAULT '1:note'")],
        index=True,
    )  # auto-corrected to Enum
    name = CharField(index=True, null=True)
    value = CharField(null=True)

    class Meta:
        table_name = "batch_annotations"


ExpressionLike = peewee.ColumnBase
ExpressionsLike = __Union[ExpressionLike, __Iterable[ExpressionLike]]
PathLike = __Union[str, __PurePath, __os.PathLike]
RunLike = __Union[int, str, Runs, Submissions]
ControlLike = __Union[int, str, ControlTypes]
SubmissionLike = __Union[int, str, Submissions]
RoiLike = __Union[int, Rois, __Tup[__Union[int, str, Wells], __Union[int, str, Refs]]]
RunsLike = __Union[RunLike, __Iterable[RunLike]]
SauronLike = __Union[int, str, Saurons]
SauronConfigLike = __Union[int, SauronConfigs, __Tup[__Union[Saurons, int, str], __datetime]]
BatteryLike = __Union[int, str, Batteries]
AssayLike = __Union[int, str, Assays]
UserLike = __Union[int, str, Users]
RefLike = __Union[int, str, Refs]
TempPlateLike = __Union[int, str, TemplatePlates]
SupplierLike = __Union[int, str, Suppliers]
BatchLike = __Union[int, str, Batches]
CompoundLike = __Union[int, str, Compounds]
NullableCompoundLike = __Union[None, int, str, Compounds]
SensorLike = __Union[int, str, Sensors]
SensorDataLike = __Union[None, __Sequence[float], bytes, str]
StimulusLike = __Union[Stimuli, int, str]
CompoundsLike = __Union[CompoundLike, __Iterable[CompoundLike]]
BatchesLike = __Union[BatchLike, __Iterable[BatchLike]]
NullableCompoundsLike = __Union[
    None, Compounds, int, str, __Iterable[__Union[None, Compounds, int, str]]
]
