package valar.core

import java.io.ByteArrayInputStream
import java.nio.charset.StandardCharsets
import java.sql.Blob

import org.mindrot.jbcrypt.BCrypt
import pippin.core._
import slick.jdbc.JdbcBackend._

class Security(implicit database: Database) {

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def check(username: String, password: String): Boolean = {
    val o: Option[Option[String]] = exec((Users filter (_.username === username) map (_.bcryptHash)).result).headOption
    if (o.isDefined && o.get.isDefined) {
      val savedHex = o.get.get
      BCrypt.checkpw(password, savedHex)
    } else false
  }

  def bcrypt(password: String): String = {
    BCrypt.hashpw(password, BCrypt.gensalt(13))
  }

}
