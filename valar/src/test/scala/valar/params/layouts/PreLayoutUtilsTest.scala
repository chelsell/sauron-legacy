package valar.params.layouts

import pippin.grammars.squints.SiPrefix
import valar.core.CommonQueries
import org.scalatest.{Matchers, PropSpec}

class PreLayoutUtilsTest extends PropSpec with Matchers {

  val prefixes = SiPrefix.prefixes map (_.symbol)
  val genericNinetySixWellPlate = CommonQueries.listPlateTypes.head

  property(s"Test missing wells") {
    PreLayoutUtils.missingWells(Seq("A1*H12"), genericNinetySixWellPlate) should equal (Set.empty)
    PreLayoutUtils.missingWells(Seq("A1*H11"), genericNinetySixWellPlate) should equal (Set((1, 12), (2, 12), (3, 12), (4, 12), (5, 12), (6, 12), (7, 12), (8, 12)))
  }
  property(s"Test overlapping wells") {
    PreLayoutUtils.overlappingWells(Seq("A1*H12"), genericNinetySixWellPlate) should equal (Set.empty)
    PreLayoutUtils.overlappingWells(Seq("A1*H11"), genericNinetySixWellPlate) should equal (Set.empty)
    PreLayoutUtils.overlappingWells(Seq("A1-A5"), genericNinetySixWellPlate) should equal (Set.empty)
    PreLayoutUtils.overlappingWells(Seq("A1-A5", "A6-A8", "F9*H12"), genericNinetySixWellPlate) should equal (Set.empty)
    PreLayoutUtils.overlappingWells(Seq("A1-A4", "A2-A3"), genericNinetySixWellPlate) should equal (Set(2, 3))
  }
}
