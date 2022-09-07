package valar.params.assays

import com.typesafe.scalalogging.Logger
import pippin.grammars.params.{DollarSignParam, DollarSignParams, DollarSignSub}
import pippin.grammars.TimeRangeGrammar
import valar.core.{StimulusFramesInfo, loadDb}
import squants.time.Time


/**
  * Utilities for working with parameters <em>and</em> their values.
  */
object AssayParameterizations {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._

  /**
    *
    * @param templates A list of (unofficial / non-Valar) stimulus frames
    * @return A sequence of (stimulus ID, range of frames) tuples
    */
  def calcOverlapInAssay(templates: Traversable[StimulusFramesInfo]): Set[(Int, IndexedSeq[Int])] = {
    // this is pretty inefficient
    var overlap: Set[(Int, IndexedSeq[Int])] = Set.empty
    for (a <- templates) {
      for (b <- templates) {
        if (a != b && a.stimulusId == b.stimulusId) {
          val over: (Int, IndexedSeq[Int]) = (a.stimulusId, Range(a.start, a.end) intersect Range(b.start, b.end))
          if (over._2.nonEmpty) overlap = overlap + over
        }
      }
    }
    overlap
  }

  def splitRange(rangeExpression: String, ization: Map[DollarSignParam, DollarSignSub]): (Int, Int) = {
    val replaced = DollarSignParams.substitute(rangeExpression, ization map (t => (t._1.name, t._2.values.head)))
    val (start, end) = TimeRangeGrammar.evalMillis(replaced)
    (start.toInt, end.toInt)
  }

  def templateToInfos(templateAssay: TemplateAssaysRow, templateStimulusFrames: Seq[TemplateStimulusFramesRow], ization: Map[DollarSignParam, DollarSignSub]): Seq[StimulusFramesInfo] = {
    templateStimulusFrames map { template =>
      val range = DollarSignParams.substitute(template.rangeExpression, ization map (t => (t._1.name, t._2.values.head)))
      // these were already checked
      val startAndStop = splitRange(range, ization)
      StimulusFramesInfo(template.stimulusId, startAndStop._1, startAndStop._2)
    }
  }

}
