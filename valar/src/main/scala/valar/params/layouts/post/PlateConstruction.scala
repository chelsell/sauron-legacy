package valar.params.layouts.post

import com.typesafe.scalalogging.LazyLogging
import pippin.grammars.{GrammarException, GridRangeGrammar, PointLike}
import pippin.grammars.params.{DollarSignParam, DollarSignSub}
import valar.params.layouts.post.LayoutParameterizations.{AgeParameterization, CompoundParameterization, DoseParameterization, NFishParameterization, VariantParameterization, WellGroupParameterization}
import valar.core.Tables.{BatchesRow, GeneticVariantsRow}
import valar.core.{exec, loadDb}
import valar.params.ParamOrigin
import valar.params.layouts.post.LayoutParameterizations._

/**
  * Builds a full plate layout from a template and parameterization.
  * Returns a FullPlateInfo to avoid inserting.
  */
object PlateConstruction extends LazyLogging {

  implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def parse(submission: SubmissionsRow): FullPlateInfo = {

    val submissionParams = exec((SubmissionParams filter (_.submissionId === submission.id)).result)
    val experiment = exec((Experiments filter (_.id === submission.experimentId)).result).head
    val templatePlate = exec((TemplatePlates filter (_.id === experiment.templatePlateId)).result).head

    def get(origin: ParamOrigin) = paramsFor(submissionParams, origin)

    // no parameterizations can be applied to control types
    val controls: Map[Int, Option[ControlTypesRow]] = ControlTypeParameterization.build(templatePlate)

    val nFish: Map[Int, Int] = NFishParameterization.build(templatePlate, get(ParamOrigin.nFish))
    val ages: Map[Int, Option[Int]] = AgeParameterization.build(templatePlate, get(ParamOrigin.ageDpf))
    val variants: Map[Int, Option[GeneticVariantsRow]] = VariantParameterization.build(templatePlate, get(ParamOrigin.variant))
    val groups: Map[Int, Option[String]] = WellGroupParameterization.build(templatePlate, get(ParamOrigin.group))

    val compounds: Map[Int, List[BatchesRow]] = CompoundParameterization.build(templatePlate, get(ParamOrigin.compound))
    val doses: Map[Int, List[Double]] = DoseParameterization.build(templatePlate, get(ParamOrigin.dose))
    if (compounds.size != doses.size) {
      throw new GrammarException(s"There are ${compounds.size} wells with compounds but ${doses.size} wells with doses")
    }
    if (compounds.flatMap(_._2).size != doses.flatMap(_._2).size) {
      throw new GrammarException(s"There are ${compounds.flatMap(_._2).size} compound treatments but ${doses.flatMap(_._2).size} doses")
    }

    FullPlateInfo(controls, nFish, ages, variants, groups, compounds, doses)
  }

  private def paramsFor(submissionParams: Seq[SubmissionParamsRow], origin: ParamOrigin): Map[DollarSignParam, DollarSignSub] = {
    val kvt = submissionParams filter (_.paramType == origin.name) map (kv => kv.name -> kv.value)
    kvt map { case (k, v) =>
      kvToParamSub(k, v)
    }
  }.toMap

  private def kvToParamSub(k: String, v: String): (DollarSignParam, DollarSignSub) = {
    val p = DollarSignParam(k, false)
    val s = if (p.isList && v.startsWith("[") && v.endsWith("]")) {
      val zs = v.substring(1, v.length - 1) split "," map (_.trim)// map quoteIfNeeded
      DollarSignSub(p, zs.toList)
    } else {
      DollarSignSub(p, List(v))
    }
    p -> s
  }

  //private def quoteIfNeeded(s: String): String = if (!s.startsWith("\"") && !s.endsWith("\"")) "\"" + s + "\"" else s

}
