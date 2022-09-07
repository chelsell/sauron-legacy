package valar.insertion

import com.typesafe.scalalogging.Logger
import valar.core.{loadDb, exec}
import valar.params.assays.AssayParameters

import scala.language.implicitConversions
import collection.JavaConverters._
import pippin.core._
import valar.core.DateTimeUtils._


object AssayInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: TemplateAssayData): TemplateAssaysRow = attempt { () => {
    val assay = insertTemplateAssay(data)
    withCleanup { () =>
      insertTemplateStimulusFrames(data, assay)
    }{ () =>
      exec(TemplateAssays filter (_.id === assay.id) delete)
    }
    assay
  }}

  private def insertTemplateAssay(data: TemplateAssayData): TemplateAssaysRow = {
    val query = TemplateAssays returning (TemplateAssays map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += TemplateAssaysRow(
      id = 0,
      name = data.name,
      description = data.description,
      authorId = Some(data.creator),
      specializes = None,
      created = timestamp()
    ))
  }

  private def insertTemplateStimulusFrames(data: TemplateAssayData, assay: TemplateAssaysRow): Seq[TemplateStimulusFramesRow] = {
    val query = TemplateStimulusFrames returning (TemplateStimulusFrames map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    data.ranges.indices flatMap { i =>
      val range = data.ranges(i)
      val stimulus = data.stimuli(i)
      val value = data.values(i)
      val exists = range.trim.nonEmpty
      // TODO check?
      if (!exists) None else Some {
      exec(query += TemplateStimulusFramesRow(
        id = 0,
        templateAssayId = assay.id,
        rangeExpression = range,
        stimulusId = stimulus,
        valueExpression = value
      ))}
    }
  }
}
