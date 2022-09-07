package valar.video

import java.lang.IllegalArgumentException
import breeze.linalg.DenseMatrix
import valar.video.RichMatrices.RichMatrix
import org.bytedeco.javacpp.indexer.UByteRawIndexer
import org.bytedeco.javacv.{Frame, OpenCVFrameConverter}

import scala.collection.immutable.IndexedSeq


/**
  * Super-fast byte matrix.
  * Just a thin wrapper around an OpenCV indexer.
  */
case class BlazingMatrix(indexer: UByteRawIndexer) {

  def rows: Int = indexer.rows.toInt
  def cols: Int = indexer.cols.toInt

  def width: Int = indexer.width.toInt
  def height: Int = indexer.height.toInt

  val indices: (Range, Range) = (0 until rows, 0 until cols)

  def data: Seq[Int] = {
    for (row <- 0 until rows; col <- 0 until cols)
      yield indexer.get(row, indexer.channels*col)
  }

  def |-|(o: BlazingMatrix): Int = {
    assert(this.rows == o.rows && this.cols == o.cols)
    var s = 0
    for (row <- 0 until rows; col <- 0 until cols) {
      s += math.abs(this(row, col) - o(row, col))
    }
    s
  }

  def apply(row: Int, col: Int): Int =
    indexer.get(row, indexer.channels*col)

  def toRichMatrix: RichMatrix = RichMatrix(toBreezeMatrix)
  def toBreezeMatrix: DenseMatrix[Int] = {
    val matrix = new DenseMatrix[Int](rows, cols)
    for (row <- 0 until rows; col <- 0 until cols) {
      matrix.update(row, col, this(row, col))
    }
    matrix
  }

  override def toString: String = s"BlazingMatrix($rows, $cols): ${super.toString}"

  override def equals(obj: scala.Any): Boolean = {
    if (!obj.isInstanceOf[BlazingMatrix]) false
    else {
      val o = obj.asInstanceOf[BlazingMatrix]
      this.data == o.data
    }
  }
}


object BlazingMatrix {
  private val matConverter = new OpenCVFrameConverter.ToMat
  def of(frame: Frame): BlazingMatrix = {
    val indexer: UByteRawIndexer = matConverter.convert(frame).createIndexer()
    BlazingMatrix(indexer)
  }
}
