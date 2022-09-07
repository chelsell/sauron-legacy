package valar.video

import valar.core.Tables.WellsRow
import valar.core.loadDb

case class Roi(x0: Int, x1: Int, y0: Int, y1: Int, wellId: Int) {
  lazy val coordinates: (Int, Int, Int, Int) = (x0, x1, y0, y1)
  lazy val width: Int = x1 - x0
  lazy val height: Int = y1 - y0
  def xyWidthHeight: (Int, Int, Int, Int) = (x0, y0, x1 - x0, y1 - y0)
  def coordinateString = s"($x0,$x1,$y0,$y1)"
  override def toString: String = s"Roi($wellId: ($x0,$x1,$y0,$y1))"
}

trait WellRoi extends Roi {
  def well: WellsRow
}

object Roi {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def of(roi: RoisRow, wellId: Int): Roi = {
    Roi(roi.x0, roi.x1, roi.y0, roi.y1, wellId)
  }
}
