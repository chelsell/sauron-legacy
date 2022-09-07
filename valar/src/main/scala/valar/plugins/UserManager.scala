package valar.plugins

import com.typesafe.scalalogging.LazyLogging
import valar.core.Tables.Users
import valar.core.{loadDb, exec}
import valar.core.Security
import slick.jdbc.JdbcBackend.Database

object UserManager extends LazyLogging {

  implicit val db: Database = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def addUser(
      username: String,
      firstName: String,
      lastName: String,
      password: Option[String],
      writeAccess: Boolean
  ): Unit = {
    (Users filter (_.username === username)).headOption match {
      case Some(user) => throw new IllegalStateException(s"User $username already exists")
      case None =>
        exec(Users += UsersRow(
          id = 0,
          username = username,
          firstName = firstName,
          lastName = lastName
        ))
        exec(Refs += RefsRow(
          id = 0,
          name="manual:"+username
        ))
        setPassword(username, password)
        setWriteAccess(username, writeAccess)
    }
  }

  def setWriteAccess(username: String, access: Boolean): Unit = {
    exec(Users filter (_.username === username) map (_.writeAccess) update access)
  }

  def setPassword(username: String, password: Option[String]): Unit = {
    val hash = password map Security.bcrypt
    val nChanged: Int = exec(Users filter (_.username === username) map (_.bcryptHash) update hash)
    if (nChanged != 1) throw new IllegalArgumentException(s"No user with username $username exists")
  }

}
