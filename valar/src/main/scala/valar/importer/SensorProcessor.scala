package valar.importer

import java.io.InputStream
import java.nio.file.{Files, Path, Paths}
import java.time.{LocalDateTime, ZonedDateTime}

import com.google.common.base.CaseFormat

import scala.collection.JavaConverters._
import collection.JavaConverters._
import com.typesafe.scalalogging.LazyLogging
import valar.core.{ImageStore, exec, loadDb}
import pippin.core._
import pippin.core.addons.TextUtils
import pippin.core.addons.TextUtils.pint
import valar.core.Tables.{RunsRow, SensorData, SensorDataRow, Sensors, SensorsRow}

import scala.io.Source
import scala.util.{Failure, Success, Try}


sealed trait GenSensor extends LazyLogging {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def isOptional: Boolean = false
  def parentDir(result: SubmissionResult): Path
  def requiredFiles: Set[RequiredFile]
  def resolve(result: SubmissionResult): Map[RequiredFile, Path] =
    (requiredFiles map (f => f -> f.resolve(parentDir(result)))).toMap
  def apply(plateRun: RunsRow, nBatteryMillis: Int)
  def name: String = CaseFormat.UPPER_CAMEL.to(CaseFormat.LOWER_UNDERSCORE, getClass.getSimpleName.replace("Sensor", ""))

  protected def insert(plateRun: RunsRow, sensor: SensorsRow, data: Traversable[Byte]): Unit = {
    exec(SensorData += SensorDataRow(
      id = 0,
      runId = plateRun.id,
      sensorId = sensor.id,
      floats = bytesToBlob(data),
      floatsSha1 = bytesToHashBlob(data)
    ))
    logger.info(s"Inserted data for sensor ${sensor.name} in processor ${getClass.getSimpleName}")
  }
}

sealed trait Sensor extends GenSensor {
  override def parentDir(result: SubmissionResult) = result.root // TODO we can change later
}
sealed trait Timing extends GenSensor {
  override def parentDir(result: SubmissionResult) = result.root // TODO we can change later
}


case class RequiredFile(name: String, pathSynonyms: Set[Path]) extends LazyLogging {
  def resolveOptional(parent: Path): Option[Path] =
        Try(resolve(parent)).toOption
  def resolve(parent: Path): Path = {
    pathSynonyms map parent.resolve filter (p => Files.exists(p) && Files.isReadable(p)) match {
      case set if set.isEmpty =>
        throw new MissingResourceException(s"Missing required file for $name (one of $pathSynonyms)")
      case set if set.size > 1 =>
        throw new MissingResourceException(s"Multiple/duplicate files found for required sensor file $name in $pathSynonyms; ambiguous")
      case set =>
        logger.debug(s"Resolved sensor file ${set.head} for $name")
        set.head
    }
  }

  override def toString: String = name
}


trait GenSensorProcessor extends Processor

class RegistrySensorProcessor(result: SubmissionResult) extends Processor(result) with GenSensorProcessor with LazyLogging {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  // TODO reflection
  //val mirror = universe.runtimeMirror(getClass.getClassLoader)
  //val classes = universe.typeOf[GenSensor].typeSymbol.asClass.knownDirectSubclasses
  val availableSensors: Map[String, GenSensor] = {
    Set(
      new SnapshotSensor(result),
      new StimuliSensor(result),
      new MicrophoneSensor(result),
      new PhotometerSensor(result),
      new ThermometerSensor(result),
      new WebcamSensor(result),
      new PreviewSensor(result)
    ) map (s => s.name -> s)
  }.toMap
  def sensors: Set[GenSensor] = {
    (result.config.sauron.hardware.sensors.registry ++ Set("stimuli", "snapshot", "webcam", "preview")) flatMap {name =>
      if (availableSensors contains name) Seq(availableSensors(name)) else {
        logger.warn(s"No sensor with name $name exists")
        Nil
      }
    }
  }.toSet

  override def apply(run: RunsRow) = {
    logger.info(s"Processing ${sensors.size} sensors on run ${run.id}")
    exec(SensorData filter (_.runId === run.id) delete)
    for (sensor <- sensors) {
      logger.info(s"Processing sensor ${sensor.name}")
      try {
        sensor.apply(run, batteryLength(run))
      } catch {
            case e: MissingResourceException =>
            if (sensor.isOptional) logger.error(s"Failed to process $sensor", e)
            else throw e
            case e: Throwable => throw e
      }
    }
  }
}


class SnapshotSensor(result: SubmissionResult) extends Timing with LazyLogging {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  private lazy val snapshotSensor = exec((Sensors filter (_.name === "sauronx-snapshot-ms")).result).head

