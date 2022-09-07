package valar.importer

import java.time.{Duration, LocalDateTime}
import java.time.format.DateTimeFormatter

import slick.jdbc.JdbcBackend.Database
import com.typesafe.scalalogging.LazyLogging
import valar.core._
import pippin.misc.FileHasher
import slick.jdbc.JdbcBackend._

import scala.language.implicitConversions
import collection.JavaConverters._
import pippin.core._
import valar.core.DateTimeUtils._
import valar.core.Tables.{SubmissionRecords, SubmissionsRow}
import pippin.grammars._
import valar.params.layouts.post.{FullPlateInfo, PlateConstruction}
import valar.core.ImageCodec

import scala.io.Source


object Importer extends LazyLogging {

  implicit val db: Database = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(result: SubmissionResult): Runs = {

    try {

      def update = updateStatus(result)(_)
      update("inserting")

      logger.info(s"Processing loaded directory for ${result.submission.lookupHash}...")
      val submission = result.submission
      val timezone = result.config.local.timezone.name

      // if a run for this submission was already inserted, delete it
      // So we can fix issues with plate type, person plated, or datetime plated, delete the plate if we can
      exec((Runs filter (_.submissionId === submission.id)).result).headOption foreach { priorRun =>
        logger.warn(s"Submission ${submission.lookupHash} was already used for plate run ${priorRun.id}. Deleting.")
        exec(Runs filter (_.id === priorRun.id) delete)
        val otherRunsOnPlate = exec((Runs filter (_.plateId === priorRun.plateId) map (_.id)).result)
        if (otherRunsOnPlate.nonEmpty) {
        exec(Plates filter (_.id === priorRun.plateId) delete)
        logger.warn(s"Deleted ${priorRun.plateId} because no other plate runs were attached to it.")
        } else {
        logger.warn(s"Not deleting plate ${priorRun.plateId} because other runs used it: $otherRunsOnPlate).")
        }
      }

      val experiment = exec((Experiments filter (_.id === submission.experimentId)).result).head
      val templatePlate = exec((TemplatePlates filter (_.id === experiment.templatePlateId)).result).head
      val plateType = exec((PlateTypes filter (_.id === templatePlate.plateTypeId)).result).head
      logger.info(s"The data will be inserted into experiment ${experiment.name} (ID ${experiment.id}).")

      val roi = result.config.sauron.rois.rois(plateType.id)
      if (plateType.nRows != roi.nRows || plateType.nColumns != roi.nColumns)
        throw new SubmissionInconsistencyException(
        """" +
        "Plate dimensions are (${plateType.nRows}, ${plateType.nColumns}) in the plate_type $plateType.id, which sauronx_submission references," +
        "but (${result.config.sauron.roi.nRows}, {result.config.sauron.roi.nRows}) in the TOML."""
        )
      if (plateType.nRows * plateType.nColumns > 127)
        throw new SubmissionInconsistencyException(s"Plate type ${plateType.id} has ${plateType.nRows} and ${plateType.nColumns}, giving it more than 127 wells, which is currently unsupported.")
      val grid = AlphanumericGrid(plateType.nRows, plateType.nColumns)
      import grid.Point

      /*
       * Now we start inserting stuff
       */

      val sauronConfig = handleSauronConfig(result)

      val toml = handleToml(result.tomlText)

      val (plate, plateIsNew) = handlePlate(submission, experiment, templatePlate)

      val run = handlePlateRun(result, sauronConfig, toml, plate, submission, experiment, templatePlate)

      try {

        handleLogFile(result.logFileText, run)

        // determine actual plate layout from expression
        val stuff = PlateConstruction.parse(submission)

        logger.info("Inserting ROIs...")
        val rois = calcRois(result, plateType)

        // now insert the wells
        logger.info("Inserting wells...")
        for (row <- 1.toShort to plateType.nRows; column <- 1.toShort to plateType.nColumns) {
          val index = Point(row, column).index.toShort
          assert(row.toInt * column.toInt < Short.MaxValue, s"Well index for ($row, $column) exceeds range of signed short")
          val well = handleWellAndTreatments(run, index, stuff)
          val roi = insertRoi(well, rois(well.wellIndex.toInt - 1))
        }

        //update("inserting sensors")
        //new RegistrySensorProcessor(result).apply(run)

        //update("inserting features")
        //new FeatureProcessor(result).apply(run)

        logger.info(s"Done with ${result.submission.lookupHash}.")

        update("available")

      } catch { // attempt to clean up
        case e: Throwable => try {
          logger.error(s"Cleanup: deleting run ${run.id}")
          exec(Runs filter (_.id === run.id) delete)
          if (plateIsNew) {
            logger.error(s"Cleanup: deleting plate ${plate.id}")
            exec(Plates filter (_.id === plate.id) delete)
          }
        } finally throw e
      }

    } catch {
      case e: Throwable =>
        try {
          updateStatus(result)("insert failed")
        } finally throw e
    }
    run
  }


