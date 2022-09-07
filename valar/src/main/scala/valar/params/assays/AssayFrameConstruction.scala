package valar.params.assays

import com.typesafe.scalalogging.Logger
import pippin.core.bytesToHash
import valar.core.{loadDb, exec}

import scala.collection.mutable
import pippin.grammars._
import pippin.grammars.params.{DollarSignParam, DollarSignParams, DollarSignSub, Ization}
import valar.core.{StimFramesAndHash, StimulusFramesInfo, loadDb}
import sun.reflect.generics.reflectiveObjects.NotImplementedException

import scala.util.{Failure, Success, Try}


case class StimulusInfo(id: Int, isAnalog: Boolean, isAudio: Boolean)

case class TemplateStimulusFrameInfo(start: Int, end: Int, stim: StimulusInfo, valueExpression: String)

case class Block(start: Int, end: Int, frames: Iterator[Byte])


class FrameIterator(blocks: Iterator[Block], end: Int) extends Iterator[Byte] {

  if (!blocks.hasNext) {
    throw new NotImplementedException() // TODO
  }
  var i = -1
  var current: Block = blocks.next()

  override def hasNext: Boolean = i + 1 < end

  override def next(): Byte = {
    i += 1
    if (i == end) throw new NoSuchElementException()
    if (i >= current.end && blocks.hasNext) {
      current = blocks.next()
    }
    if (i >= current.start && current.frames.hasNext) {
      current.frames.next()
    } else (-128).toByte
  }
}


object Substituter {
  def prepRange(rangeExpression: String, ization: Map[DollarSignParam, DollarSignSub]): (Int, Int) = {
    val replaced = DollarSignParams.substitute(rangeExpression, ization map (t => (t._1.name, t._2.values.head)))
    val (start, end) = TimeRangeGrammar.evalMillis(replaced)
    (start.toInt, end.toInt)
  }
  def prepValue(valueExpression: String, ization: Map[DollarSignParam, DollarSignSub]): String = {
    DollarSignParams.substitute(valueExpression, ization map (t => (t._1.name, t._2.values.head)))
  }
}


class BlockConstructor(val automaticRounding: Boolean) {

  def buildBlock(info: TemplateStimulusFrameInfo, seed: Option[Int]): Block = {
    val rb = seed map randBasis
    val values: Iterator[Double] = TimeSeriesGrammar.build[Double](info.valueExpression,info. start, info.end, d => d, randBasis = rb).toIterator
    val bytes = byteifyFrames(info.stim.isAnalog, info.stim.isAudio, values)
    Block(info.start, info.end, bytes)
  }

  private def byteifyFrames(isAnalog: Boolean, isAudio: Boolean, values: Iterator[Double]): Iterator[Byte] = {
    val unmapper = StimulusValue.fromUnsignedDouble(isAnalog, isAudio, automaticRounding)(_)
    values map { f =>
      Try(unmapper(f)) match {
        case Success(v) => v.value
        case Failure(e: TempRangeException) => throw new IllegalArgumentException(e)
        case Failure(e) => throw e
      }
    }
  }
}


class Stitcher(constructor: BlockConstructor) {
  def stitch(infos: Seq[TemplateStimulusFrameInfo], seed: Option[Int]): Map[StimulusInfo, FrameIterator] = {
    testOverlap(infos)
    // start and end of the whole assay
    val assayStart = (infos map (_.start)).min
                // TODO disabled this. Is that ok?
    //assert(assayStart == 0, s"Assay start is at $assayStart, not 0")
    val assayEnd = (infos map (_.end)).max
    infos groupBy (_.stim) map { case (stimulus: StimulusInfo, group) =>
      val blocks = group map (info => constructor.buildBlock(info, seed))
      stimulus -> new FrameIterator(blocks.iterator, assayEnd)
    }
  }
  private def testOverlap(infos: Seq[TemplateStimulusFrameInfo]): Unit = {
    val overlap = AssayParameterizations.calcOverlapInAssay(infos map (info => StimulusFramesInfo(info.stim.id, info.start, info.end)))
    if (overlap.nonEmpty) {
      throw new BlockOverlapException()
    }
  }
}


class AssayFrameConstruction(val automaticRounding: Boolean) {

  implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def build(templateAssay: TemplateAssaysRow, ization: Map[DollarSignParam, DollarSignSub]): Map[StimulusInfo, FrameIterator] = {
    val params = AssayParameters.assayParams(templateAssay.id)
    val seed = getSeed(ization)
    val templateStimframes = exec((TemplateStimulusFrames filter (_.templateAssayId === templateAssay.id)).result)
    val infos = getInfos(templateStimframes, ization)
    new Stitcher(new BlockConstructor(automaticRounding)).stitch(infos, seed)
  }

  private def getInfos(templateStimframes: Seq[TemplateStimulusFramesRow], ization: Map[DollarSignParam, DollarSignSub]): Seq[TemplateStimulusFrameInfo] = {
    val stimuliById: Map[Int, StimulusInfo] = (exec(Stimuli.result) map (s => s.id -> StimulusInfo(s.id, s.analog, s.audioFileId.nonEmpty))).toMap
    templateStimframes map { ts =>
      val range = Substituter.prepRange(ts.rangeExpression, ization)
      val value = Substituter.prepValue(ts.valueExpression, ization)
      val stimulus = stimuliById(ts.stimulusId)
      TemplateStimulusFrameInfo(range._1, range._2, stimulus, value)
    }
  }

  private def getSeed(ization: Map[DollarSignParam, DollarSignSub]): Option[Int] = {
    ization.get(DollarSignParam("$seed", true)) map {
      v => Try(v.values.head.toInt) getOrElse {
        throw new IllegalArgumentException(s"Bad seed $v")
      }
    }
  }

}
