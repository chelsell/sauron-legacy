package valar.core

import java.time.ZoneId
import slick.jdbc.JdbcBackend.Database

import java.io.{File, FileNotFoundException}
import com.typesafe.config.{Config, ConfigFactory}

import java.nio.file.{Path, Paths}


def getConfigPath(): Path = {
  val etcPath = Paths.get("/", "etc", "Valarfile")
  val appPath = Paths.get("conf", "application.conf") // mainly for testing
  sys.env.get("VALAR_CONFIG") match {
    case Some(p) => Paths.get(p)
    case (None, etcPath.exists()) => etcPath
    case _ => throw new FileNotFoundException(s"Provide a config file at $$VALAR_CONFIG or $etcPath")
  }
}


class ValarConfig(val config: Config = ConfigFactory.parseFile(getConfigPath())) {

  val timezone: ZoneId = ZoneId.systemDefault()

  private lazy val db: Database = try {
    Database.forConfig("valar_db", config)
  } catch {
    case e: Throwable =>
      // Guice injection in Valinor throws a confusion error message otherwise
      printerrln("ERROR: ValarConfig.load() failed")
      throw e
  }
  def load = db

}

/**
  * Mutable singleton.
  */
object ValarConfig {

  var instance: ValarConfig = new ValarConfig()

}
