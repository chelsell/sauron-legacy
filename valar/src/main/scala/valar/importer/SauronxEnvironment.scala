package valar.importer

import java.time.LocalDateTime

import scala.collection.JavaConverters._
import com.typesafe.config.{Config, ConfigValueType}
import com.typesafe.scalalogging.LazyLogging
import pippin.core._

case class SauronxEnvironment(datetimeStarted: LocalDateTime, sauronxHash: Array[Byte], data: Map[String, String]) {

  def this(config: Config) = {
    this(LocalDateTime.parse(config.getString("datetime_started")), hexToBytes(config.getString("sauronx_hash")), SauronxEnvironment.configMap(config))
  }
}

object SauronxEnvironment extends LazyLogging {
  private def configMap(config: Config): Map[String, String] = {
    config.entrySet().asScala map {entry =>
      val value = if (entry.getValue.valueType != ConfigValueType.STRING) {
        logger.warn(s"Environment property ${entry.getKey} has type ${entry.getValue.valueType} instead of string")
        entry.getKey -> entry.getValue.unwrapped.toString
      } else {
        entry.getKey -> entry.getValue.unwrapped.asInstanceOf[String]
      }
      logger.debug(s"Setting $value")
      value
    }
  }.toMap
}
