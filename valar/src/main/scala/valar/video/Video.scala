package valar.video

import java.io.{Closeable, File}
import java.nio.file.{Files, Path, Paths}
import java.util.NoSuchElementException

import breeze.linalg.DenseMatrix
import com.typesafe.scalalogging.LazyLogging
import valar.video.Codec.H265Crf
import pippin.misc.{FileHasher, ValidationFailedException}
import org.bytedeco.javacpp.avformat.AVFormatContext
import org.bytedeco.javacpp.opencv_core.Mat
import org.bytedeco.javacv.{FFmpegFrameGrabber, Frame, OpenCVFrameConverter}
import org.bytedeco.javacpp.opencv_imgproc.cvtColor
import org.bytedeco.javacpp.opencv_imgproc.COLOR_YUV2GRAY_420

import scala.io.Source
import scala.util.{Failure, Success, Try}

trait ContainerFormat {
  def name: String
  def ext: String
}
object ContainerFormat {
  case object Mkv extends ContainerFormat {
    override val ext = ".mkv"
    override def name: String = "Matroska Multimedia Container"
  }
  case object Avi extends ContainerFormat {
    val ext = ".avi"
    override def name = "Audio Video Interleaved"
  }
}

trait Codec {
  def name: String
  def ext: String
}
object Codec {
  case class H265Crf(crf: Byte) extends Codec with Comparable[H265Crf] {
    require(crf > 0 && crf < 52, s"Invalid CRF $crf")
    override def name: String = "High Efficiency Video Coding"
    override def ext: String = ".x265-" + crf
    override def compareTo(o: H265Crf): Int = crf compareTo o.crf
  }
  case class H264Crf(crf: Byte) extends Codec with Comparable[H265Crf] {
    require(crf > 0 && crf < 52, s"Invalid CRF $crf")
    override def name: String = "MPEG-4 Part 10, Advanced Video Coding"
    override def ext: String = ".x264-" + crf
    override def compareTo(o: H265Crf): Int = crf compareTo o.crf
  }
}


case class VideoFile(path: Path, containerFormat: ContainerFormat, codec: Codec) extends LazyLogging {
  require(Files.isRegularFile(path), s"$path is not a file")
  private val hashFile = Paths.get(path.toString + ".sha256")
  if (!Files.isRegularFile(hashFile)) {
    logger.warn(s"Hash file $hashFile does not exist")
  }
  def validates: Boolean = {
    require(Files.isRegularFile(hashFile), s"No sha256 file for $path exists")
    val sha256 = Source.fromFile(hashFile.toFile).mkString.trim
    Try(new FileHasher("SHA-256").validate(path, sha256)) match {
      case Success(_) => true
      case Failure(e: ValidationFailedException) => false
      case Failure(e) => throw e
    }
  }
  def peekAt[V](getter: VideoIterator => V): V = VideoIterator.peekAt(path)(getter)
  def nFrames: Int = peekAt(_.lengthInFrames)
  def nMicroseconds: Long = peekAt(_.lengthInTime)
  def reader(): VideoIterator = VideoIterator.from(path)
}


class VideoIterator(grabber: FFmpegFrameGrabber) extends Iterator[Frame] with Closeable with LazyLogging  {

  grabber.start()
  override val length: Int = grabber.getLengthInFrames
  private var i = 0
  override def hasNext: Boolean = i < length - 1
  logger.info(s"Video has $length frames") // important to log because it can be wrong (see note below)

  override def next(): Frame = {
    if (i == length - 1) {
      close()
    }
//    grabber.setFrameNumber(i)
    i += 1
    /*
     * Read the Javadoc for FrameGrabber.grab() carefully:
     * Although it returns a new Frame, that Frame is always that same. That is:
     * frame.grab() == frame.grab()
     * Instead, it replaces the buffer of the old frame to reduce the frequency of GC.
     * We could probably exploit this, but this is simpler.
     */
    val grabbed = grabber.grab()
    /*
    So the issue here is:
    Sometimes the length from grabber.getLengthInFrames is wrong by about +5 frames.
    To work around this issue, calling code *may* be designed to expect null values.
    Either way, it's better than a NPE here.
     */
    if (grabbed == null) null else grabbed.clone()
  }

  override def close(): Unit = {
    grabber.close()
  }

  def frameNumber(frameNumber: Int): Unit = grabber.setFrameNumber(frameNumber)
  def sampleRate: Int = grabber.getSampleRate
  def videoMetadata(key: String): String = grabber.getVideoMetadata(key)
  def audioBitrate: Int = grabber.getAudioBitrate
  def audioChannels: Int = grabber.getAudioChannels
  def videoBitrate: Int = grabber.getVideoBitrate
  def sampleFormat: Int = grabber.getSampleFormat
  def audioMetadata(key: String): String = grabber.getAudioMetadata(key)
  def formatContext: AVFormatContext = grabber.getFormatContext
  def imageHeight: Int = grabber.getImageHeight
  def audioCodec: Int = grabber.getAudioCodec
  def aspectRatio: Double = grabber.getAspectRatio
  def format: String = grabber.getFormat
  def pixelFormat: Int = grabber.getPixelFormat
  def metadata(key: String): String = grabber.getMetadata(key)
  def lengthInFrames: Int = grabber.getLengthInFrames
  def gamma: Double = grabber.getGamma
  def videoCodec: Int = grabber.getVideoCodec
  def frameRate: Double = grabber.getFrameRate
  def imageWidth: Int = grabber.getImageWidth
  def lengthInTime: Long = grabber.getLengthInTime
}

object VideoIterator {
  def from(path: Path) = new VideoIterator(new FFmpegFrameGrabber(path.toFile))
  def peekAt[V](path: Path)(getter: VideoIterator => V): V = peekAt(from(path))(getter)
  def peekAt[V](iterator: VideoIterator)(getter: VideoIterator => V): V = {
    var iter = null: VideoIterator
    try {
      getter(iterator)
    } finally {
      if (iter != null) iter.close()
    }
  }
}
