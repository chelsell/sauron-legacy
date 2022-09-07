package valar.importer

import java.nio.file.{Files, Path, Paths}
import java.util.regex.Pattern
import com.google.common.base.CaseFormat
import com.typesafe.scalalogging.LazyLogging
import valar.core.Tables.{RunsRow, SubmissionsRow}

case class SubmissionResult(
    submission: SubmissionsRow,
    run: RunsRow,
    tomlText: String,
    config: TomlConfig,
    environment: SauronxEnvironment,
    logFileText: String,
    root: Path,
    videoFile: Path,
    timing: Path,
    sensors: Path,
) extends LazyLogging {
  require(Files.isDirectory(timing), "Timing path is not a directory")
  require(Files.isDirectory(sensors), "Sensor path is not a directory")
  require(
    Pattern.compile("[\\da-h]{12}").matcher(submission.lookupHash).matches(),
    s"${submission.lookupHash} does not look like a submission hash, which should be a 12-digit hex number"
  )
  if (state != States.Untouched) logger.warn(s"${submission.lookupHash} was run before and ended with state ${state.name}")
  def state: State = States.get(root)
}

sealed trait State {
  def name: String = CaseFormat.UPPER_CAMEL.converterTo(CaseFormat.LOWER_HYPHEN).convert(getClass.getSimpleName).replaceAll("_", "-")
  def filename: String = "." + name
}
object States {

  val all: List[State] = List(ReadyForInsertion, FileMissing, PartiallyUnzipped, ValidationFailed, ValidationSucceeded, MaterializationFailed, EnvironmentParseFailed, AlreadyUsed, InvalidHash, TouchedOnly, Untouched)

  case object Untouched extends State
  case object TouchedOnly extends State
  case object FileMissing extends State
  case object InvalidHash extends State
  case object AlreadyUsed extends State
  case object EnvironmentParseFailed extends State
  case object MaterializationFailed extends State
  case object ValidationFailed extends State
  case object ValidationSucceeded extends State
  case object PartiallyUnzipped extends State
  case object ReadyForInsertion extends State

  def get(root: Path): State =
    all find (state => Files.exists(root.resolve(state.filename))) getOrElse Untouched
  def reset(root: Path): Unit =
    for (s <- all) Files.deleteIfExists(root.resolve(s.filename))
  // can't afford to suppress cause; TODO add suppressed
  def set(root: Path, state: State): Unit = scala.util.control.Exception.ignoring(classOf[Error]) {
    reset(root)
    Files.createFile(root.resolve(state.filename))
  }
}
