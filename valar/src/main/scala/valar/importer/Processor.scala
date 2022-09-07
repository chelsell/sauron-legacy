package valar.importer

import valar.core.{exec, loadDb}

abstract class Processor(submissionResult: SubmissionResult) {

  private implicit val db = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def apply(plateRun: RunsRow): Unit
}

