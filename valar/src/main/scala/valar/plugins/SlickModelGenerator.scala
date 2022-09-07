package valar.plugins

import valar.core.ValarConfig

object SlickModelGenerator {

  def generate(): Unit = {
    val config = ValarConfig.instance
    implicit val db = config.load
    val url = config.config.getString("valar_db.url")
    val gen = SourceCodeGenerator.run(
      "slick.jdbc.MySQLProfile",
      "com.mysql.cj.jdbc.Driver",
      url,
      "src/main/scala",
      "valar.core",
      None,
      None,
      true
    )
  }
  
}
