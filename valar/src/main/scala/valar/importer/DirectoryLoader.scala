package valar.importer

import java.nio.file.{Files, Path, Paths, StandardCopyOption}
import java.util.Comparator
import scala.compat.java8.FunctionConverters._
import scala.collection.JavaConverters._
import com.typesafe.config.{ConfigException, ConfigFactory, ConfigParseOptions}
import com.typesafe.scalalogging.LazyLogging
import pippin.core.exceptions.ServiceFailedException
import pippin.misc.{FileHasher, SevenZipCommandLine, ValidationFailedException}
import valar.core.{exec, loadDb}
import valar.features.FeatureProcessor.getFeature

import scala.io.Source
import scala.util.{Failure, Success, Try}


object DirectoryLoader extends LazyLogging {

  implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._


  def load(dir: Path): SubmissionResult = {

    def file(s: String): Path = {
      if (!Files.isRegularFile(dir.resolve(s))) throw new SubmissionInconsistencyException(s"Missing required file $s")
      if (!Files.isReadable(dir.resolve(s))) throw new SubmissionInconsistencyException(s"Required file $s is not readable")
      dir.resolve(s)
    }
    def directory(s: String): Path = {
      if (!Files.isDirectory(dir.resolve(s))) throw new SubmissionInconsistencyException(s"Missing required directory $s")
      if (!Files.isReadable(dir.resolve(s))) throw new SubmissionInconsistencyException(s"Required directory $s is not readable")
      dir.resolve(s)
    }

    logger.info(s"Examining new directory $dir...")

    def extract(): SubmissionResult = {
      val submissionHashFile = file("submission_hash.txt")
      val submissionHash = Source.fromFile(submissionHashFile.toFile).mkString.trim
      val tomlFile = file("config.toml")
      val environmentFile = file("environment.properties")
      val logFile = file("sauronx.log")
      val timingDir = directory("timing")
      val sensorsDir = directory("sensors")
      val videoFile = file("camera/x265-crf15/x265-crf15.mkv") // TODO get best quality
      val sha256File = file(s"$videoFile.sha256")
      logger.info(s"Found all required files for $submissionHash in $dir .")
      _load(submissionHash, tomlFile, environmentFile, logFile, dir, videoFile, timingDir, sensorsDir)
    }

    Try {
      extract()
    } match {
      case Success(result) => result
      case Failure(e) =>
        States.set(dir, States.FileMissing)
        throw e
    }
  }


  private def _load(
      submissionHash: String,
      tomlFile: Path,
      environmentFile: Path,
      logFile: Path,
      root: Path,
      videoFile: Path,
      timingDir: Path,
      sensorsDir: Path
  ): SubmissionResult = {

    require(Files.isRegularFile(tomlFile), s"TOML path $tomlFile is not a file")
    require(Files.isRegularFile(environmentFile), s"Environment path $tomlFile is not a file")
    require(Files.isRegularFile(videoFile), s"Video path $tomlFile is not a file")
    require(Files.isRegularFile(logFile), s"Log path $tomlFile is not a file")
    require(Files.isDirectory(timingDir), s"Timing path $timingDir is not a directory")
    require(Files.isDirectory(sensorsDir), s"Sensors path $sensorsDir is not a directory")

    States.set(root, States.TouchedOnly)

    val submission = exec((Submissions filter (_.lookupHash === submissionHash)).result).headOption getOrElse {
      States.set(root, States.InvalidHash)
      throw new SubmissionInconsistencyException(s"No submission with hash $submissionHash exists")
    }

    // TODO allow override with a flag set
    val run = exec((Runs filter (_.submissionId === submission.id)).result).headOption
    
    val environment = Try(new SauronxEnvironment(ConfigFactory.parseFile(environmentFile.toFile, ConfigParseOptions.defaults().setAllowMissing(false)))) match {
      case Success(env) => env
      case Failure(e: ConfigException) =>
        States.set(root, States.EnvironmentParseFailed)
        throw new EnvironmentPropertiesException(e.origin(), e.getMessage, e.getCause)
      case Failure(e) => throw e
    }

    val tomlText = Source.fromFile(tomlFile.toFile).mkString
    val tomlConfig = Try(TomlConfig.materialize(tomlFile)) match {
      case Success(cfg) => cfg
      case Failure(e) => // TODO less general
        States.set(root, States.MaterializationFailed)
        throw new TomlConfigMaterializationException(cause = e) // it's not perfect, but let's just assume it's a user error
    }

    val logFileText = Source.fromFile(logFile.toFile).mkString

    SubmissionResult(submission, run, tomlText, tomlConfig, environment, logFileText, root, videoFile, timingDir, sensorsDir)
  }
  
}
