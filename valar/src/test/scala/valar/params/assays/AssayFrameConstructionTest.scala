package valar.params.assays

import pippin.core.bytesToHash
import pippin.grammars.TimeSeriesGrammar
import valar.core.DateTimeUtils.timestamp
import valar.core.Tables.{TemplateAssays, TemplateStimulusFrames}
import valar.core.{StimFramesAndHash, exec, loadDb}
import org.scalatest.{FunSuite, Matchers, PropSpec}

class AssayFrameConstructionTest extends PropSpec with Matchers {

  implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  property("frame iterator") {
    val blocks = Seq(
      Block(0, 5, Seq(1, 2).map(_.toByte).iterator),
      Block(7, 11, Seq(5, 6, 7).map(_.toByte).iterator)
    )
    // --------------------------------------------------------------------//
    // blocks    =      a   a   a   a   a   .   .   b   b   b   b   .   .  //
    // indices  =       0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12  //
    val expected = List(1,  2,  -128,  -128,  -128,  -128,  -128,  5,  6,  7,  -128,  -128,  -128) //
    // --------------------------------------------------------------------//
    val list = new FrameIterator(blocks.iterator, 13).toList
    list should equal (expected)
  }

  property("block constructor, digital") {
    val constructor = new BlockConstructor(false)
    val stim = StimulusInfo(1, false, false)
    val info = TemplateStimulusFrameInfo(5, 10, stim, "if $t=6: 1")
    val block = constructor.buildBlock(info, Some(1))
    block.start should equal(5)
    block.end should equal (10)
    block.frames.toList should equal (List(-128, -127, -128, -128, -128))
  }

  property("block constructor, analog") {
    val constructor = new BlockConstructor(true)
    val stim = StimulusInfo(1, true, false)
    val info = TemplateStimulusFrameInfo(0, 10, stim, "if $t<=6: $t/3 else: 255")
    val block = constructor.buildBlock(info, Some(1))
    block.start should equal(0)
    block.end should equal (10)
    block.frames.toList should equal (List(-128, -128, -127, -127, -127, -126, -126, 127, 127, 127))
  }

  property("build and stitch") {
    val constructor = new BlockConstructor(false)
    val stim1 = StimulusInfo(1, true, false)
    val stim2 = StimulusInfo(2, true, false)
    val stim3 = StimulusInfo(3, true, false)
    val blocka1 = TemplateStimulusFrameInfo(0, 3, stim1, "2+128")
    val blocka2 = TemplateStimulusFrameInfo(4, 7, stim1, "3+128")
    val blockb1 = TemplateStimulusFrameInfo(0, 2, stim2, "5+128")
    val blockb2 = TemplateStimulusFrameInfo(4, 5, stim2, "6+128")
    val blockc1 = TemplateStimulusFrameInfo(0, 1, stim3, "8+128")
    val blockc2 = TemplateStimulusFrameInfo(5, 6, stim3, "9+128")
    val stitcher = new Stitcher(constructor)
    val stuff = stitcher.stitch(List(blocka1, blocka2, blockb1, blockb2, blockc1, blockc2), Some(1))
    (stuff contains stim1) should be (true)
    (stuff contains stim2) should be (true)
    (stuff contains stim3) should be (true)
    stuff(stim1).toList should equal (List(2, 2, 2, -128, 3, 3, 3))
    stuff(stim2).toList should equal (List(5, 5, -128, -128, 6, -128, -128))
    stuff(stim3).toList should equal (List(8, -128, -128, -128, -128, 9, -128))
  }

  property("equal stimuli") {
    val constructor = new BlockConstructor(false)
    // these two have the same IDs:
    val stim1 = StimulusInfo(1, true, false)
    val stim2 = StimulusInfo(1, true, false)
    assert(stim1 == stim2)
    val blocka1 = TemplateStimulusFrameInfo(0, 3, stim1, "2+128")
    val blockb1 = TemplateStimulusFrameInfo(4, 6, stim2, "5+128")
    val stitcher = new Stitcher(constructor)
    val stuff = stitcher.stitch(List(blocka1, blockb1), Some(1))
    (stuff contains stim1) should be (true)
    (stuff contains stim2) should be (true)
    stuff(stim1).toList should equal (List(2, 2, 2, -128, 5, 5))
    // it's already been used up!!!
    stuff(stim2).toList should equal (List())
  }

  property("sequential blocks") {
    val constructor = new BlockConstructor(false)
    // these two have the same IDs:
    val stim1 = StimulusInfo(1, true, false)
    val blocka1 = TemplateStimulusFrameInfo(0, 3, stim1, "2+128")
    val blocka2 = TemplateStimulusFrameInfo(3, 5, stim1, "5+128")
    val stitcher = new Stitcher(constructor)
    val stuff = stitcher.stitch(List(blocka1, blocka2), Some(1))
    (stuff contains stim1) should be (true)
    stuff(stim1).toList should equal (List(2, 2, 2, 5, 5))
  }

  property("gap between blocks") {
    val constructor = new BlockConstructor(false)
    // these two have the same IDs:
    val stim1 = StimulusInfo(1, true, false)
    val blocka1 = TemplateStimulusFrameInfo(0, 2, stim1, "2+128")
    val blocka2 = TemplateStimulusFrameInfo(8, 10, stim1, "5+128")
    val stitcher = new Stitcher(constructor)
    val stuff = stitcher.stitch(List(blocka1, blocka2), Some(1))
    (stuff contains stim1) should be (true)
    stuff(stim1).toList should equal (List(2, 2, -128, -128, -128, -128, -128, -128, 5, 5))
  }

  property("illegal overlap") {
    val constructor = new BlockConstructor(false)
    // these two have the same IDs:
    val stim1 = StimulusInfo(1, true, false)
    val blocka1 = TemplateStimulusFrameInfo(0, 3, stim1, "2+128")
    val blocka2 = TemplateStimulusFrameInfo(2, 4, stim1, "5+128")
    val stitcher = new Stitcher(constructor)
    a [BlockOverlapException] should be thrownBy {
      val x = stitcher.stitch(List(blocka1, blocka2), Some(1))
      println(x mapValues (_.toList))
    }
  }
}
