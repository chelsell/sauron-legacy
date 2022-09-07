package valar.insertion

import com.typesafe.scalalogging.Logger
import valar.core._

import scala.language.implicitConversions
import collection.JavaConverters._
import pippin.core._
import valar.core.DateTimeUtils._
import pippin.grammars.params.{DollarSignParam, DollarSignSub, TextToParameterization}
import valar.core
import valar.params.assays.{AssayFrameConstruction, AssayParameters, FrameIterator, StimulusInfo}


object BatteryInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: BatteryData): BatteriesRow = attempt { () =>
    insertNew(data)
  }

  private def insertNew(data: BatteryData): BatteriesRow = attempt { () => {
    if (data.assays.isEmpty) throw new ValidationException(s"Must have at least 1 assay")
                val assays: Seq[(AssaysRow, Boolean)] = (data.assays zip data.params) filter (z => z._1 > 0) map { case (a, params) =>
      val templateAssay = exec((TemplateAssays filter (_.id === a)).result).head
      handleAssay(templateAssay, params)
    }
    withCleanup { () => {
      val battery = insertBattery(data, assays map (_._1))
      withCleanup { () =>
        attachAssays(battery, assays map (_._1))
      }{ () =>
        exec(Batteries filter (_.id === battery.id) delete)
      }
      battery
    }}{ () => {
      // only delete assays we just created
      assays filter (_._2) map (_._1) foreach { a =>
        exec(Assays filter (_.id === a.id) delete)
      }
    }}
  }}

  private def insertBattery(data: BatteryData, assays: Seq[AssaysRow]): BatteriesRow = {
    val length = (assays map (_.length)).sum
    val hash = bytesToBlob(RowHashes.batteryHash(assays))
    val query = Batteries returning (Batteries map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += BatteriesRow(
      id = 0,
      name = data.name,
      description = data.description,
      length = length,
      authorId = Some(data.creator),
      templateId = None,
      hidden = false,
      notes = data.notes,
      assaysSha1 = hash,
      created = timestamp()
    ))
  }

  private def handleAssay(templateAssay: TemplateAssaysRow, izationText: String): (AssaysRow, Boolean) = {
    val ization = parseParameterization(templateAssay, izationText)
    val iterators: Map[StimulusInfo, FrameIterator] = new AssayFrameConstruction(true).build(templateAssay, ization)
    val stimFramesAndHashes = stahes(iterators).toSeq
    val hash = RowHashes.assayHash(stimFramesAndHashes)
    val matching = exec(Assays.result) find (h => blobToBytes(h.framesSha1) sameElements hash)
    matching map { a =>
      (a, false)
    } getOrElse {
      val a = insertAssay(templateAssay, stimFramesAndHashes, ization, hash)
      (a, true)
    }
  }

  private def parseParameterization(templateAssay: TemplateAssaysRow, izationText: String): Map[DollarSignParam, DollarSignSub] = {
    val params = AssayParameters.assayParams(templateAssay)
    val paramNames = (params map (_.param)).toSet
    // we do not allow list types in assay parameters
    val paramLengths = (params map (p => p.param.name -> 1)).toMap
    val preppedText = izationText.replaceAllLiterally(";", "\n")
    new TextToParameterization().parse(preppedText, paramNames, paramLengths)
  }

  private def insertAssay(templateAssay: TemplateAssaysRow, stimFramesAndHashes: Seq[StimFramesAndHash], ization: Map[DollarSignParam, DollarSignSub], hash: Array[Byte]): AssaysRow = {
    val length = stimFramesAndHashes.head.frames.length
    val query = Assays returning (Assays map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val assay = exec(query += AssaysRow(
      id = 0,
      name = nameAssay(templateAssay, ization),
      description = templateAssay.description,
      length = length,
      hidden = false,
      templateAssayId = Some(templateAssay.id),
      framesSha1 = bytesToBlob(hash),
      created = timestamp()
    ))
    val q = StimulusFrames returning (StimulusFrames map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    stimFramesAndHashes foreach { stah =>
      exec(q += StimulusFramesRow(
        id = 0,
        assayId = assay.id,
        stimulusId = stah.stimSourceId,
        frames = bytesToBlob(stah.frames),
        framesSha1 = bytesToBlob(bytesToHash(stah.frames))
      ))
    }
    assay
  }

  private def attachAssays(battery: BatteriesRow, assays: Seq[AssaysRow]): Seq[AssayPositionsRow] = {
    val query = AssayPositions returning (AssayPositions map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val starts: Seq[Int] = assays.foldLeft(Seq(0))((s, a) =>
      s ++ Seq(s.last + a.length)
    )
    (assays zip starts) map { case (assay, start) =>
      exec(query += AssayPositionsRow(
        id = 0,
        batteryId = battery.id,
        assayId = assay.id,
        start = start
      ))
    }
  }

  private def nameAssay(templateAssay: TemplateAssaysRow, ization: Map[DollarSignParam, DollarSignSub]): String = {
    templateAssay.name + (if (ization.isEmpty) "" else ":" + ization.map(e => e._1.name + "=" + e._2.values.head).mkString(","))
  }

  private def stahes(iterators: Map[StimulusInfo, FrameIterator]): Iterable[StimFramesAndHash] = {
    iterators map { case (stim, it) =>
      val frames = it.toArray
      val hash = bytesToHash(frames)
      StimFramesAndHash(stim.id, frames, hash)
    }
  }


}
