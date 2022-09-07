package valar.features

import slick.jdbc.JdbcBackend.Database

import java.nio.file.{Path, Paths}
import java.time.{LocalDateTime, ZonedDateTime}
import java.time.temporal.ChronoUnit

import scala.reflect.ClassTag
import breeze.linalg.DenseVector
import com.typesafe.scalalogging.LazyLogging
import valar.core.{exec, loadDb}
import valar.video.VTimeFeature
import valar.video._
import pippin.core._
import valar.core.Tables.{Features, FeaturesRow, RunsRow, WellFeatures, WellFeaturesRow}

import scala.util.{Failure, Success, Try}


trait GenFeatureInserter[V] extends LazyLogging {

  private implicit val db: Database = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  protected lazy val insertQuery = WellFeatures returning (WellFeatures map (_.id)) into ((newRow, id) => newRow.copy(id = id))

  def valar: FeaturesRow
  def lorien: VTimeFeature[V]
  def apply(run: RunsRow, videoFile: Path): Unit

  protected def insert(bytes: Traversable[Byte], roi: Roi): Unit = {
    exec(insertQuery += WellFeaturesRow(
      id = 0,
      wellId = roi.wellId,
      typeId = valar.id,
      floats = bytesToBlob(bytes),
      sha1 = bytesToHashBlob(bytes)
    ))
  }
}


abstract class PlainFeatureInserter[V]\
    (container: ContainerFormat, codec: Codec)\
    (implicit ct: ClassTag[V])\
    extends GenFeatureInserter[V] {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def converter(arr: Array[V]): Array[Byte]

  def apply(run: RunsRow, videoFile: Path): Unit = {

    logger.info(s"Calculating and inserting ${valar.name} for run ${run.tag}.")

    val rois = RoiUtils.manual(SimplePlateInfo.fetch(run.id)) map { case (well, roi) => Roi.of(roi, well.id)}

    // TODO only 1 delete query
    //logger.warn(s"Deleting ${previous.size} previous features")
    rois map (_.wellId) foreach { wellId =>
      val previous = exec((WellFeatures filter (wf => wf.wellId === wellId && wf.typeId === valar.id)).result)
      if (previous.nonEmpty) {
        logger.debug(s"Deleting previous ${valar.name} on ${run.tag}")
        assert(previous.size == 1)
        exec(WellFeatures filter (wf => wf.wellId === wellId && wf.typeId === valar.id) delete)
      }
    }

    val started = LocalDateTime.now()

    val results: Map[Roi, Array[V]] = Try {
      val video = VideoFile(videoFile, container, codec)
      lorien.applyOnAll(video, rois)
    } match {
      case Success(array) => array
      case Failure(e) => throw new FeatureCalculationFailedException(s"${valar.name} calculation on run ${run.tag} failed", e)
    }
    val finishedCalc = LocalDateTime.now()
    logger.info(
        s"Calculating ${valar.name} on ${run.tag} took ${ChronoUnit.SECONDS.between(started, finishedCalc)}" +
        s"seconds from $started to $finishedCalc"
    )

    for (((roi, floats), i) <- results.zipWithIndex) {
      insert(converter(floats), roi)
      if (i % 12 == 0) logger.info(s"Processed ${valar.name} for well $i of ${valar.name} on ${run.tag}.")
    }

    logger.info(s"Finished inserting ${valar.name} for run ${run.tag}.")
  }
}


class MiFeatureInserter(container: ContainerFormat, codec: Codec) extends PlainFeatureInserter[Float](container, codec) {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  override val valar: FeaturesRow = exec((Features filter (_.name === "MI")).result).head
  override val lorien = new MiFeature()
  override def converter(arr: Array[Float]): Array[Byte] = floatsToBytes(arr).toArray
}

class CdInserter(container: ContainerFormat, codec: Codec, tau: Int) extends PlainFeatureInserter[Float](container, codec) {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  override val valar: FeaturesRow = exec((Features filter (_.name === s"cd($tau)")).result).head
  override val lorien = new CdFeature(tau)
  override def converter(arr: Array[Float]): Array[Byte] = floatsToBytes(arr).toArray
}

class TdInserter(container: ContainerFormat, codec: Codec, tau: Int) extends PlainFeatureInserter[Float](container, codec) {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  override val valar: FeaturesRow = exec((Features filter (_.name === s"td($tau)")).result).head
  override val lorien = new TdFeature(tau)
  override def converter(arr: Array[Float]): Array[Byte] = floatsToBytes(arr).toArray
}

class CdplusInserter(container: ContainerFormat, codec: Codec, tau: Int) extends PlainFeatureInserter[Float](container, codec) {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  override val valar: FeaturesRow = exec((Features filter (_.name === s"cd+($tau)")).result).head
  override val lorien = new CdplusFeature(tau)
  override def converter(arr: Array[Float]): Array[Byte] = floatsToBytes(arr).toArray
}

class TdplusInserter(container: ContainerFormat, codec: Codec, tau: Int) extends PlainFeatureInserter[Float](container, codec) {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  override val valar: FeaturesRow = exec((Features filter (_.name === s"td+($tau)")).result).head
  override val lorien = new TdplusFeature(tau)
  override def converter(arr: Array[Float]): Array[Byte] = floatsToBytes(arr).toArray
}


object FeatureProcessor {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def getFeature(s: String): PlainFeatureInserter = {
    s match {
      case "MI" => new MiFeatureInserter(ContainerFormat.Mkv, Codec.H265Crf(15))
      case "cd(10)" => new CdInserter(ContainerFormat.Mkv, Codec.H265Crf(15), 10)
      case "td(10)" => new TdInserter(ContainerFormat.Mkv, Codec.H265Crf(15), 10)
      case "cd+(10)" => new CdplusInserter(ContainerFormat.Mkv, Codec.H265Crf(15), 10)
      case "td+(10)" => new TdplusInserter(ContainerFormat.Mkv, Codec.H265Crf(15), 10)
      case _ => throw new IllegalArgumentException(s"Unrecognized feature ${args(0)}")
    }
  }
  
}
