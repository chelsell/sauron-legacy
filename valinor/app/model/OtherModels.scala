package model

import kokellab.valar.core.Tables.{RunsRow, ExperimentsRow, SauronsRow, SubmissionRecordsRow, SubmissionsRow, UsersRow}

case class SubmissionInfo(run: RunsRow, submission: Option[SubmissionsRow], history: Seq[SubmissionRecordsRow])

case class SimpleSubmissionInfo(history: SubmissionRecordsRow, submission: SubmissionsRow, user: UsersRow)
