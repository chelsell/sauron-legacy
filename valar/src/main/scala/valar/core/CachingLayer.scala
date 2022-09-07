package valar.core

import com.typesafe.scalalogging.Logger
import slick.jdbc.JdbcBackend.Database
import valar.core.CommonQueries.getClass
import valar.core.Tables.Saurons

class CachingLayer0 {

  val logger: Logger = Logger(getClass)
  implicit val db: Database = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  val saurons: Seq[SauronsRow] =
    exec(Saurons.result)

  val stimuli: Seq[StimuliRow] =
    exec(Stimuli.result)

  val users: Seq[UsersRow] =
    exec(Users.result)

  val loginUsers: Seq[UsersRow] =
    users filter (_.bcryptHash.isDefined)

  val writeAuthorizedUsers: Seq[UsersRow] =
    users filter (_.bcryptHash.isDefined) filter (_.writeAccess)

}

class CachingLayer1 extends CachingLayer0 {

  val logger: Logger = Logger(getClass)
  implicit val db: Database = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  val refs: Seq[RefsRow] =
    exec(Refs.result)

  val suppliers: Seq[SuppliersRow] =
    exec(Suppliers.result)

}
