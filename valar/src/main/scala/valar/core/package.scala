package valar

import com.typesafe.scalalogging.LazyLogging
import slick.jdbc.JdbcBackend.Database
import slick.dbio.DBIO
import slick.jdbc.JdbcBackend._

import scala.concurrent.Await
import scala.concurrent.duration._
import pippin.core._

package object core extends LazyLogging {

  lazy val valarCommitHash: Array[Byte] = thisGitCommitSha1Bytes

  def loadDb(): Database = ValarConfig.instance.load

  def exec[T](action: DBIO[T], waitSeconds: Int = 120)(implicit db: Database): T = Await.result(db run action, waitSeconds.seconds)

  def execInsert(action: DBIO[Int], waitSeconds: Int = 120)(implicit db: Database): Unit = {
    val nRowsAffected = Await.result(db run action, waitSeconds.seconds)
    if (nRowsAffected != 1) throw new IllegalStateException(s"$nRowsAffected rows were inserted")
  }

  trait ValarException extends Exception
  class ValarInconsistencyException(message: String = null, cause: Throwable = null) extends Exception(message, cause) with ValarException

}
