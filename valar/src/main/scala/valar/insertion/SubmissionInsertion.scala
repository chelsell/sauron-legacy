package valar.insertion

import java.sql.Timestamp

import com.typesafe.scalalogging.Logger
import pippin.core.addons.SecureRandom
import valar.core.DateTimeUtils.timestamp
import valar.core.{DateTimeUtils, exec, loadDb}
import valar.params.layouts.PreLayoutUtils
import valar.params.layouts.post.LayoutParameterizations


object SubmissionInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  /**
    * Inserts the submission unless something failed.
    * The submission is always a new row.
    */
  def insert(data: SubmissionData): SubmissionsRow = attempt { () => {
    validate(data)
    val sub = insertSubmission(data)
    withCleanup { () =>
        insertParams(data, sub)
    }{ () =>
      exec(Submissions filter (_.id === sub.id) delete)
    }
    sub
  }}

  private def validate(data: SubmissionData): Unit = {
    val templatePlate = getTemplatePlate(data).get
    val treatments = exec((TemplateTreatments filter (_.templatePlateId === templatePlate.id)).result)
    if (data.datetimeDosed.isDefined ^ treatments.nonEmpty) {
      throw new ValidationException("The datetime dosed must be filled in if and only if the plate has compound treatments")
    }
  }

  /**
    * Inserts the submission but not params.
    */
  private def insertSubmission(data: SubmissionData): SubmissionsRow = {
    val query = Submissions returning (Submissions map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    // we never handle timezones on the browser, so we always assume (everywhere) that it's the db timezone
    val dtd = data.datetimeDosed map (dt => DateTimeUtils.toSqlTimestamp(dt.atZone(DateTimeUtils.dbZone)))
    val dtp = DateTimeUtils.toSqlTimestamp(data.datetimePlated.atZone(DateTimeUtils.dbZone))
    exec(query += SubmissionsRow(
      id = 0,
      lookupHash = newSubHash(),
      experimentId = data.experiment,
      userId = data.creator,
      personPlatedId = data.personPlated,
      continuingId =  getMatchingPlate(data) map (_.id),
      datetimePlated = dtp,
      datetimeDosed = dtd,
      acclimationSec = Some(data.acclimationSecs),
      description = data.description,
      notes = data.notes,
      created = timestamp()
    ))
  }

  /**
    * Parses parameterization text and inserts into SubmissionsParams.
    */
  private def insertParams(data: SubmissionData, sub: SubmissionsRow): Seq[SubmissionParamsRow] = {
    val templatePlate = getTemplatePlate(sub).get // we know the template plate exists because this is SauronX
    val wellIzation = PreLayoutUtils.parseTreatmentParams(data.treatmentParameters, templatePlate)
    val treatmentIzation = PreLayoutUtils.parseTreatmentParams(data.treatmentParameters, templatePlate)
    val query = SubmissionParams returning (SubmissionParams map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    for ((plateParam, plateSub) <- wellIzation ++ treatmentIzation) yield
      exec(query += SubmissionParamsRow(
        id = 0,
        submissionId = sub.id,
        paramType = plateParam.origin.name,
        name = plateParam.param.name,
        value = plateSub.valueToText
      ))
  }.toSeq

  /**
    * If the plate is being rerun, checks for a matching previous run.
    * A run matches if:
    *   - It was run on SauronX (has a submission)
    *   - The datetime plated matches
    *   - The person plated matches
    *   - The plate type matches (technically, also if the prior run does not have a plate type)
    */
  private def getMatchingPlate(data: SubmissionData): Option[SubmissionsRow] = {
    if (data.rerunning) {
      val experiment = exec((Experiments filter (_.id === data.experiment)).result).head
      val dtp = DateTimeUtils.toSqlTimestamp(data.datetimePlated.atZone(DateTimeUtils.dbZone))
      matchingPlate(experiment, data.personPlated, dtp) orElse {
        throw new LookupFailedException("Matching plate not found. The plate must be plated at the same time by the same person and have the same plate type.")
      }
    } else None
  }

  private def matchingPlate(experiment: ExperimentsRow, personPlated: Int, datetimePlated: Timestamp): Option[SubmissionsRow] = {
    exec((
      Submissions filter (_.datetimePlated === datetimePlated) filter (_.personPlatedId === personPlated)
    ).result).headOption filter (prevSub => plateTypesMatch(prevSub, experiment))
  }

  private def plateTypesMatch(prevSub: SubmissionsRow, newExperiment: ExperimentsRow): Boolean = {
    getPlateType(prevSub) map (_.id) forall { prevPlateType =>
      val newPlateType = exec((TemplatePlates filter (_.id === newExperiment.templatePlateId.get) map (_.plateTypeId)).result).head
      newPlateType == prevPlateType
    }
  }

  private def getPlateType(sub: SubmissionsRow): Option[PlateTypesRow] = {
    getTemplatePlate(sub) flatMap { tp =>
      exec((PlateTypes filter (_.id === tp.plateTypeId)).result).headOption
    }
  }

  private def getTemplatePlate(data: SubmissionData): Option[TemplatePlatesRow] = {
    val templatePlateId = exec((Experiments filter (_.id === data.experiment) map (_.templatePlateId)).result).head
    exec((TemplatePlates filter (_.id === templatePlateId)).result).headOption
  }

  private def getTemplatePlate(sub: SubmissionsRow): Option[TemplatePlatesRow] = {
    // inefficient, but ok
    val templatePlateId = exec((Experiments filter (_.id === sub.experimentId) map (_.templatePlateId)).result).head
    exec((TemplatePlates filter (_.id === templatePlateId)).result).headOption
  }

  private val random = new SecureRandom()

  private def newSubHash(): String = (random.alphanumeric filter (c => c.isDigit || (Set('a', 'c', 'b', 'd', 'e', 'f') contains c)) take 12).mkString

}
