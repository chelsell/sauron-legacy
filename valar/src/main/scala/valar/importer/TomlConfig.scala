package valar.importer

import java.nio.file.Path
import java.time.{LocalDateTime, ZoneId, ZoneOffset, ZonedDateTime}
import java.util
import java.util.Date

import scala.util.{Try, Success, Failure}
import scala.language.implicitConversions
import collection.JavaConverters._
import com.moandjiezana.toml.Toml
import valar.core.DateTimeUtils

trait Materializable[A] {
  implicit class ObjectToMap(obj: Object) {
    implicit def mapify: Map[String, AnyRef] = obj.asInstanceOf[java.util.Map[String, Object]].asScala.toMap
  }
  implicit class ObjectToString(obj: Object) {
    implicit def str: String = obj.asInstanceOf[String]
  }
  implicit class ObjectToChar(obj: Object) {
    implicit def chr: Char = {
      val str = obj.asInstanceOf[String]
      if (str.length != 1) throw new IllegalArgumentException(s"$str is not a single character")
      str.head
    }
  }
  implicit class ObjectToInt(obj: Object) {
    implicit def int: Int = obj.asInstanceOf[Long].toInt
  }
  implicit class ObjectToByte(obj: Object) {
    implicit def byte: Byte = obj.asInstanceOf[Long].toByte
  }
  implicit class ObjectToDouble(obj: Object) {
    implicit def double: Double = Try(obj.asInstanceOf[Double]).recoverWith({case e => Try(obj.asInstanceOf[Long].toDouble)}).getOrElse(throw new IllegalArgumentException("Not a double"))
  }
  implicit class ObjectToStringList(obj: Object) {
    implicit def stringList: List[String] = obj.asInstanceOf[java.util.ArrayList[AnyRef]].asScala.toList map (_.asInstanceOf[String])
  }
  implicit class ObjectToIntList(obj: Object) {
    implicit def intList: List[Int] = obj.asInstanceOf[java.util.ArrayList[AnyRef]].asScala.toList map (_.asInstanceOf[Long].toInt)
  }
  implicit class ObjectToByteList(obj: Object) {
    implicit def byteList: List[Byte] = obj.asInstanceOf[java.util.ArrayList[AnyRef]].asScala.toList map (_.asInstanceOf[Long].toByte)
  }
  implicit class ObjectToDate(obj: Object) {
    implicit def datetime: LocalDateTime = LocalDateTime.ofInstant(obj.asInstanceOf[Date].toInstant, ZoneOffset.UTC)
  }
  def materialize(m: java.util.Map[String, AnyRef]): A = materialize(m.asScala.toMap)
  def materialize(m: Map[String, AnyRef]): A
}

case class TomlConfig(local: Local, sauron: Sauron)
object TomlConfig extends Materializable[TomlConfig] {
  def materialize(path: Path): TomlConfig = materialize(new Toml().read(path.toFile))
  def materialize(toml: Toml): TomlConfig = materialize(toml.toMap)
  override def materialize(m: Map[String, AnyRef]): TomlConfig =
    TomlConfig(Local.materialize(m("local").mapify), Sauron.materialize(m("sauron").mapify))
}

case class Local(storage: LocalStorage, timezone: LocalTimezone)
object Local extends Materializable[Local] {
  override def materialize(m: Map[String, AnyRef]): Local =
    Local(LocalStorage.materialize(m("storage").mapify), LocalTimezone.materialize(m("timezone").mapify))
}

case class LocalStorage(directoryFormat: String)
object LocalStorage extends Materializable[LocalStorage] {
  override def materialize(m: Map[String, AnyRef]): LocalStorage =
    LocalStorage(m("directory_format").str)
}

case class LocalTimezone(name: ZoneId, abbreviation: String, utcOffset: BigDecimal)
object LocalTimezone extends Materializable[LocalTimezone] {
  override def materialize(m: Map[String, AnyRef]): LocalTimezone = LocalTimezone(
    ZoneId.of(m("name").str),
    m("abbreviation").str,
    BigDecimal(m("utc_offset").double)
  )
}

case class Sauron(number: Byte, lastModificationDateTime: LocalDateTime, mostRecentModificationDescription: String, hardware: SauronHardware, rois: SauronRois)
object Sauron extends Materializable[Sauron] {
  override def materialize(m: Map[String, AnyRef]): Sauron = Sauron(
    m("number").int.toByte, m("last_modification_datetime").datetime,
    m("most_recent_modification_description").str,
    SauronHardware.materialize(m("hardware").mapify),
    SauronRois.materialize(m("roi").mapify)
  )
}

case class HardwareCamera(
  deviceIndex: Int, mode: String, plates: CameraPlates, exposure: Double, framesPerSecond: Int,
  setupBufferMilliseconds: Int, paddingBeforeMilliseconds: Int, paddingAfterMilliseconds: Int
)
object HardwareCamera extends Materializable[HardwareCamera] {
  override def materialize(m: Map[String, AnyRef]): HardwareCamera = HardwareCamera(
    m("device_index").int,
    m("mode").str,
    CameraPlates.materialize(m("plate").mapify),
    m("exposure").double,
    m("frames_per_second").int,
    m("setup_buffer_milliseconds").int,
    m("padding_before_milliseconds").int,
    m("padding_after_milliseconds").int
  )
}

