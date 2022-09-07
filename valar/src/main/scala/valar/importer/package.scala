package valar

import com.typesafe.config.{ConfigException, ConfigOrigin}
import pippin.core.exceptions.ServiceFailedException
import pippin.misc.ValidationFailedException
import valar.core.Tables.{RunsRow, Experiments}
import valar.core.{ImageStore, ValarException, exec, loadDb}

package object importer {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  /**
    * A user error in importing.
    */
  trait ValarImporterException extends ValarException
  class SubmissionInconsistencyException(message: String = null) extends Exception(message) with ValarImporterException
  class MissingResourceException(resource: String = null) extends Exception(s"Required resource $resource is missing") with ValarImporterException
  class ImporterValidationFailedException(message: String = null, cause: Throwable = null) extends ValidationFailedException(message, cause) with ValarImporterException
  class ImporterServiceFailedException(message: String = null, cause: Throwable = null) extends ServiceFailedException(message, cause) with ValarImporterException
  // TODO this is moronic, but ConfigException.origin() can return null, and using that in the constructor will cause a NPE.
  class EnvironmentPropertiesException(origin: ConfigOrigin = null, message: String = null, cause: Throwable = null) extends ConfigException(message, cause) with ValarImporterException
  class TomlConfigMaterializationException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with ValarImporterException
  class SensorDataFormatException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with ValarImporterException
  class FeatureCalculationFailedException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with ValarImporterException
  class RequestNotImplementedException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with ValarImporterException

  def batteryLength(plateRun: RunsRow): Int = {
    exec((for {
      (experiment, battery) <- Experiments join Batteries on (_.batteryId === _.id)
      if experiment.id === plateRun.experimentId
    } yield battery.length).result).head
  }

}
