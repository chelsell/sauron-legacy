package valar.insertion

import java.sql.{Date, Timestamp}
import java.time.{LocalDate, LocalDateTime, ZoneId, ZonedDateTime}

import com.typesafe.scalalogging.Logger
import pippin.misc.Chem
import pippin.core.{bytesToHashHex, intsToBytes}
import pippin.core
import pippin.core.addons.SecureRandom
import valar.core.DateTimeUtils.timestamp
import valar.core.{DateTimeUtils, ValarConfig, exec, loadDb}

import scala.util.{Failure, Success, Try}
import scala.util.control.NonFatal

object CompoundLabelInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: CompoundLabelData, refId: Byte): CompoundLabelsRow = attempt { () => {
    val result = exec((CompoundLabels filter (_.refId === data.refId) filter (_.compoundId === data.compoundId) filter (_.name === data.name)).result).headOption
    result getOrElse {
      val query = CompoundLabels returning (CompoundLabels map (_.id)) into ((newRow, id) => newRow.copy(id = id))
      exec(query += CompoundLabelsRow(
        id = 0,
        refId = data.refId,
        compoundId = data.compoundId,
        name = data.name,
        created = timestamp()
      ))
    }
  }}

}
