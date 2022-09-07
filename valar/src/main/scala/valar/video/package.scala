package valar.video

import java.nio.file.{Files, Path, Paths}

import breeze.linalg.DenseMatrix
import com.sksamuel.scrimage.{Grayscale, Image, Pixel}
import pippin.core.thisGitCommitSha1Bytes
import pippin.core._
import java.lang.AssertionError
import valar.core.loadDb

package object core {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  lazy val lorienCommitHash: Array[Byte] = thisGitCommitSha1Bytes

  def indicate(b: Boolean): Int = if (b) 1 else 0

  object TraversableImplicits {
    implicit class TraversableImplicit[T](seq: Traversable[T]) {
      def only(
        emptyError: Traversable[T] => Nothing = seq => throw new AssertionError("Sequence is empty"),
        excessError: Traversable[T] => Nothing = seq => throw new AssertionError("There are ${traversable.size} elements")
      ): T = seq.size match {
        case 1 => seq.head
        case 0 => emptyError(seq)
        case _ => excessError(seq)
      }
    }
  }

  trait LorienException extends Exception
  class FeatureCalculationFailedException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with LorienException
  class MissingException(message: String = null) extends Exception(message) with LorienException
  class InconsistencyException(message: String = null) extends Exception(message) with LorienException
  class AmbiguousException(message: String = null) extends Exception(message) with LorienException

}
