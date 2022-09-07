package valar.params.layouts

import pippin.grammars.GrammarException
import pippin.grammars.params.{DollarSignParam, DollarSignSub}
import valar.core.DateTimeUtils.timestamp
import valar.core.Tables.{TemplatePlates, TemplatePlatesRow, TemplateWells, TemplateWellsRow}
import valar.core.{exec, loadDb}
import valar.params.{ParamOrigin, PlateParam}
import valar.params.layouts.post.{LayoutGrammars, LayoutParameterizations}
import org.scalatest.{Matchers, PropSpec}

class LayoutParameterizationsTest extends PropSpec with Matchers {

  implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  property("N fish") {
    var templatePlate: TemplatePlatesRow = null
    try {

      templatePlate = newTemplatePlate()
      newTemplateWell(templatePlate.id, "A1*H12", "4+2+$cat", "", "7", "")
      val param = DollarSignParam("$cat", false)
      val sub = DollarSignSub(param, List("3"))
      val int2int = LayoutParameterizations.NFishParameterization.build(templatePlate, Map(param -> sub))
      val expected: Map[Int, Int] = (for (i <- 0 until 96) yield (i, 9)).toMap
      int2int.size should equal (expected.size)
      int2int should equal (expected)

    } finally {
      if (templatePlate != null) exec(TemplatePlates filter (_.id === templatePlate.id) delete)
    }
  }

  property("Library") {
    var templatePlate: TemplatePlatesRow = null
    try {

      templatePlate = newTemplatePlate()
      newTemplateTreatment(templatePlate.id, "A1*H12", "$...library", "1")
      val param = DollarSignParam("$...library", false)
      val sub = DollarSignSub(param, List("/CB61611/"))
      val int2int = LayoutParameterizations.CompoundParameterization.build(templatePlate, Map(param -> sub))
      val expected: Map[Int, List[Int]] = (for (i <- 0 until 96) yield (i, List(54590 + i))).toMap
      int2int.size should equal (expected.size)
      (int2int mapValues (x => x map (_.id))) should equal (expected)

    } finally {
      if (templatePlate != null) exec(TemplatePlates filter (_.id === templatePlate.id) delete)
    }
  }

  property("Library 2") {
    var templatePlate: TemplatePlatesRow = null
    try {

      templatePlate = newTemplatePlate()
      newTemplateTreatment(templatePlate.id, "A1*H12", "$...library", "1")
      val param = DollarSignParam("$...library", false)
      val sub = DollarSignSub(param, List("[/CB61611/]"))
      val int2int = LayoutParameterizations.CompoundParameterization.build(templatePlate, Map(param -> sub))
      val expected: Map[Int, List[Int]] = (for (i <- 0 until 96) yield (i, List(54590 + i))).toMap
      int2int.size should equal (expected.size)
      (int2int mapValues (x => x map (_.id))) should equal (expected)

    } finally {
      if (templatePlate != null) exec(TemplatePlates filter (_.id === templatePlate.id) delete)
    }
  }

  // TODO this is copied

  private lazy val plateQuery = TemplatePlates returning (TemplatePlates map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  private lazy val wellQuery = TemplateWells returning (TemplateWells map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  private lazy val treatmentQuery = TemplateTreatments returning (TemplateTreatments map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  private def newTemplatePlate() = exec(plateQuery += TemplatePlatesRow(
    id = 0,
    name = "~~._LayoutParametersTest_2",
    plateTypeId = 1,
    authorId = 1, // TODO don't rely on real data
    created = timestamp()
  ))

  private def newTemplateTreatment(templatePlateId: Short, wellRange: String, compoundExpression: String, doseExpression: String) = exec(treatmentQuery += TemplateTreatmentsRow(
    0,
    templatePlateId,
    wellRange,
    compoundExpression,
    doseExpression
  ))

  private def newTemplateWell(templatePlateId: Short, wellRange: String, nExpression: String, variantExpression: String, ageExpression: String, groupExpression: String) = exec(wellQuery += TemplateWellsRow(
    id = 0,
    templatePlateId,
    wellRange,
    None,
    nExpression,
    variantExpression,
    ageExpression,
    groupExpression
  ))

}
