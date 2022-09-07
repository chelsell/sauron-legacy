package valar

import slick.jdbc.JdbcBackend.Database

import valar.ValarCli.run
import valar.core.Tables.Runs
import valar.core.ValarConfig.instance
import valar.core.exec
import valar.features.FeatureProcessor.getFeature
import valar.importer.DirectoryLoader
import valar.importer.{Importer, RegistrySensorProcessor}
import valar.plugins.UserManager
import valar.plugins.SlickModelGenerator
import valar.plugins.MaintenanceTasks

import java.nio.file.{Path, Paths}
import java.util.Locale
import scala.util.{Failure, Success, Try}

object ValarCli {

  def insert(path: Path, features: Seq[String]): Unit = {
    val submission = DirectoryLoader.load(path)
    // step 1: Create run
    val run = Importer.insert(submission)
    // step 2: Insert sensors
    new RegistrySensorProcessor(submission).apply(run)
    // step 3: Insert feature(s)
    features map getFeature forEach (_.apply(run, submission.videoFile))
  }

  def calculate(path: Path, features: Seq[String]): Unit = {
    val submission = DirectoryLoader.load(path)
    features map getFeature forEach (_.apply(run, submission.videoFile))
  }

  def showHelp(): Unit = {
    println("Commands:")
    println("  | show-help")
    println("  | list-users")
    println("  | insert <path> <features...>")
    println("        ex: calculate /var/spool/30f3cca082ae 'cd(10)' 'MI']")
    println("  | calculate <path> <features...>")
    println("        ex: calculate /store/2021/05/12/20210512.152983.Thor 'cd(10)']")
    println("  | add-user <username> <fist-name> <last-name> <password> <write-access>")
    println("        ex: add-user kerri -- Kerri Johnson false")
    println("  | disable-user <username>")
    println("        ex: disable-user kerri")
    println("  | set-password <username> <password>")
    println("        ex: set-password kerri thisismypassword")
    println("  | grant-write-access <username>")
    println("        ex: grant-write-access kerri")
    println("  | deny-write-access <username>")
    println("        ex: deny-write-access kerri")
    println("  | generate-models")
    println("  | reset-assay-hashes")
    println("  | reset-battery-hashes")
  }
  
  def listUsers(): Unit = {
    {
      implicit val db: Database = instance.db
      import valar.core.Tables._
      import valar.core.Tables.profile.api._
      println("Users: " + exec((Users map (_.username)).result) mkString ", ")
    }
  }

  def run(cmd: String, args: Seq[String]): Unit =
    cmd match {
      case "show-help" => showHelp()
      case "list-users" => 
      case "insert" => insert(Paths.get(args(0)), args.tail)
      case "calculate" => insert(Paths.get(args(0)), args.tail)
      case "add-user" => UserManager.addUser(args(0), args(1), args(2), optional(args(3)), bool(args(4)))
      case "disable-user" => UserManager.setPassword(args(0), None)
      case "set-password" => UserManager.setPassword(args(0), args(1))
      case "grant-write-access" => UserManager.setWriteAccess(args(0), true)
      case "deny-write-access" => UserManager.setWriteAccess(args(0), false)
      case "generate-models" => SlickModelGenerator.generate()
      case "reset-assay-hashes" => MaintenanceTasks.setAllAssayHashes()
      case "reset-battery-hashes" => MaintenanceTasks.setAllBatteryHashes()
      case _ => showHelp()
    }

  protected def bool(s: String): Boolean =
    s.toLowerCase(Locale.ENGLISH) match {
      case "0" | "no" => false
      case "1" | "yes" => true
      case _ => s.toBoolean
    }

  protected def optional(s: String): Option[String] =
    if (s.toSet == Set("-")) None else Some(s)

  def main(args: Array[String]): Unit =
    run(args.head, args.tail)
}
