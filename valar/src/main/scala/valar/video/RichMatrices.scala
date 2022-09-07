package valar.video

import scala.language.implicitConversions
import breeze.math._
import breeze.numerics._
import breeze.linalg.DenseMatrix
import breeze.linalg._
import breeze.numerics.abs
import breeze.linalg.{sum => breezesum}
import breeze.linalg.{min => breezemin}
import breeze.linalg.{max => breezemax}
import breeze.stats.DescriptiveStats
import com.typesafe.scalalogging.LazyLogging
import valar.core.loadDb

object RichMatrices extends LazyLogging {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  implicit def richMatrixToMatrix(richMatrix: RichMatrix): Matrix[Int] = richMatrix.matrix

  implicit class RichMatrix(val matrix: DenseMatrix[Int]) {

    def crop(roi: Roi): RichMatrix = {
      if (roi.width > matrix.cols)
        logger.warn(s"Width ${roi.width} for ROI $roi extends outside of image bounds (${matrix.cols} x ${matrix.rows})")
      if (roi.height > matrix.rows)
        logger.warn(s"Height ${roi.height} for ROI $roi extends outside of image bounds (${matrix.cols} x ${matrix.rows})")
      RichMatrix(matrix(
        roi.y0 to roi.y0 + min(roi.height, matrix.rows),
        roi.x0 to roi.x0 + min(roi.width, matrix.cols)
      ))
    }
    def crop(roi: RoisRow, wellId: Int): RichMatrix = crop(Roi.of(roi, wellId))
    def `//`(roi: Roi): RichMatrix = crop(roi)

    def normalize255(q: Double): RichMatrix = {
      val sub: DenseMatrix[Int] = matrix - quantile(q).toInt
      RichMatrix(sub * 255/(quantile(1-q)-quantile(q)).toInt)
    }
    def normalize32b(q: Double): RichMatrix = {
      val sub: DenseMatrix[Int] = matrix - quantile(q).toInt
      RichMatrix(sub * (2^32)/(quantile(1-q)-quantile(q)).toInt)
    }

    def quantile(q: Double): Double = DescriptiveStats.percentile(matrix.data map (_.toDouble), q)
    def sum: Int = breezesum(matrix)
    def size: Int = matrix.size
    def mean: Double = breezesum(matrix) / (matrix.rows*matrix.cols)

    def +(o: RichMatrix): RichMatrix = RichMatrix(matrix - o.matrix)
    def +(o: Int): RichMatrix = RichMatrix(matrix + o)
    def -(o: Int): RichMatrix = RichMatrix(matrix - o)
    def -(o: RichMatrix): RichMatrix = RichMatrix(matrix - o.matrix)

    def |-|(o: RichMatrix): RichMatrix = abs(matrix - o.matrix)
    def |-|(o: Int): RichMatrix = abs(matrix - o)

    def #<(o: Int): Int = breezesum(I(matrix <:< DenseMatrix.fill(matrix.rows, matrix.cols)(o))).toInt
    def #>(o: Int): Int = breezesum(I(matrix >:> DenseMatrix.fill(matrix.rows, matrix.cols)(o))).toInt
    def #>=(o: Int): Int = breezesum(I(matrix >:> DenseMatrix.fill(matrix.rows, matrix.cols)(o-1))).toInt
    def #<=(o: Int): Int = breezesum(I(matrix <:< DenseMatrix.fill(matrix.rows, matrix.cols)(o+1))).toInt

    def #<(o: RichMatrix): Int = breezesum(I(matrix <:< o.matrix)).toInt
    def #>(o: RichMatrix): Int = breezesum(I(matrix >:> o.matrix)).toInt
    def #>=(o: RichMatrix): Int = breezesum(I(matrix >:> o.matrix)).toInt
    def #<=(o: RichMatrix): Int = breezesum(I(matrix <:< o.matrix)).toInt

    def |<(o: Int): Int = breezesum(breezemax(matrix, o)) - o*matrix.size
    def |<=(o: Int): Int = breezesum(breezemax(matrix, o+1)) - (o+1)*matrix.size
    def |>(o: Int): Int = breezesum(breezemin(matrix, o)) + o*matrix.size
    def |>=(o: Int): Int = breezesum(breezemin(matrix, o-1)) + (o-1)*matrix.size

    def |<(o: RichMatrix): Int = breezesum(breezemax(matrix, o.matrix)) - breezesum(o.matrix)
    def |<=(o: RichMatrix): Int = breezesum(breezemax(matrix, o.matrix+1)) - breezesum(o.matrix+1)
    def |>(o: RichMatrix): Int = breezesum(breezemin(matrix, o.matrix)) + breezesum(o.matrix)
    def |>=(o: RichMatrix): Int = breezesum(breezemin(matrix, o.matrix-1)) + breezesum(o.matrix-1)

    def +<>(o: RichMatrix): Int = breezesum(signum(matrix - o.matrix)).toInt
    def +<>(o: Int): Int = breezesum(signum(matrix - o)).toInt

    // the map call makes these slow
    def <>(o: RichMatrix): RichMatrix = RichMatrix(signum(matrix - o.matrix) map (_.toInt))
    def <>(o: Int): RichMatrix = RichMatrix(signum(matrix - o) map (_.toInt))
  }
}
