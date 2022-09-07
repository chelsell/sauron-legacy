package valar.params.assays

import pippin.core.bytesToHash
import pippin.grammars.TimeSeriesGrammar
import pippin.grammars.squints.SiPrefix
import valar.core.DateTimeUtils._
import valar.core.{StimFramesAndHash, StimulusFramesInfo, exec, loadDb}
import org.scalatest.{Matchers, PropSpec}

class AssayParameterizationsTest extends PropSpec with Matchers {

  implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  val prefixes = SiPrefix.prefixes map (_.symbol)

  property("overlap works") {
    AssayParameterizations.calcOverlapInAssay(Seq(
      StimulusFramesInfo(0, 10, 20),
      StimulusFramesInfo(0, 15, 25),
      StimulusFramesInfo(1, 0, 15),
      StimulusFramesInfo(1, 2, 3)
    )) should equal (Set(
      (0, Vector.range(15, 20)),
      (1, Vector(2))
    ))
  }
  property("overlap detects no overlap when there is none") {
    AssayParameterizations.calcOverlapInAssay(Seq(
      StimulusFramesInfo(0, 10, 20),
      StimulusFramesInfo(0, 20, 30),
      StimulusFramesInfo(0, 30, 40),
      StimulusFramesInfo(1, 2, 3),
      StimulusFramesInfo(1, 3, 5)
    )) should equal (Set.empty)
  }


}
