package valar.video

trait ColorValue[V] extends Seq[V] {
  val bitDepth: BitDepth
}

class RgbU8(val red: Byte, val green: Byte, val blue: Byte) extends ColorValue[Byte] {
  override def length: Int = 3
  override def iterator: Iterator[Byte] = Seq(red, green, blue).iterator
  override def apply(idx: Int): Byte = idx match {
    case 0 => red
    case 1 => green
    case 2 => blue
    case _ => throw new IndexOutOfBoundsException(s"Index $idx is out of bounds for type Rgb(red, green, blue)")
  }
  override val bitDepth: BitDepth = BitDepth.U8
}

sealed class GrayscaleU8(val value: Byte) extends ColorValue[Byte] {
  override def length: Int = 1
  override def iterator: Iterator[Byte] = Seq(value).iterator
  override def apply(idx: Int): Byte = idx match {
    case 0 => value
    case _ =>  throw new IndexOutOfBoundsException(s"Index $idx is out of bounds for type Grayscale(value)")
  }
  override val bitDepth: BitDepth = BitDepth.U8
}

sealed case class BitDepth(nBits: Short)
object BitDepth {
  val U8 = BitDepth(8)
  val U16 = BitDepth(16)
  val U24 = BitDepth(24)
  val U32 = BitDepth(32)
}