  private def updateStatus(result: SubmissionResult)(status: String) = {
    exec(SubmissionRecords += SubmissionRecordsRow(
        id = 0,
        datetimeModified = timestamp(),
        status = Some(status),
        submissionId = result.submission.id,
        sauronId = result.config.sauron.number,
        created = toSqlTimestamp(result.environment.datetimeStarted.atZone(DateTimeUtils.dbZone))
    ))
  }

  private def calcRois(result: SubmissionResult, plateType: PlateTypesRow): Array[Roi] = {
    val info = result.config.sauron.rois.rois(plateType.id) // can fail, but only if SauronX allowed a bad plate run
    val width = info.x1 - info.x0
    val height = info.y1 - info.y0
    var x = info.x0
    var y = info.y0
    var built = new scala.collection.mutable.ArrayBuffer[Roi]()
    for (row <- 0 until info.nRows) {
      for (column <- 0 until info.nColumns) {
        built += Roi(math.round(x).toInt, math.round(x + width).toInt, math.round(y).toInt, math.round(y + height).toInt)
        x += width + info.padX
      }
      y += height + info.padY
      x = info.x0
    }
    built.toArray
  }


  private def insertRoi(well: WellsRow, roi: Roi): RoisRow = {
    val insertRoiQuery = Rois returning (Rois map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(insertRoiQuery += RoisRow(
      id = 0,
      wellId = well.id,
      x0 = roi.x0.toShort,
      y0 = roi.y0.toShort,
      x1 = roi.x1.toShort,
      y1 = roi.y1.toShort,
      refId = 63 // TODO don't hardcode
    ))
  }


  private def handleWellAndTreatments(
      run: RunsRow, index: Short,
      stuff: FullPlateInfo
    ): WellsRow = {

    logger.debug(s"Inserting well at index $index")
    val insertWellQuery = Wells returning (Wells map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val well = exec(insertWellQuery += WellsRow(
      id = 0,
      runId = run.id,
      wellIndex = index,
      controlTypeId = stuff.controls(index) map (_.id),
      variantId = stuff.variants(index) map (_.id),
      wellGroup = stuff.groups(index),
      n = stuff.nFish(index),
      age = stuff.ages(index),
      created = timestamp()
    ))

    // insert the treatments
    val matchingCompounds = stuff.compounds.getOrElse(index, Nil)
    val matchingDoses = stuff.doses.getOrElse(index, Nil)
    logger.debug(s"Inserting ${matchingCompounds.size} treatments at index $index")
    assert(matchingCompounds.size == matchingDoses.size, s"There are ${matchingCompounds.size} compounds but ${matchingDoses.size} doses")
    val insertTreatmentQuery = WellTreatments returning (WellTreatments map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val treatments: Seq[WellTreatmentsRow] = matchingCompounds zip matchingDoses map { case (compound: BatchesRow, dose: Double) =>
      logger.debug(s"Inserting treatment ${compound.id} at dose $dose for well $index")
      exec(insertTreatmentQuery += WellTreatmentsRow(
        id = 0,
        wellId = well.id,
        batchId = compound.id,
        micromolarDose = Some(dose)
      ))
    }

    well
  }


  private def handleToml(text: String): ConfigFilesRow = {
    val sha1 = bytesToHashBlob(text.getBytes)
    val toml = exec((ConfigFiles filter (_.textSha1 === sha1) map (r => r.?)).result).flatten.headOption
    toml getOrElse {
      val insertQuery = ConfigFiles returning (ConfigFiles map (_.id)) into ((newRow, id) => newRow.copy(id = id))
      val newToml = exec(insertQuery += ConfigFilesRow(
        id = 0,
        tomlText = text,
        textSha1 = sha1,
        created = timestamp()
      ))
      logger.info(s"Inserted new row ${newToml.id} in config_files.")
      newToml
    }
  }

  private def handleLogFile(text: String, run: RunsRow): LogFilesRow = {
    val sha1 = bytesToHashBlob(text.getBytes)
    val insertQuery = LogFiles returning (LogFiles map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val logFile = exec(insertQuery += LogFilesRow(
      id = 0,
      runId = run.id,
      text = text,
      textSha1 = sha1,
      created = timestamp()
    ))
    logger.info(s"Inserted new row ${logFile.id} in log_files.")
    logFile
  }


  private def handlePlateRunInfo(result: SubmissionResult, plateRun: RunsRow) = {
    def insert(key: String, rawValue: String): Unit = {
      val value = if (rawValue.length <= 10000) rawValue else {
        logger.warn(s"Value for $key in environment.properties is too long (>10,000 chars). Truncating.")
        rawValue.substring(0, 10000)
      }
      exec {
        RunTags += RunTagsRow(
          id = 0,
          runId = plateRun.id,
          name = key,
          value = value
        )
      }
    }
    for ((key, value) <- result.environment.data) {
      insert(key, value)
    }
    logger.info("Inserted run info.")
  }


  private def handlePlateRun(result: SubmissionResult, sauronConfig: SauronConfigsRow, toml: ConfigFilesRow, plate: PlatesRow, submission: SubmissionsRow, experiment: ExperimentsRow, templatePlate: TemplatePlatesRow): RunsRow = {

    logger.info("Inserting run...")

    val timezone = result.config.local.timezone.name
    val incubationMinutes = if (submission.datetimeDosed.isEmpty) None else Some {
      val dtPlated = DateTimeUtils.fromSqlTimestamp(submission.datetimePlated, timezone)
      val dtDosed = DateTimeUtils.fromSqlTimestamp(submission.datetimeDosed.get, timezone)
      Duration.between(dtPlated, dtDosed).getSeconds.toInt / 60
    }

    val insertQuery = Runs returning (Runs map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val run: RunsRow = exec(insertQuery += RunsRow(
      id = 0,
      experimentId = experiment.id,
      plateId = plate.id,
      description = submission.description,
      experimentalistId = submission.userId,
      submissionId = Some(submission.id),
      datetimeRun = sqlDatetimeStarted(result),
      datetimeDosed = submission.datetimeDosed,
      name = None,
      tag = generateTag(sauronConfig.sauronId, result),
      sauronConfigId = sauronConfig.id,
      configFileId = Some(toml.id),
      incubationMin = incubationMinutes,
      acclimationSec = submission.acclimationSec,
      notes = None,
      created = timestamp()
    ))

    //val tag = generateTag(run, sauronConfig.sauronId, result)
    //exec(Runs filter (_.id === run.id) map (_.tag) update tag)
    val name = generateName(run, sauronConfig.sauronId, result)
    exec(Runs filter (_.id === run.id) map (_.name) update Some(name))
    val r = exec((Runs filter (_.id === run.id)).result).head
    logger.info(s"Inserted run ${r.id} / ${r.tag} / ${r.name}.")
    handlePlateRunInfo(result, run)
    run
  }

  private def generateTag(sauronId: Byte, result: SubmissionResult): String = {
    val date = result.environment.datetimeStarted.format(DateTimeFormatter.ofPattern("yyyyMMdd"))
    val time = result.environment.datetimeStarted.format(DateTimeFormatter.ofPattern("HHmmss"))
    s"${date}.${time}.S${sauronId}"
  }

  private def generateName(run: RunsRow, sauronId: Byte, result: SubmissionResult): String = {
    val user = exec((Users filter (_.id === run.experimentalistId)).result).head
    val date = result.environment.datetimeStarted.format(DateTimeFormatter.ofPattern("yyyyMMdd"))
    val time = result.environment.datetimeStarted.format(DateTimeFormatter.ofPattern("HHmmss"))
    val sauronText = "%02d".format(sauronId)
    val nBefore = exec((Runs filter (_.plateId === run.plateId) filter (_.datetimeRun < sqlDatetimeStarted(result))).result).length
    s"$date-r${run.id}-u${initials(user)}-S$sauronText-$nBefore-$time"
  }


  private def initials(user: UsersRow): String = {
    var use = true
    var s = ""
    for (z <- (user.firstName + " " + user.lastName).zipWithIndex) {
      val i = z._2
      val c = z._1
      if (use && c.isUpper && !c.isLower) {
        s += c
      }
      use = !c.isLower
    }
    s
  }

  private def sqlDatetimeStarted(result: SubmissionResult) =
    DateTimeUtils.toSqlTimestamp(
      result.environment.datetimeStarted
      .atZone(result.config.local.timezone.name)
    )

  private def handlePlate(submission: SubmissionsRow, experiment: ExperimentsRow, templatePlate: TemplatePlatesRow): (PlatesRow, Boolean) = {
    val plate: Option[PlatesRow] = if (submission.continuingId.isDefined) {
      val run = exec((Runs filter (_.submissionId === submission.continuingId)).result).headOption
      run map {r =>
        exec((Plates filter (_.id === r.plateId)).result).head
      }
    } else None
    plate map { p =>
      logger.info(s"Using existing plate ${p.id}.")
      (p, false)
    } getOrElse {
      val insertQuery = Plates returning (Plates map (_.id)) into ((newRow, id) => newRow.copy(id = id))
      val newPlate = exec(insertQuery += PlatesRow(
        id = 0,
        plateTypeId = Some(templatePlate.plateTypeId),
        personPlatedId = submission.personPlatedId,
        datetimePlated = Some(submission.datetimePlated),
        created = timestamp()
      ))
      logger.info(s"Inserted new plate ${newPlate.id}.")
      (newPlate, true)
    }
  }


  private def handleSauronConfig(result: SubmissionResult): SauronConfigsRow = {
    val n = result.config.sauron.number
    val sauron = exec((Saurons filter (_.id === n)).result).headOption
    if (sauron.isEmpty) throw new SubmissionInconsistencyException(s"No sauron with number ${result.config.sauron.number} exists")
    val lastModDatetime = DateTimeUtils.toSqlTimestamp(result.config.sauron.lastModificationDateTime.atZone(result.config.local.timezone.name))
    val sauronConfig: Option[SauronConfigsRow] = exec((SauronConfigs filter (_.sauronId === sauron.get.id) filter (_.datetimeChanged === lastModDatetime)).result).headOption
    sauronConfig getOrElse {
      val insertQuery = SauronConfigs returning (SauronConfigs map (_.id)) into ((newRow, id) => newRow.copy(id = id))
      val newSauronConfig = exec(insertQuery += SauronConfigsRow(
        id = 0,
        sauronId = sauron.get.id,
        datetimeChanged = lastModDatetime,
        description = result.config.sauron.mostRecentModificationDescription,
        created = timestamp()
      ))
      logger.info(s"Inserted new sauron_config ${newSauronConfig.id} for S${sauron.get.id} modified at $lastModDatetime (our time).")
      newSauronConfig
    }
  }
}
