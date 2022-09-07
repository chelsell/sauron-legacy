package valar.insertion

import java.sql.Date
import java.time.LocalDate

import com.typesafe.scalalogging.Logger
import valar.core.DateTimeUtils.timestamp
import valar.core.{exec, loadDb}


object AnnotationInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: AnnotationData): AnnotationsRow = attempt { () => {
    val query = Annotations returning (Annotations map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += AnnotationsRow(
      id = 0,
      name = data.name,
      value = None,
      level = data.level,
      runId = data.run,
      submissionId = data.submission,
      wellId = None,
      assayId = None,
      annotatorId = data.creator,
      description = data.description,
      created = timestamp()
    ))
  }}

  private def convertDate(d: LocalDate): Date = Date.valueOf(d)

}
