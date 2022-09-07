package valar.params.assays

import valar.core.Tables.{StimuliRow, TemplateStimulusFramesRow}

import scala.util.{Failure, Success, Try}

private class TempRangeException(val value: Double, cause: Exception = null) extends Exception(s"Value $value is out of range", cause)

sealed trait StimulusValue {
  val value: Byte
}

case class PwmStimulusValue(value: Byte) extends StimulusValue {}

case class AudioStimulusValue(value: Byte) extends StimulusValue {}

case class BinaryStimulusValue(value: Byte) extends StimulusValue {
  if (value != -127 && value != -128) throw new TempRangeException(value + 128)
}

object StimulusValue {

  def fromUnsignedDouble(stimulus: StimuliRow, automaticRounding: Boolean)(d: Double): StimulusValue =
    fromUnsignedDouble(stimulus.analog, stimulus.audioFileId.nonEmpty, automaticRounding)(d)

  def fromUnsignedDouble(isAnalog: Boolean, isAudio: Boolean, automaticRounding: Boolean)(d: Double): StimulusValue = {
    val dFixed = if (automaticRounding) math.round(d) else d
    val b = Try(BigDecimal.valueOf(dFixed - 128).toByteExact) match { // throw ArithmeticException if it's not exact
      case Success(v: Byte) => v
      case Failure(e: ArithmeticException) => throw new TempRangeException(d-128, e)
      case Failure(e) => throw e
    }
    if (isAnalog) PwmStimulusValue(b)
    else if (isAudio) AudioStimulusValue(b)
    else BinaryStimulusValue(b)
  }
}
