package valar.insertion

import java.time.{LocalDate, LocalDateTime}

case class LoadData(
  template: Int,
  edit: Boolean
)


case class TransferData(
  name: String,
  description: Option[String],
  plateType: Byte,
        supplier: Int,
        parent: Option[Int],
        dilutionFactor: Option[Double],
        microliters: Option[Double],
  creator: Int
) {
}

/*
  Note that none of these are optional because they're expressions, not actual values.
  An empty string is translated to a null when processing the expression.
  */
case class LayoutData(
  name: String,
  description: Option[String],
  plateType: Byte,
  fishRanges: List[String],
  controls: List[Option[Byte]],
  nFish: List[String],
  ages: List[String],
  variants: List[String],
  groups: List[String],
  treatmentRanges: List[String],
  drugs: List[String],
  doses: List[String],
  creator: Int
) {
  require(Seq(fishRanges.size, controls.size, nFish.size, variants.size).distinct.size == 1, "Somehow an input field for wells is missing!")
  require(Seq(treatmentRanges.size, drugs.size, doses.size).distinct.size == 1, "Somehow an input field for treatments is missing!")
}

case class SubmissionData(
  experiment: Int,
  fishParameters: String,
  treatmentParameters: String,
  datetimePlated: LocalDateTime,
  datetimeDosed: Option[LocalDateTime],
  acclimationSecs: Int,
  creator: Int,
  personPlated: Int,
  description: String,
  notes: Option[String],
  rerunning: Boolean
)

case class TemplateAssayData(
  name: String,
  description: Option[String],
  ranges: List[String],
  stimuli: List[Int],
  values: List[String],
  creator: Int
) {
  require(Seq(ranges.size, stimuli.size, values.size).distinct.size == 1, "Somehow an input field for stimuli is missing!")
}

case class BatteryData(
  name: String,
  description: Option[String],
  notes: Option[String],
  assays: List[Int],
  params: List[String],
  creator: Int
) {
  require(Seq(assays.size, params.size).distinct.size == 1, "Somehow an input field for assays is missing!")
}

case class ExperimentData(
  name: String,
  description: Option[String],
  project: Int,
  battery: Int,
  templatePlate: Int,
  transferPlate: Option[Int],
  acclimationSecs: Int,
  notes: Option[String],
  creator: Int
)

case class ProjectData(
  name: String,
  projectType: Byte,
  description: Option[String],
  reason: Option[String],
  methods: Option[String],
  active: Boolean,
  creator: Int
)

case class VariantData(
  name: String,
  lineageType: String,
  mother: Option[Int],
  father: Option[Int],
  dateCreated: Option[LocalDate],
  notes: Option[String],
  creator: Int
) {
  val allLineageTypes = Set("injection", "cross", "selection", "wild-type")
  val lineageTypesPermittedHere = Set("cross", "selection", "wild-type")
  require(lineageTypesPermittedHere contains lineageType, "Bad lineage type")
  /*
  TODO
    .verifying("A wild-type cannot have a parent", data => data.lineageType != "wild-type" || data.father.isEmpty && data.mother.isEmpty)
    .verifying("A cross must have two parents", data => data.lineageType != "cross" || data.father.isDefined && data.mother.isDefined)
    .verifying("Selection and injection lineage type must have exactly one parent", data => data.lineageType != "selection" && data.lineageType != "injection" || data.father.isEmpty ^ data.mother.isEmpty)
   */
}

case class ConstructData(
  name: String,
  kind: String,
  supplier: Int,
  location: Int,
  box: Int,
  tube: Int,
  description: Option[String],
  ref: Int,
  pubmedId: Option[Int],
  pubLink: Option[String],
  personMade: Int,
  dateMade: Option[LocalDate],
  selectionMarker: Option[String],
  bacterialStrain: Option[String],
  vector: Option[String],
  rawFile: String,
  notes: Option[String],
  creator: Int
) {
  val allTypes = Set("plasmid", "guide", "morpholino", "other")
}

case class CompoundData(
  isFreshStock: Boolean,
  kind: String,
  supplier: Int,
  catalogNumber: Option[String],
  inchi: String,
  dateOrdered: LocalDate,
  boxNumber: Option[Int],
  wellNumber: Option[Int],
  location: Option[Int],
  locationNote: Option[String],
  amount: String,
  madeFrom: Option[String],
  molecularWeight: Option[Double],
  concentrationMillimolar: Option[Double],
  solvent: Int,
  compoundLabelsText: Option[String],
  batchLabelsText: Option[String],
  notes: Option[String],
  creator: Int
) {
  def hasInchi: Boolean = inchi.trim != "*"
  require(Set("compound", "mixture", "exposure", "blinded") contains kind, s"$kind is not a valid batch type")
  //require(isFreshStock || madeFrom.nonEmpty, s"If a dry stock, leave off 'box', 'well', and 'made from'. Otherwise fill out 'made from' and fill 'box' and 'well' if applicable.")
  //require(isFreshStock || amount.toLowerCase(Locale.ENGLISH).endsWith("mL"), s"If not a dry stock, use 'mL' for amount")
  def compoundLabels: Set[String] = extract(compoundLabelsText).toSet
  def batchLabels: Set[String] = extract(batchLabelsText).toSet
  private def extract(o: Option[String]): Seq[String] =
    o map (s => s.split("\n").toSeq map (_.trim) filter (_.nonEmpty)) getOrElse Seq.empty
}

case class CompoundLabelData(
  compoundId: Int,
  name: String,
  refId: Int
)

case class AnnotationData(
  run: Option[Int],
  submission: Option[Int],
  name: Option[String],
  description: Option[String],
  level: String,
  creator: Int
) {
  private val validLevels = Set("0:good", "1:note", "2:caution", "3:warning", "4:danger", "9:deleted", "to_fix", "fixed")
  require(validLevels contains level, s"Level $level is not valid; must be one of [${validLevels.mkString(",")}]")
}

object AnnotationData {
  val levels = Set("0:good", "1:note", "2:caution", "3:warning", "4:danger", "9:deleted", "to_fix", "fixed")
}