case class CameraPlates(rois: Map[Byte, CameraPlate])
object CameraPlates extends Materializable[CameraPlates] {
  override def materialize(m: Map[String, AnyRef]) = CameraPlates {
    m map {case (key: String, value: AnyRef) =>
      key.toByte -> CameraPlate.materialize(value.mapify)
    }
  }
}

case class Roi(x0: Int, x1: Int, y0: Int, y1: Int)

case class CameraPlate(roi: Roi) {}
object CameraPlate extends Materializable[CameraPlate] {
  override def materialize(m: Map[String, AnyRef]) = CameraPlate {
            val list = m("roi").intList
                require(list.size == 4, "ROI must be a list of 4 integers")
    Roi(list(0), list(1), list(2), list(3))
  }
}

case class SauronRois(rois: Map[Byte, SauronRoi])
object SauronRois extends Materializable[SauronRois] {
  override def materialize(m: Map[String, AnyRef]) = SauronRois {
    m map {case (key: String, value: AnyRef) =>
      key.toByte -> SauronRoi.materialize(value.mapify)
    }
  }
}

case class SauronRoi(
  nRows: Int, nColumns: Int,
  x0: Double, y0: Double, x1: Double, y1: Double,
  padX: Double, padY: Double
)
object SauronRoi extends Materializable[SauronRoi] {
  override def materialize(m: Map[String, AnyRef]): SauronRoi = SauronRoi(
    m("n_rows").int, m("n_columns").int,
    m("x0").double, m("y0").double, m("x1").double, m("y1").double,
    m("padx").double, m("pady").double
  )
}

case class SauronHardware(camera: HardwareCamera, stimuli: HardwareStimuli, illumination: HardwareIllumination, sensors: HardwareSensors, arduino: HardwareArduino)
object SauronHardware extends Materializable[SauronHardware] {
  override def materialize(m: Map[String, AnyRef]): SauronHardware =
    SauronHardware(
      HardwareCamera.materialize(m("camera").mapify),
      HardwareStimuli.materialize(m("stimuli").mapify),
      HardwareIllumination.materialize(m("illumination").mapify),
      HardwareSensors.materialize(m("sensors").mapify),
      HardwareArduino.materialize(m("arduino").mapify)
    )
}

case class HardwareIllumination(pins: Pins)
object HardwareIllumination extends Materializable[HardwareIllumination] {
  override def materialize(m: Map[String, AnyRef]) =
    HardwareIllumination(Pins.materialize(m("pins").mapify))
}

case class HardwareStimuli(audio: HardwareAudio, digitalPins: Pins, analogPins: Pins)
object HardwareStimuli extends Materializable[HardwareStimuli] {
  override def materialize(m: Map[String, AnyRef]): HardwareStimuli =
    HardwareStimuli(HardwareAudio.materialize(m("audio").mapify), Pins.materialize(m("digital_pins").mapify), Pins.materialize(m("analog_pins").mapify))
}

case class Pins(pins: Map[String, Byte])
object Pins extends Materializable[Pins] {
  override def materialize(m: Map[String, AnyRef]): Pins = Pins {
    m map { case (key, value) => key -> value.byte }
  }
}

case class HardwareAudio(
  audioFloor: Double, defaultSystemVolume: Byte,
  sauronxOutputAudioDevice: String, sauronxInputAudioDevice: String, defaultOutputAudioDevice: String
)
object HardwareAudio extends Materializable[HardwareAudio] {
  override def materialize(m: Map[String, AnyRef]) = HardwareAudio(
    m("audio_floor").double,
    m("default_system_volume").byte,
    m("sauronx_output_audio_device").str,
    m("sauronx_input_audio_device").str,
    m("default_output_audio_device").str)

}

case class HardwareSensors(samplingIntervalMilliseconds: Int, registry: List[String], digitalPins: Pins, analogPins: Pins)
object HardwareSensors extends Materializable[HardwareSensors] {
  override def materialize(m: Map[String, AnyRef]) = HardwareSensors(
    m("sampling_interval_milliseconds").int,
    m("registry").stringList,
    Pins.materialize(m("digital_pins").mapify),
    Pins.materialize(m("analog_pins").mapify)
  )
}

case class HardwareArduino(chipset: String, compatibleChipsets: List[String], arduinoPorts: ArduinoPorts)
object HardwareArduino extends Materializable[HardwareArduino] {
  override def materialize(m: Map[String, AnyRef]): HardwareArduino = HardwareArduino(
    m("chipset").str,
    m("compatible_chipsets").stringList,
    ArduinoPorts.materialize(m("ports").mapify)
  )
}

case class ArduinoPorts(digital: Ports, analog: Ports)
object ArduinoPorts extends Materializable[ArduinoPorts] {
  override def materialize(m: Map[String, AnyRef]): ArduinoPorts =
    ArduinoPorts(Ports.materialize(m("digital").mapify), Ports.materialize(m("analog").mapify))
}

case class Ports(ports: Map[Char, List[Byte]])
object Ports extends Materializable[Ports] {
  override def materialize(m: Map[String, AnyRef]) = Ports {
    m map {case (key, value) =>
      key.chr -> value.byteList
    }
  }
}
