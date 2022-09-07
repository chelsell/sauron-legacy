package valar.insertion

import java.sql.Date
import java.time.LocalDate

import com.typesafe.scalalogging.Logger
import valar.core.DateTimeUtils.timestamp
import valar.core.{exec, loadDb}


object VariantInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: VariantData): GeneticVariantsRow = attempt { () => {
    val variant = insertVariant(data)
//    withCleanup { () =>
//      insertEvents(data, variant)
//    }{ () =>
//      exec(GeneticVariants filter (_.id === variant.id) delete)
//    }
    variant
  }}

  private def insertVariant(data: VariantData): GeneticVariantsRow = {
    val query = GeneticVariants returning (GeneticVariants map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += GeneticVariantsRow(
      id = 0,
      name = data.name,
      motherId = data.mother,
      fatherId = data.father,
      lineageType = Some(data.lineageType),
      dateCreated = data.dateCreated map convertDate,
      creatorId = data.creator,
      fullyAnnotated = false,
      created = timestamp()
    ))
  }

  private def convertDate(d: LocalDate): Date = Date.valueOf(d)

}
