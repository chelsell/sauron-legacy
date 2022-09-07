package valar.params.layouts

import pippin.grammars.params.DollarSignParam
import valar.core.DateTimeUtils._
import valar.core.{exec, loadDb}
import valar.params.{ParamOrigin, PlateParam}
import org.scalatest.{Matchers, PropSpec}

class LayoutParametersTest extends PropSpec with Matchers {

  implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  property("Detecting well parameters without lists") {

    var templatePlate: TemplatePlatesRow = null
    try {

      templatePlate = newTemplatePlate()
      val nFishExpression = "$n_fish * $i + $r + $c + $something"
      val strainExpression = "\"singWT\""
      val templateWells = Seq(
        newTemplateWell(templatePlate.id, "A1...H12", nFishExpression, strainExpression, "7", ""),
        newTemplateWell(templatePlate.id, "A1", nFishExpression, strainExpression, "7", ""),
        newTemplateWell(templatePlate.id, "A1-A5", nFishExpression, strainExpression, "7", "")
      )

      val params: Set[PlateParam] = PreLayoutUtils.listWellParams(templatePlate)
      val expectedSet = Set(
        PlateParam(DollarSignParam("$n_fish", false), ParamOrigin.nFish, 1),
        PlateParam(DollarSignParam("$something", false), ParamOrigin.nFish, 1)
      )
      params should equal (expectedSet)
      for (p <- params) p.param.isList should be (false)

    } finally {
      if (templatePlate != null) exec(TemplatePlates filter (_.id === templatePlate.id) delete)
    }
  }

  property("Detecting well parameters with lists") {

    var templatePlate: TemplatePlatesRow = null
    try {

      templatePlate = newTemplatePlate()
      val templateWells = Seq(
        newTemplateWell(templatePlate.id, "A1-D1", "$...fishes", "$...strains", "7", ""), // same # of wells, though technically it shouldn't check
        newTemplateWell(templatePlate.id, "A1-A4", "$...fishes", "$...strains", "7", "")
      )

      val params: Set[PlateParam] = PreLayoutUtils.listWellParams(templatePlate)
      val expectedSet = Set(
        PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.nFish, 4),
        PlateParam(DollarSignParam("$...strains", false), ParamOrigin.variant, 4)
      )
      params should equal (expectedSet)
      for (p <- params) p.param.isList should be (true)

    } finally {
      if (templatePlate != null) exec(TemplatePlates filter (_.id === templatePlate.id) delete)
    }
  }

  property("Detecting mismatched lengths and origins") {

    PreLayoutUtils.mismatches(Set(
      PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.nFish, 4),
      PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.nFish, 5)
    )) should equal (Set("$...fishes"))

    PreLayoutUtils.mismatches(Set(
      PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.nFish, 5),
      PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.variant, 5)
    )) should equal (Set("$...fishes"))

    PreLayoutUtils.mismatches(Set(
      PlateParam(DollarSignParam("$fishes", false), ParamOrigin.nFish, 1),
      PlateParam(DollarSignParam("$fishes", false), ParamOrigin.nFish, 1)
    )) should equal (Set.empty[String])

    PreLayoutUtils.mismatches(Set(
      PlateParam(DollarSignParam("$...fishes", false), ParamOrigin.nFish, 4),
      PlateParam(DollarSignParam("$...nofishes", false), ParamOrigin.nFish, 5)
    )) should equal (Set.empty[String])
  }

  private lazy val plateQuery = TemplatePlates returning (TemplatePlates map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  private lazy val wellQuery = TemplateWells returning (TemplateWells map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  private def newTemplatePlate() = exec(plateQuery += TemplatePlatesRow(
    id = 0,
    name = "%_LayoutParametersTest_1",
    plateTypeId = 1,
    authorId = 1, // TODO don't rely on real data
    created = timestamp()
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
