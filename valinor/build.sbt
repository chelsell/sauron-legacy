name := "valinor"

description := "Kokel Lab webserver and home for Valar"

organization := "com.github.kokellab"
	
version := "0.2.2-SNAPSHOT"
	
isSnapshot := true 
scalaVersion := "2.12.2"
	
javacOptions ++= Seq("-source", "1.8", "-target", "1.8", "-Xlint:all")
	
scalacOptions ++= Seq("-unchecked", "-deprecation")
	
testOptions in Test += Tests.Argument("-oF")
	
homepage := Some(url("https://github.com/kokellab/valinor"))
	
developers := List(Developer("dmyersturnbull", "Douglas Myers-Turnbull", "dmyersturnbull@kokellab.com", url("https://github.com/dmyersturnbull")))
	
startYear := Some(2016)
	
scmInfo := Some(ScmInfo(url("https://github.com/kokellab/valinor"), "https://github.com/kokellab/valinor.git"))

routesGenerator := InjectedRoutesGenerator

resolvers ++= Seq("RoundEights" at "http://maven.spikemark.net/roundeights") // for hasher

libraryDependencies += guice
	
libraryDependencies ++= Seq(
	"com.typesafe" % "config" % "1.3.0",
	"com.typesafe.slick" %% "slick" % "3.2.0",
	"com.google.guava" % "guava" % "25.1-jre",
	"com.google.code.findbugs" % "jsr305" % "3.0.1", // to work around compiler warnings about missing anotations from Guava
	"org.slf4j" % "slf4j-api" % "1.8.0-beta2",
	"ch.qos.logback" %  "logback-classic" % "1.3.0-alpha4",
	"com.typesafe.play" % "play-logback_2.12" % "2.6.15",
	"com.typesafe.scala-logging" %% "scala-logging" % "3.9.0",
	"com.typesafe.play" %% "play" % "2.6.13",
	"com.google.inject" % "guice" % "4.0",
	"com.typesafe.play" %% "play-slick" % "3.0.3",
	"de.svenkubiak" % "jBCrypt" % "0.4.1",
	"org.scalatest" %% "scalatest" % "3.0.1" % "test",
	"org.scalactic" %% "scalactic" % "3.0.1" % "test",
	"org.scalacheck" %% "scalacheck" % "1.13.5" % "test",
	"org.scalamock" %% "scalamock-scalatest-support" % "3.5.0" % "test",
	"com.github.kokellab" %% "skale-core" % "0.5.0-SNAPSHOT",
	"com.github.kokellab" %% "skale-grammars" % "0.5.0-SNAPSHOT",
	"com.github.kokellab" %% "valar-core" % "0.6.3-SNAPSHOT",
	"com.github.kokellab" %% "valar-params" % "0.6.3-SNAPSHOT",
	"com.github.kokellab" %% "valar-insertion" % "0.6.3-SNAPSHOT"
) map (_.exclude("org.slf4j", "slf4j-log4j12"))

libraryDependencies += filters

dependencyOverrides += "com.google.guava" % "guava" % "25.1-jre" // some dependency uses 17.0
dependencyOverrides += "org.slf4j" % "slf4j-api" % "1.8.0-beta2" // can't use 1.7.x is incompatible
dependencyOverrides += "ch.qos.logback" %  "logback-classic" % "1.3.0-alpha4"

libraryDependencies := libraryDependencies.value map (_.exclude("org.slf4j", "slf4j-log4j12")) map (_.exclude("org.slf4j", "slf4j-log4j13")) map (_.exclude("org.slf4j", "slf4j-jdk14")) map (_.exclude("org.slf4j", "slf4j-simple")) map (_.exclude("org.slf4j", "slf4j-nop")) map (_.exclude("org.slf4j", "slf4j-jcl")) map (_.exclude("org.slf4j", "slf4j-nlog4j"))

pomExtra :=
	<issueManagement>
		<system>Github</system>
		<url>https://github.com/kokellab/valinor/issues</url>
	</issueManagement>

lazy val root = (project in file(".")).enablePlugins(PlayScala)
