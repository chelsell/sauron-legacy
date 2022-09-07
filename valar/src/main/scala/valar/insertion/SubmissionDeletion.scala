package valar.insertion

import java.sql.Date
import java.time.LocalDate

import com.typesafe.scalalogging.Logger
import valar.core.DateTimeUtils.timestamp
import valar.core.{exec, loadDb}


object SubmissionDeletion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def delete(lookupHash: String, user: UsersRow): Unit = {
    exec((Submissions filter (_.lookupHash === lookupHash)).result).headOption match {
      case Some(s) => delete(s, user)
      case None => throw new LookupFailedException(s"No submission with lookup hash $lookupHash exists")
    }
  }

  def delete(submission: SubmissionsRow, user: UsersRow): Unit = attempt { () => {
    val run = exec((Runs filter (_.submissionId === submission.id)).result).headOption
    if (run.isDefined) {
      throw new ValidationException(s"Cannot delete ${submission.lookupHash} because it is associated with run ${run.get.id}")
    } else if (!hasAcceptableRecords(submission) ) {
      throw new RefusalException(s"Refusing to delete submission ${submission.lookupHash} because the data was already transferred to Valar")
    } else if (submission.userId == user.id) {
      throw new RefusalException(s"Refusing to delete submission ${submission.lookupHash} because another user created it")
    } else {
      exec((Submissions filter (_.id === submission.id)).delete)
    }
  }}

  private def hasAcceptableRecords(submission: SubmissionsRow): Boolean = {
    val history = exec((SubmissionRecords filter (_.submissionId === submission.id)).result)
    history forall ( h => acceptableStatuses contains h.status.getOrElse(""))
  }

  private val acceptableStatuses = Set("starting","capturing","failed","cancelled","extracting","compressing","uploading")

}
