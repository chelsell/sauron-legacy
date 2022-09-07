package valar.params.layouts.post

import scala.reflect.ClassTag
import com.typesafe.scalalogging.Logger
import pippin.grammars._
import pippin.grammars.params.{DollarSignParam, DollarSignSub, GridParameterizer, Ization}
import valar.core.{exec, loadDb}
import valar.params.ParamOrigin
import valar.params.layouts.{TooFewException, TooManyException}
import valar.params.layouts.post.LayoutGrammars._


/**
  * Provides converters from parameterizations to grid mappings of Valar objects.
  * Each parameter type has a single corresponding class inside this object.
  * This is the complete list:
  *   - CompoundParameterization (compound batch),  List\[BatchesRow\]
  *   - DoseParameterization (micromolar dose), List\[Double\]
  *   - ControlTypeParameterization, ControlTypesRow
  *   - NFishParameterization, Int
  *   - VariantParmameterization, Option[GeneticVariantsRow]
  *   - AgeParameterization, Option[Int]
  *   - WellGroupParameterization, Option[String]
  *
  * Each has a trait and a companion object.
  * The trait defines apply(TemplatePlatesRow, Ization) => Map\[PointLike, Seq\[O\]\]
  * The object defines build(TemplatePlatesRow, Ization) => Map\[Int, X\]
  * where the Int in the returned map are 1-based well indices
  * For example, WellGroupParameterization's object will return Map\[Int, Int\]
  * Whereas the trait will return Map\[Int, Seq\[Int\]\], even though there can only be one group per well.
  * For this reason, using the companion objects might be preferred.
  *
  */
object LayoutParameterizations {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  /**
    * A converter from parameterizations to grid mappings.
    * @tparam R The type of rows for parameters, either TemplateWellsRow or TemplateTreatmentsRow
    * @tparam O The return type, such as BatchesRow; a Seq\[O\] will always be returned
    */
  trait LayoutParameterization[R, O] {

    def apply(
        templatePlate: TemplatePlatesRow,
        ization: Map[DollarSignParam, DollarSignSub]
    )(implicit tag: ClassTag[O]): Map[PointLike, Seq[O]] = {
      val plateType = exec((PlateTypes filter (_.id === templatePlate.plateTypeId)).result).head
      val results = allRows(templatePlate).foldLeft(initCells(plateType))({ case (cellMap: Map[PointLike, Seq[O]], next) =>
        val cells = parseCells(plateType, next)
        val nextCells: Map[PointLike, Seq[O]] = parse(cells, valueFetcher(next), ization) map (i => i._1 -> i._2.toSeq)
        // add the values; do NOT replace elements in the map
        cellMap ++ (nextCells map (i => i._1 -> (cellMap(i._1) ++ i._2)))
      })
      // TODO
      //if (results.size < min) throw new TooFewException(origin, min, results.size)
      //if (results.size > max) throw new TooManyException(origin, max, results.size)
      results
    }

    /**
      * Fetches required parameters as rows from Valar.
      */
    protected def allRows(templatePlate: TemplatePlatesRow): Seq[R]

    protected def parseCells(plateType: PlateTypesRow, w: R): Seq[PointLike]
    protected def grammarFn(s: String): Option[O]
    protected def valueFetcher(r: R): String
    protected def min: Int
    protected def max: Int
    protected def origin: ParamOrigin
    protected def substitutionTestValue: String

    private def initCells(plateType: PlateTypesRow): Map[PointLike, Seq[O]] = {
      allCells(plateType.nRows, plateType.nColumns) map (cell => cell -> Seq.empty[O])
    }.toMap

    private def allCells(nRows: Int, nColumns: Int): Seq[PointLike] = {
      val grid = AlphanumericGrid(nRows, nColumns)
      grid.traversalRange(grid.Point(1, 1), grid.Point(nRows, nColumns))((i, j) => grid.Point(i, j)) // the need to define the implicit is unfortunate
    }

    private def parse(cells: Seq[PointLike], valueExpression: String, ization: Map[DollarSignParam, DollarSignSub]): Map[PointLike, Option[O]] = {
      new GridParameterizer().mapToValue(
        cells = cells,
        valueExpression = valueExpression,
        substitutions = ization
      ) map { case (point, value) => point -> grammarFn(value) }
    }
  }

  trait WellParameterization[O] extends LayoutParameterization[TemplateWellsRow, O] {
    override protected def allRows(templatePlate: TemplatePlatesRow): Seq[TemplateWellsRow] =
      exec((TemplateWells filter (_.templatePlateId === templatePlate.id)).result)
    override protected def parseCells(plateType: PlateTypesRow, w: TemplateWellsRow): Seq[PointLike] =
      GridRangeGrammar.eval(w.wellRangeExpression, plateType.nRows, plateType.nColumns)
    override protected val min = 0
    override protected val max = 1
  }

  trait TreatmentParameterization[O] extends LayoutParameterization[TemplateTreatmentsRow, O] {

