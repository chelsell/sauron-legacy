import com.typesafe.config.{ConfigException, ConfigFactory, Config}

lazy val valar = (
  project
  .in(file("."))
  .settings(
    name := "valar",
    organization := "com.github.dmyersturnbull",
    assembly / assemblyJarName := "valar-backend.jar",
    assembly / assemblyOutputPath := "target",
    assembly / mainClass := Some("valar.ValarCli"),
    version := "1.0.0-SNAPSHOT",
    isSnapshot := true,
    scalaVersion := "3.0.0",
    javacOptions ++= Seq(
      "-source", "16",
      "-target", "16",
      "-Xlint:all"
    ),
    scalacOptions ++= Seq(
      "-deprecation",
      "-feature",
      "-explain",
      "-explain-types",
      "-unchecked",
      "-Xmigration",
    ),
    javaOptions += "-Xmx4G",
    semanticdbEnabled := true,
    description := "backend supporting Valar, the all-knowing relational database",
    organizationHomepage := Some(url("https://github.com/dmyersturnbull")),
    homepage := Some(url("https://github.com/dmyersturnbull/valar-backend")),
    developers := List(
      Developer(
        "dmyersturnbull",
        "Douglas Myers-Turnbull",
        "---",
        url("https://github.com/dmyersturnbull")
      )
    ),
    startYear := Some(2016),
    scmInfo := Some(ScmInfo(
      url("https://github.com/dmyersturnbull/valar-backend"),
      "https://github.com/dmyersturnbull/valar-backend.git"
    )),
    libraryDependencies ++= Seq(
      ("com.github.dmyersturnbull" %% "pippin-core" % "0.7.0-SNAPSHOT").cross(CrossVersion.for3Use2_13),
      ("com.github.dmyersturnbull" %% "pippin-logconfig" % "0.7.0-SNAPSHOT").cross(CrossVersion.for3Use2_13),
      ("com.github.dmyersturnbull" %% "pippin-grammars" % "0.7.0-SNAPSHOT").cross(CrossVersion.for3Use2_13),
      ("com.github.dmyersturnbull" %% "pippin-misc" % "0.7.0-SNAPSHOT").cross(CrossVersion.for3Use2_13),
      ("com.moandjiezana.toml" % "toml4j" % "0.7.1"),
      ("com.iheart" %% "ficus" % "1.5.0").cross(CrossVersion.for3Use2_13),
      ("com.typesafe.slick" %% "slick" % "3.3.3").cross(CrossVersion.for3Use2_13),
      ("com.typesafe.slick" %% "slick-hikaricp" % "3.3.3").cross(CrossVersion.for3Use2_13),
      ("com.typesafe.slick" %% "slick-codegen" % "3.3.3").cross(CrossVersion.for3Use2_13),
      ("mysql" % "mysql-connector-java" % "8.0.25"),
      ("org.scalanlp" %% "breeze" % "1.2").cross(CrossVersion.for3Use2_13),
      ("com.sksamuel.scrimage" %% "scrimage-core" % "4.0.19").cross(CrossVersion.for3Use2_13),
      ("org.bytedeco" % "javacv-platform" % "1.4.1"),
      ("org.boofcv" % "core" % "0.34.0"),
      ("com.github.scopt" %% "scopt" % "4.0.1"),
      ("io.argonaut" %% "argonaut" % "6.3.3"),
      ("de.svenkubiak" % "jBCrypt" % "0.4.3"),
      ("com.google.code.findbugs" % "jsr305" % "3.0.1"), // to ignore missing annotations from Guava
      ("com.typesafe" % "config" % "1.4.1"),
      ("com.google.guava" % "guava" % "30.1.1-jre"),
      ("org.slf4j" % "slf4j-api" % "2.0.0-alpha1"),
      ("com.typesafe.scala-logging" %% "scala-logging" % "3.9.2").cross(CrossVersion.for3Use2_13),
      ("org.scalatest" %% "scalatest" % "3.2.9" % "test"),
      ("org.scalactic" %% "scalactic" % "3.2.9" % "test"),
      ("org.scalacheck" %% "scalacheck" % "1.15.4" % "test"),
      ("org.scalatestplus" %% "scalacheck-1-14" % "3.2.2.0" % "test").cross(CrossVersion.for3Use2_13)
    ) map (_.exclude("org.slf4j", "slf4j-log4j12"))
  )
)