  private val snapshotFile = RequiredFile("snapshots", Set(Paths.get("timing", "snapshots.list.csv"), Paths.get("sensors", "snapshots.list.csv")))
  override def requiredFiles: Set[RequiredFile] = Set(snapshotFile)

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {

    val helper = new SensorHelper(result, plateRun, nBatteryMillis)
    val snapshotPath = resolve(result)(snapshotFile)

    val millis = helper.toMillis(snapshotPath)
    if (millis.isEmpty) throw new SensorDataFormatException(s"Snapshot data in $snapshotFile is empty")

    val data = millis.foldLeft(Array.empty[Byte]) { case (array, time) =>
      array ++ intsToBytes(Seq(time))
    }
    insert(plateRun, snapshotSensor, data)
  }
}


class StimuliSensor(result: SubmissionResult) extends Timing with LazyLogging {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  private lazy val snapshotSensor = exec((Sensors filter (_.name === "sauronx-snapshot-ms")).result).head
  private lazy val stimulusmsSensor = exec((Sensors filter (_.name === "sauronx-stimulus-ms")).result).head
  private lazy val stimulusIdSensor = exec((Sensors filter (_.name === "sauronx-stimulus-id")).result).head
  private lazy val stimulusValueSensor = exec((Sensors filter (_.name === "sauronx-stimulus-value")).result).head

  private val stimuliFile = RequiredFile("stimuli", Set(Paths.get("timing", "stimuli.csv"), Paths.get("sensors", "stimuli.csv")))
  override def requiredFiles: Set[RequiredFile] = Set(stimuliFile)

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {
    val helper = new SensorHelper(result, plateRun, nBatteryMillis)

    val reader = TextUtils.openCsvReader(stimuliFile.resolve(result.root))
    val timeData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    val pinData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    val valueData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    for (mp <- reader.iteratorWithHeaders) {
      if (!(mp contains "datetime") || !(mp contains "id") || !(mp contains "intensity"))
        throw new SensorDataFormatException(s"Wrong stimulus times file headers; expected 'datetime', 'id', and 'intensity'")
      timeData ++= intsToBytes(Seq(helper.toMillis(mp("datetime"))))
      pinData ++= intsToBytes(Seq(mp("id").toInt))
      valueData ++= helper.sbarray(mp("intensity"), "stimulus value")
    }

    insert(plateRun, stimulusmsSensor, timeData)
    insert(plateRun, stimulusIdSensor, pinData)
    insert(plateRun, stimulusValueSensor, valueData)
  }
}



class MicrophoneSensor(result: SubmissionResult) extends Sensor with LazyLogging {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  private lazy val values = exec((Sensors filter (_.name === "sauronx-microphone-wav")).result).head
  private lazy val timestamps = exec((Sensors filter (_.name === "sauronx-microphone-ms")).result).head

  private val wavFile = RequiredFile("microphone_log.flac", Set(Paths.get("sensors", "microphone_log.flac")))
  private val timestampsFile = RequiredFile("microphone_times.txt", Set(Paths.get("sensors", "microphone_times.txt")))
  override def requiredFiles: Set[RequiredFile] = Set(wavFile, timestampsFile)

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {
    val helper = new SensorHelper(result, plateRun, nBatteryMillis)
    val timeData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    var stream: InputStream = null
    try {
      stream = Files.newInputStream(wavFile.resolve(result.root))
      val bytes = stream.readAllBytes()
      if (bytes.isEmpty) {
        logger.error("The microphone file of length 0")
      } else {
        logger.info(s"Microphone filesize is ${bytes.size} bytes")
        insert(plateRun, values, bytes)
      }
    } finally {
      if (stream != null) stream.close()
    }
    val lines = Files.readAllLines(timestampsFile.resolve(result.root)).asScala
    for (line <- lines) {
      timeData ++= intsToBytes(Seq(helper.toMillis(line)))
    }
    insert(plateRun, timestamps, timeData)
  }
}



class PreviewSensor(result: SubmissionResult) extends Sensor with LazyLogging {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  private lazy val webcam = exec((Sensors filter (_.name === "preview")).result).head

  override val isOptional = true
  private val file = RequiredFile("preview.jpg", Set(Paths.get("preview.jpg"), Paths.get("sensors/preview.jpg")))
  override def requiredFiles: Set[RequiredFile] = Set(file)

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {
    var stream: InputStream = null
    try {
      stream = Files.newInputStream(file.resolve(result.root))
      val theBytes = stream.readAllBytes()
      if (theBytes.isEmpty) {
        logger.error("The preview file is of length 0")
      } else {
        logger.info(s"Inserting main camera snapshot of ${theBytes.size} bytes")
        insert(plateRun, webcam, theBytes)
      }
    } finally {
      if (stream != null) stream.close()
    }
  }
}


