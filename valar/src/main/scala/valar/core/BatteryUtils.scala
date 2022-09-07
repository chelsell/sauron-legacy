package valar.core

import java.sql.Blob

import javax.sql.rowset.serial.SerialBlob
import com.typesafe.scalalogging.{LazyLogging, Logger}
import pippin.core.exceptions.InvalidDataFormatException
import pippin.core._
import valar.core.Tables.Assays
import slick.jdbc.JdbcBackend.Database


/**
  * Implements the calculation of hashes for stimframes, assays, and batteries.
  * TODO clean up
  */
object RowHashes {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def batteryHash(assayBatteryInfos: Seq[AssayInBatteryInfo]): Array[Byte] = {
    bytesToHash(
      assayBatteryInfos sortBy (_.start) flatMap (info => {
        val assays = exec((Assays filter (_.id === info.assayId)).result)
        assert(assays.size == 1)
        val assay = assays.head
        blobToBytes(assay.framesSha1) ++ intsToBytes(Seq(assay.length))
      })
    )
  }

  def batteryHash(assays: Seq[AssaysRow]): Array[Byte] = {
    val x = (assays zip assayStarts(assays)) map (t => AssayInBatteryInfo(t._1.id, t._2))
    batteryHash(x)
  }

  def assayStarts(assays: Seq[AssaysRow]): Seq[Int] = {
    var n = 0
    (for (a <- assays) yield {
      n += a.length
      n - a.length
    }).toList
  }

  def assayHash(stimFramesAndHashes: Seq[StimFramesAndHash]): Array[Byte] = {
    bytesToHash(stimFramesAndHashes sortBy (_.stimSourceId) flatMap (f => intsToBytes(Seq(f.stimSourceId)) ++ f.frames))
  }

  def buildFramesForStimulus(frames: Seq[Byte], assay: Assay, stimulusName: String): StimFramesAndHash = {
    val assayFrames: Array[Byte] = frames.slice(assay.start, assay.stop).toArray
    val stimIds = exec((Stimuli filter (_.name === stimulusName) map (_.id)).result)
    if (stimIds.isEmpty) throw new IllegalArgumentException(s"No stimulus source with name $stimulusName")
    val stimframesHash = bytesToHash(assayFrames)
    StimFramesAndHash(stimIds.head, assayFrames, stimframesHash)
  }

  def findMatchingBattery(batteryHash: Array[Byte]): Option[MatchingBattery] = {

    // find a battery that has exactly those Assays
    // this problem again: can't filter by blob
    val allBatteries = exec((
      Batteries map (row => (row.id, row.name, row.assaysSha1))
    ).result)
    val matchingBatteries = (allBatteries
      map (b => MatchingBattery(b._1, b._2, b._3))
      filter (mp => blobToBytes(mp.hash) sameElements batteryHash)
    )
    assert(matchingBatteries.size < 2, s"Somehow the battery matches two or more batteries in the database: ${matchingBatteries.map(_.id.toString).mkString(", ")}")
    matchingBatteries.headOption
  }

  def findMatchingAssays(hashOfAssay: Array[Byte]): Seq[MatchingAssay] = {
    // unfortunately, Slick doesn't seem to allow lookup by the binary hash (which is represented as a blob)
    // so, we'll select all of them and then search for it -- matchingAssay is the end result
    val allAssaysQuery = Assays map (row => (row.id, row.name, row.framesSha1))
    exec(allAssaysQuery.result) filter {case (id, name, hash) =>
      // I have no idea why the blob comparison doesn't work (it's supposed to)
      blobToBytes(hash) sameElements hashOfAssay
    } map {case (id, name, hash) => MatchingAssay(id, name, hash)} // just because that tuple is too complex
  }

  def fixBatteryHash(battery: BatteriesRow) = {
    val assayPositions = exec((AssayPositions filter (_.batteryId === battery.id)).result)
    val q = for {
      (p, a) <- AssayPositions join Assays on (_.assayId === _.id)
      if p.batteryId === battery.id
    } yield a
    val assays = exec(q.result)
    val badBatteryHash = blobToBytes(battery.assaysSha1)
    val correctBatteryHash = batteryHash(assays)
    println(s"BATTERY:    ${bytesToHex(badBatteryHash)} ------> ${bytesToHex(correctBatteryHash)}")
    exec(Batteries filter (_.id === battery.id) map (_.assaysSha1) update bytesToBlob(correctBatteryHash))
  }

  def fixAssayHash(assay: AssaysRow): Unit = {
    val stashes = exec((StimulusFrames filter (_.assayId === assay.id)).result) map { stimframes =>
      val frames = blobToBytes(stimframes.frames)
      val badHash = blobToBytes(stimframes.framesSha1)
      val correctHash = bytesToHash(frames)
      val stash = StimFramesAndHash(stimframes.stimulusId, frames, correctHash)
      println(s"FRAMES:     ${bytesToHex(badHash)} ------> ${bytesToHex(correctHash)}")
      exec(StimulusFrames filter (_.id === stimframes.id) map (_.framesSha1) update bytesToBlob(correctHash))
      stash
    }
    val badAssayHash = blobToBytes(assay.framesSha1)
    val correctAssayHash = assayHash(stashes)
    println(s"ASSAY:      ${bytesToHex(badAssayHash)} ------> ${bytesToHex(correctAssayHash)}")
    exec(Assays filter (_.id === assay.id) map (_.framesSha1) update bytesToBlob(correctAssayHash))
  }

}


case class StimulusFramesInfo(stimulusId: Int, start: Int, end: Int)

case class MatchingAssay(id: Int, name: String, hash: Blob)
case class MatchingBattery(id: Int, name: String, hash: Blob)

case class Assay(name: String, start: Int, stop: Int, length: Int) {
  require(length == stop - start)
}

case class AssayInBatteryInfo(assayId: Int, start: Int)

case class StimFramesAndHash(stimSourceId: Int, frames: Array[Byte], hash: Array[Byte])
