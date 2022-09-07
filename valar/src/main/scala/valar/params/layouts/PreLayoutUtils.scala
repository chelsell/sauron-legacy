package valar.params.layouts

import com.typesafe.scalalogging.Logger
import pippin.grammars.GridRangeGrammar
import pippin.grammars.params.{DollarSignParam, DollarSignParams, DollarSignSub, TextToParameterization}
import valar.core.CommonQueries.{listPlateTypes, listTemplateTreatments, listTemplateWells}
import valar.core.{loadDb, exec}
import valar.params.{ParamOrigin, PlateParam}


object PreLayoutUtils {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def missingWells(wellRangeExpressions: Seq[String], plateType: PlateTypesRow): Set[(Int, Int)] = {
    val requiredPoints = for (r <- 1 to plateType.nRows; c <- 1 to plateType.nColumns) yield (r, c)
    val actualPoints = wellRangeExpressions flatMap { fishRange =>
      GridRangeGrammar.eval(fishRange, nRows = plateType.nRows, nColumns = plateType.nColumns)
    } map (p => (p.row, p.column))
    requiredPoints.toSet -- actualPoints.toSet
  }

  def overlappingWells(wellRangeExpressions: Seq[String], plateType: PlateTypesRow): Set[Int] = {
    val pointLists = (wellRangeExpressions filterNot (_.trim.isEmpty) map {fishRange =>
      GridRangeGrammar.eval(fishRange, nRows = plateType.nRows, nColumns = plateType.nColumns)
    }).zipWithIndex
    var totalIntersection = collection.mutable.HashSet.empty[Int]
    for (a <- pointLists; b <- pointLists) yield {
      if (a._2 != b._2) {
        totalIntersection ++= (a._1.map(_.index).toSet intersect b._1.map(_.index).toSet)
      }
    }
    totalIntersection.toSet
  }

  def listWellParams(templatePlateId: Int): Set[PlateParam] = {
    val templatePlate = exec((TemplatePlates filter (_.id === templatePlateId)).result).head
    listWellParams(templatePlate)
  }
  def listWellParams(templatePlate: TemplatePlatesRow): Set[PlateParam] = {
    val plateType = (listPlateTypes filter (_.id == templatePlate.plateTypeId)).head
    val wells = listTemplateWells filter (_.templatePlateId == templatePlate.id)
    wells flatMap { well =>
      val wellSize = GridRangeGrammar.eval(well.wellRangeExpression, plateType.nRows, plateType.nColumns).size
      def f(s: String, o: ParamOrigin) = fetch(plateType, wellSize, s, o)
      Set(
        f(well.variantExpression, ParamOrigin.variant),
        f(well.nExpression, ParamOrigin.nFish),
        f(well.ageExpression, ParamOrigin.ageDpf),
        f(well.groupExpression, ParamOrigin.group)
      ).flatten
    } filterNot (_.param.isPredefined)
  }.toSet

  def listTreatmentParams(templatePlateId: Int): Set[PlateParam] = {
    val templatePlate = exec((TemplatePlates filter (_.id === templatePlateId)).result).head
    listTreatmentParams(templatePlate)
  }
  def listTreatmentParams(templatePlate: TemplatePlatesRow): Set[PlateParam] = {
    val plateType = (listPlateTypes filter (_.id == templatePlate.plateTypeId)).head
    val treatments = listTemplateTreatments filter (_.templatePlateId == templatePlate.id)
    treatments flatMap { treatment =>
      val wellSize = GridRangeGrammar.eval(treatment.wellRangeExpression, plateType.nRows, plateType.nColumns).size
      def f(s: String, o: ParamOrigin) = fetch(plateType, wellSize, s, o)
      Set(
        f(treatment.batchExpression, ParamOrigin.compound),
        f(treatment.doseExpression, ParamOrigin.dose)
      ).flatten
    } filterNot (_.param.isPredefined)
  }.toSet

  def parseWellParams(text: String, templatePlate: TemplatePlatesRow): Map[PlateParam, DollarSignSub] = {
    parseParams(text, PreLayoutUtils.listWellParams(templatePlate))
  }

  def parseTreatmentParams(text: String, templatePlate: TemplatePlatesRow): Map[PlateParam, DollarSignSub] = {
    parseParams(text, PreLayoutUtils.listTreatmentParams(templatePlate))
  }

  def parseParams(text: String, expectedParams: Set[PlateParam]): Map[PlateParam, DollarSignSub] = {
    val parser = new TextToParameterization(failOnUnexpected = true, quote = false)
    val lengths = (expectedParams map (p => p.param.name -> p.length)).toMap
    val lookup = (expectedParams map (ep => ep.param -> ep)).toMap
    parser.parse(text, expectedParams map (_.param), lengths).values map { paramSub =>
      lookup(paramSub.key) -> paramSub
    }
  }.toMap

  private def fetch(plateType: PlateTypesRow, wellSize: Int, expression: String, origin: ParamOrigin): Set[PlateParam] = {
    (
      DollarSignParams.find(expression, predefinedParams)
      map (p => PlateParam(p, origin, if (p.isList) wellSize else 1))
    )
  }

  /**
    * Return the names of params that don't match in origin or length to other params with the same name.
    */
  def mismatches(params: Set[PlateParam]): Set[String] = {
    val groups = params.toSeq.groupBy(_.param.name) // toSeq so we can allow duplicates of length & origin
     (groups filter { case (name: String, seq: Seq[PlateParam]) =>
       (seq map (_.length)).distinct.size > 1 || (seq map (_.origin)).distinct.size > 1
     }).keys
  }.toSet

  val predefinedParams: Set[String] = Set("$r", "$c", "$i")

}
