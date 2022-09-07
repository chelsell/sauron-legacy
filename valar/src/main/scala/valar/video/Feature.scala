package valar.video

import com.typesafe.scalalogging.LazyLogging
import valar.video.RichMatrices.RichMatrix
import valar.video.TraversableImplicits._
import valar.core.{exec, loadDb}

import scala.language.implicitConversions
import scala.reflect.ClassTag

/**
  * A Feature maps a time-series of matrices to an output array.
  */
sealed trait VFeature[@specialized(Byte, Short, Int, Long, Float, Double) V] {
  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._
  val name: String
  final lazy val valarObj: FeaturesRow = exec((Features filter (_.name === name)).result).headOption getOrElse (throw new IllegalArgumentException(s"There is no feature with name $name"))
  final lazy val valarId: Byte = valarObj.id
  def apply(input: Iterator[RichMatrix]): Array[V]
//  def bytes(array: Array[V]): Array[Byte]
}


/**
 * A time-dependent feature F has a number of elements n for a video of n frames.
 * They can be broken into consecutive pieces calculated independently; that is:
 * F = [F_1, F_2, ..., F_n] = [F(0, 1), F(1, 2), ..., F(n-1, n)]
 * Each F_t is an element in T.
 */
trait VTimeFeature[@specialized(Byte, Short, Int, Long, Float, Double) V] extends VFeature[V] with LazyLogging {

  /**
    * Calculates a time-dependent feature in chunks, two frames at a time.
    */
  def applyOnAll(
      video: VideoFile, rois: Traversable[Roi]
  )(implicit tag: ClassTag[V]): Map[Roi, Array[V]] = {
    val nFrames = video.nFrames
    val results: Map[Roi, Array[V]] = (rois map (roi => roi -> Array.ofDim[V](nFrames))).toMap
    val slid = video.reader() takeWhile (_ != null) map (f => BlazingMatrix.of(f).toBreezeMatrix) sliding 2
    var i = 0
    slid foreach { case Seq(prevImage, nextImage) =>
      for (roi <- rois) {
        results(roi)(i + 1) = apply( // + 1 so that index 0 is 0
          Iterator(prevImage `//` roi, nextImage `//` roi)
        ).toTraversable.only(
          excessError = seq => throw new AssertionError(s"The time-dependent feature ${getClass.getSimpleName} returned ${seq.size} != 1 calculated between two frames")
        )
      }
      i += 1
    }
    if (i == nFrames) logger.info(s"Expected $nFrames and got $i")
    else logger.warn(s"Expected $nFrames but got $i")
    results
  }
}