    override protected def allRows(templatePlate: TemplatePlatesRow): Seq[TemplateTreatmentsRow] =
      exec((TemplateTreatments filter (_.templatePlateId === templatePlate.id)).result)

    override protected def parseCells(plateType: PlateTypesRow, w: TemplateTreatmentsRow): Seq[PointLike] =
      GridRangeGrammar.eval(w.wellRangeExpression, plateType.nRows, plateType.nColumns)
    override protected val min = 0
    override protected val max = Int.MaxValue
  }

  object ControlTypeParameterization extends WellParameterization[ControlTypesRow] {

    def build(templatePlate: TemplatePlatesRow): Map[Int, Option[ControlTypesRow]] =
      apply(templatePlate, Map.empty) map (kv => kv._1.index -> kv._2.headOption)

    override protected def grammarFn(s: String): Option[ControlTypesRow] = ControlTypeGrammar.apply(s)
    override protected def valueFetcher(r: TemplateWellsRow) = r.controlType map (_.toString) getOrElse "" // TODO I hate this
    override protected def origin: ParamOrigin = ParamOrigin.controlType
    override protected val substitutionTestValue: String = "1" // a control type ID
  }

  object VariantParameterization extends WellParameterization[GeneticVariantsRow] {

    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, Option[GeneticVariantsRow]] =
      apply(templatePlate, ization) map (kv => kv._1.index -> kv._2.headOption)

    override protected def grammarFn(s: String): Option[GeneticVariantsRow] = VariantGrammar.apply(s)
    override protected def valueFetcher(r: TemplateWellsRow) = r.variantExpression
    override protected def origin: ParamOrigin = ParamOrigin.variant
    override protected val substitutionTestValue: String = "\"Singapore\""
  }

  object NFishParameterization extends WellParameterization[Int] {

    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, Int] =
      apply(templatePlate, ization) map (kv => kv._1.index -> kv._2.head)

    override protected def grammarFn(s: String): Option[Int] = NFishGrammar.apply(s)
    override protected def origin: ParamOrigin = ParamOrigin.nFish
    override protected def valueFetcher(r: TemplateWellsRow) = r.nExpression
    override protected val substitutionTestValue: String = "10"
    override protected val min = 1 // mandatory
    override protected val max = 1
  }

  object AgeParameterization extends WellParameterization[Int] {
    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, Option[Int]] =
      apply(templatePlate, ization) map (kv => kv._1.index -> kv._2.headOption)
    override protected def grammarFn(s: String): Option[Int] = AgeGrammar.apply(s)
    override protected def valueFetcher(r: TemplateWellsRow) = r.ageExpression
    override protected def origin: ParamOrigin = ParamOrigin.ageDpf
    override protected def substitutionTestValue: String = "20"
  }

  object WellGroupParameterization extends WellParameterization[String] {

    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, Option[String]] =
      apply(templatePlate, ization) map (kv => kv._1.index -> kv._2.headOption)

    override protected def grammarFn(s: String): Option[String] = WellGroupGrammar.apply(s)
    override protected def valueFetcher(r: TemplateWellsRow) = r.groupExpression
    override protected def origin: ParamOrigin = ParamOrigin.group
    override protected def substitutionTestValue: String = "\"hello\""
  }

  object CompoundParameterization extends TreatmentParameterization[BatchesRow] {

    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, List[BatchesRow]] =
      apply(templatePlate, ization mapValues fillLibrary) map (kv => kv._1.index -> kv._2.toList)

    override protected def grammarFn(s: String): Option[BatchesRow] = CompoundGrammar.apply(s)
    override protected def valueFetcher(r: TemplateTreatmentsRow) = r.batchExpression
    override protected def origin: ParamOrigin = ParamOrigin.compound
    override protected def substitutionTestValue: String = "\"oc_13095e6e514\"" // DMSO

    private def fillLibrary(sub: DollarSignSub): DollarSignSub = {
      if (sub.values.head.startsWith("/") && sub.values.head.endsWith("/") || sub.values.head.startsWith("[/") && sub.values.head.endsWith("/]")) {
        val plate = if (sub.values.head.startsWith("[/")) sub.values.head.substring(2).stripSuffix("/]") else sub.values.head.substring(1).stripSuffix("/")
        val ocs = exec((
          Batches filter (_.legacyInternalId.startsWith(plate)) sortBy (_.legacyInternalId)
          ).result)
        DollarSignSub(sub.key, ocs.toList map (_.lookupHash))
      } else sub
    }
  }

  object DoseParameterization extends TreatmentParameterization[Double] {
    def build(templatePlate: TemplatePlatesRow, ization: Map[DollarSignParam, DollarSignSub]): Map[Int, List[Double]] =
      apply(templatePlate, ization) map (kv => kv._1.index -> kv._2.toList)
    override protected def grammarFn(s: String): Option[Double] = DoseGrammar.apply(s)
    override protected def valueFetcher(r: TemplateTreatmentsRow) = r.doseExpression
    override protected def origin: ParamOrigin = ParamOrigin.dose
    override protected def substitutionTestValue: String = "0.1"
  }

}
