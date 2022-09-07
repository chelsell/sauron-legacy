package valar.video

import java.io.IOException
import java.nio.file.{Files, Path, Paths}
import scala.util.{Failure, Success, Try}
import valar.core.Tables.{Runs, RunsRow, PlateTypes, PlateTypesRow, PlatesRow, Rois, RoisRow}
import valar.core.{exec, loadDb}

object RoiUtils {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def manual(info: SimplePlateInfo): Map[WellsRow, RoisRow] = {
    val rois = exec((
      for {
        (roi, well) <- Rois join Wells on (_.wellId === _.id)
        if well.runId === info.run.id
      } yield (well, roi)
    ).result)
    if (rois.size != info.plateType.nRows * info.plateType.nColumns) {
      throw new AmbiguousException(s"Plate type ${info.plateType.id} has ${info.plateType.nRows*info.plateType.nColumns} wells, but found ${rois.size} manually defined ROIs") with LorienException
    }
    rois.toMap
  }
}


case class SimplePlateInfo(run: RunsRow, plate: PlatesRow, plateType: PlateTypesRow)

object SimplePlateInfo {

  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def fetch(runId: Int): SimplePlateInfo = {
    val stuff = exec((
      for {
        ((run, plate), plateType) <- Runs join Plates on (_.plateId === _.id) join PlateTypes on (_._2.plateTypeId === _.id)
        if run.id === runId
      } yield (run, plate, plateType)
    ).result).headOption.orNull
    require(stuff != null, s"No plate run with ID $runId exists")
    SimplePlateInfo(stuff._1, stuff._2, stuff._3)
  }
}
