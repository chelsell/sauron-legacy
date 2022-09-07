package valar.insertion

import com.typesafe.scalalogging.Logger
import valar.core.DateTimeUtils.timestamp
import valar.core.{exec, loadDb}


object ExperimentInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: ExperimentData): ExperimentsRow = attempt { () => {
    val project = exec((Projects filter (_.id === data.project)).result).head
    if (!(data.name startsWith (project.name + " :: "))) {
      throw new ValidationException(s"The experiment name must begin with ${project.name + " :: "}")
    }
    val query = Experiments returning (Experiments map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += ExperimentsRow(
      id = 0,
      name = data.name,
      description = data.description,
      creatorId = data.creator,
      projectId = data.project,
      batteryId = data.battery,
      templatePlateId = Some(data.templatePlate),
      transferPlateId = data.transferPlate,
      defaultAcclimationSec = data.acclimationSecs,
      notes = data.notes,
      active = true,
      created = timestamp()
    ))
  }}

}