class WebcamSensor(result: SubmissionResult) extends Sensor with LazyLogging {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  private lazy val webcam = exec((Sensors filter (_.name === "webcam")).result).head

  private val file = RequiredFile("snap.jpg", Set(Paths.get("snap.jpg"), Paths.get("sensors/snap.jpg")))
  override def requiredFiles: Set[RequiredFile] = Set(file)
  override val isOptional = true

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {
    var stream: InputStream = null
    try {
      stream = Files.newInputStream(file.resolve(result.root))
      val theBytes = stream.readAllBytes()
      if (theBytes.isEmpty) {
        logger.error("The webcam snapshot is of length 0")
      } else {
        logger.info(s"Inserting webcam snapshot of ${theBytes.size} bytes")
        insert(plateRun, webcam, theBytes)
      }
    } finally {
      if (stream != null) stream.close()
    }
  }
}



abstract class CsvSensor(result: SubmissionResult) extends Sensor with LazyLogging {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  protected def valuesName: String
  protected def timestampsName: String
  protected def filename: String

  private lazy val values = exec((Sensors filter (_.name === valuesName)).result).head
  private lazy val timestamps = exec((Sensors filter (_.name === timestampsName)).result).head

  private val csvFile = RequiredFile(filename, Set(Paths.get("sensors", filename)))
  override def requiredFiles: Set[RequiredFile] = Set(csvFile)

  override def apply(plateRun: RunsRow, nBatteryMillis: Int): Unit = {
    val helper = new SensorHelper(result, plateRun, nBatteryMillis)

    val reader = TextUtils.openCsvReader(csvFile.resolve(result.root))
    val timeData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    val valueData = scala.collection.mutable.ArrayBuffer.empty[Byte]
    for (mp <- reader.iteratorWithHeaders) {
      if (!(mp contains "Time") || !(mp contains "Value"))
        throw new SensorDataFormatException(s"Wrong stimulus times file headers; expected 'Value' and 'Time'")
      timeData ++= intsToBytes(Seq(helper.toMillis(mp("Time"))))
      valueData ++= shortsToBytes(helper.ssarray(mp("Value"), "sensor value"))
    }

    insert(plateRun, values, valueData)
    insert(plateRun, timestamps, timeData)
  }
}


class PhotometerSensor(result: SubmissionResult) extends CsvSensor(result) {

  protected def valuesName = "sauronx-tinkerkit-photometer-values"
  protected def timestampsName = "sauronx-tinkerkit-photometer-ms"
  protected def filename = "photometer_log.csv"

}


class ThermometerSensor(result: SubmissionResult) extends CsvSensor(result) {

  protected def valuesName = "sauronx-tinkerkit-thermometer-values"
  protected def timestampsName = "sauronx-tinkerkit-thermometer-ms"
  protected def filename = "thermometer_log.csv"

}


class SensorHelper(result: SubmissionResult, plateRun: RunsRow, nBatteryMillis: Int) {

  val timezone = result.config.local.timezone.name
  val start = result.environment.datetimeStarted.atZone(timezone)
  val startMillis = start.toInstant.toEpochMilli

  def sbarray(signedByte: String, thing: String): Array[Byte] = Try(Array(TextUtils.signByte(signedByte))) match {
    case Success(array) => array
    case Failure(e) => throw new SensorDataFormatException(s"$signedByte does not look liked a signed byte (0–255) for $thing", e)
  }

  def ssarray(signedShort: String, thing: String): Array[Short] = Try(Array(signShort(signedShort))) match {
    case Success(array) => array
    case Failure(e) => throw new SensorDataFormatException(s"$signedShort does not look liked a signed short (0–65536) for $thing", e)
  }

  def signShort(string: String): Short = (pint(string) - 32768).toString.toShort

  def toMillis(path: Path): Seq[Int] =
    Try(Files.readAllLines(path).asScala map toMillis) match {
      case Success(data) => data
      case Failure(e) => throw new SensorDataFormatException(s"Failed to read timestamps from $path", e)
    }

  def toMillis(string: String): Int =
    (ZonedDateTime.of(LocalDateTime.parse(string.replace(' ', 'T')), result.config.local.timezone.name).toInstant.toEpochMilli - startMillis).toInt
}

