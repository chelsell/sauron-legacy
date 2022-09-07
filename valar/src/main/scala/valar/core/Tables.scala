package valar.core
// AUTO-GENERATED Slick data model
/** Stand-alone Slick data model for immediate use */
object Tables extends {
  val profile = slick.jdbc.MySQLProfile
} with Tables

/** Slick data model trait for extension, choice of backend or usage in the cake pattern. (Make sure to initialize this late.) */
trait Tables {
  val profile: slick.jdbc.JdbcProfile
  import profile.api._
  import slick.model.ForeignKeyAction
  // NOTE: GetResult mappers for plain SQL are only generated for tables where Slick knows how to map the types of all columns.
  import slick.jdbc.{GetResult => GR}

  /** DDL for all tables. Call .create to execute. */
  lazy val schema: profile.SchemaDescription = Array(Annotations.schema, AssayParams.schema, AssayPositions.schema, Assays.schema, AudioFiles.schema, Batches.schema, BatchLabels.schema, Batteries.schema, Compounds.schema, ConfigFiles.schema, ControlTypes.schema, Experiments.schema, Features.schema, GeneticVariants.schema, Locations.schema, LogFiles.schema, MandosExpression.schema, MandosInfo.schema, MandosObjectLinks.schema, MandosObjects.schema, MandosObjectTags.schema, MandosPredicates.schema, MandosRules.schema, MandosRuleTags.schema, Plates.schema, PlateTypes.schema, ProjectTypes.schema, Refs.schema, Rois.schema, Runs.schema, RunTags.schema, SauronConfigs.schema, Saurons.schema, SauronSettings.schema, SensorData.schema, Sensors.schema, Stimuli.schema, StimulusFrames.schema, SubmissionParams.schema, SubmissionRecords.schema, Submissions.schema, Projects.schema, Suppliers.schema, TemplateAssays.schema, TemplatePlates.schema, TemplateStimulusFrames.schema, TemplateTreatments.schema, TemplateWells.schema, Tissues.schema, TransferPlates.schema, Users.schema, VAnnotations.schema, VExperiments.schema, VMandosRules.schema, VRuns.schema, WellFeatures.schema, Wells.schema, WellTreatments.schema).reduceLeft(_ ++ _)
  @deprecated("Use .schema instead of .ddl", "3.0")
  def ddl = schema

  /** Entity class storing rows of table Annotations
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(255,true), Default(None)
   *  @param value Database column value SqlType(VARCHAR), Length(255,true), Default(None)
   *  @param level Database column level SqlType(ENUM), Length(9,false), Default(1:note)
   *  @param runId Database column run_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param submissionId Database column submission_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param wellId Database column well_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param assayId Database column assay_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param annotatorId Database column annotator_id SqlType(SMALLINT UNSIGNED)
   *  @param description Database column description SqlType(MEDIUMTEXT), Length(16777215,true), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class AnnotationsRow(id: Int, name: Option[String] = None, value: Option[String] = None, level: String = "1:note", runId: Option[Int] = None, submissionId: Option[Int] = None, wellId: Option[Int] = None, assayId: Option[Int] = None, annotatorId: Int, description: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching AnnotationsRow objects using plain SQL queries */
  implicit def GetResultAnnotationsRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[String], e3: GR[Option[Int]], e4: GR[java.sql.Timestamp]): GR[AnnotationsRow] = GR{
    prs => import prs._
    AnnotationsRow.tupled((<<[Int], <<?[String], <<?[String], <<[String], <<?[Int], <<?[Int], <<?[Int], <<?[Int], <<[Int], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table annotations. Objects of this class serve as prototypes for rows in queries. */
  class Annotations(_tableTag: Tag) extends profile.api.Table[AnnotationsRow](_tableTag, Some("valar"), "annotations") {
    def * = (id, name, value, level, runId, submissionId, wellId, assayId, annotatorId, description, created) <> (AnnotationsRow.tupled, AnnotationsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), name, value, Rep.Some(level), runId, submissionId, wellId, assayId, Rep.Some(annotatorId), description, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> AnnotationsRow.tupled((_1.get, _2, _3, _4.get, _5, _6, _7, _8, _9.get, _10, _11.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(255,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(255,varying=true), O.Default(None))
    /** Database column value SqlType(VARCHAR), Length(255,true), Default(None) */
    val value: Rep[Option[String]] = column[Option[String]]("value", O.Length(255,varying=true), O.Default(None))
    /** Database column level SqlType(ENUM), Length(9,false), Default(1:note) */
    val level: Rep[String] = column[String]("level", O.Length(9,varying=false), O.Default("1:note"))
    /** Database column run_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val runId: Rep[Option[Int]] = column[Option[Int]]("run_id", O.Default(None))
    /** Database column submission_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val submissionId: Rep[Option[Int]] = column[Option[Int]]("submission_id", O.Default(None))
    /** Database column well_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val wellId: Rep[Option[Int]] = column[Option[Int]]("well_id", O.Default(None))
    /** Database column assay_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val assayId: Rep[Option[Int]] = column[Option[Int]]("assay_id", O.Default(None))
    /** Database column annotator_id SqlType(SMALLINT UNSIGNED) */
    val annotatorId: Rep[Int] = column[Int]("annotator_id")
    /** Database column description SqlType(MEDIUMTEXT), Length(16777215,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(16777215,varying=true), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Assays (database name concern_to_assay) */
    lazy val assaysFk = foreignKey("concern_to_assay", assayId, Assays)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Runs (database name annotation_to_run) */
    lazy val runsFk = foreignKey("annotation_to_run", runId, Runs)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Submissions (database name concern_to_submission) */
    lazy val submissionsFk = foreignKey("concern_to_submission", submissionId, Submissions)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Users (database name concern_to_person) */
    lazy val usersFk = foreignKey("concern_to_person", annotatorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Wells (database name concern_to_well) */
    lazy val wellsFk = foreignKey("concern_to_well", wellId, Wells)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (level) (database name level) */
    val index1 = index("level", level)
    /** Index over (name) (database name name) */
    val index2 = index("name", name)
  }
  /** Collection-like TableQuery object for table Annotations */
  lazy val Annotations = new TableQuery(tag => new Annotations(tag))

  /** Entity class storing rows of table AssayParams
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param assayId Database column assay_id SqlType(SMALLINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(30,true)
   *  @param value Database column value SqlType(DOUBLE) */
  case class AssayParamsRow(id: Int, assayId: Int, name: String, value: Double)
  /** GetResult implicit for fetching AssayParamsRow objects using plain SQL queries */
  implicit def GetResultAssayParamsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Double]): GR[AssayParamsRow] = GR{
    prs => import prs._
    AssayParamsRow.tupled((<<[Int], <<[Int], <<[String], <<[Double]))
  }
  /** Table description of table assay_params. Objects of this class serve as prototypes for rows in queries. */
  class AssayParams(_tableTag: Tag) extends profile.api.Table[AssayParamsRow](_tableTag, Some("valar"), "assay_params") {
    def * = (id, assayId, name, value) <> (AssayParamsRow.tupled, AssayParamsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(assayId), Rep.Some(name), Rep.Some(value)).shaped.<>({r=>import r._; _1.map(_=> AssayParamsRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column assay_id SqlType(SMALLINT UNSIGNED) */
    val assayId: Rep[Int] = column[Int]("assay_id")
    /** Database column name SqlType(VARCHAR), Length(30,true) */
    val name: Rep[String] = column[String]("name", O.Length(30,varying=true))
    /** Database column value SqlType(DOUBLE) */
    val value: Rep[Double] = column[Double]("value")

    /** Foreign key referencing Assays (database name assay_param_to_assay) */
    lazy val assaysFk = foreignKey("assay_param_to_assay", assayId, Assays)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (name,assayId) (database name assay_and_name_unique) */
    val index1 = index("assay_and_name_unique", (name, assayId), unique=true)
  }
  /** Collection-like TableQuery object for table AssayParams */
  lazy val AssayParams = new TableQuery(tag => new AssayParams(tag))

  /** Entity class storing rows of table AssayPositions
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param batteryId Database column battery_id SqlType(SMALLINT UNSIGNED)
   *  @param assayId Database column assay_id SqlType(SMALLINT UNSIGNED)
   *  @param start Database column start SqlType(INT UNSIGNED) */
  case class AssayPositionsRow(id: Int, batteryId: Int, assayId: Int, start: Int)
  /** GetResult implicit for fetching AssayPositionsRow objects using plain SQL queries */
  implicit def GetResultAssayPositionsRow(implicit e0: GR[Int]): GR[AssayPositionsRow] = GR{
    prs => import prs._
    AssayPositionsRow.tupled((<<[Int], <<[Int], <<[Int], <<[Int]))
  }
  /** Table description of table assay_positions. Objects of this class serve as prototypes for rows in queries. */
  class AssayPositions(_tableTag: Tag) extends profile.api.Table[AssayPositionsRow](_tableTag, Some("valar"), "assay_positions") {
    def * = (id, batteryId, assayId, start) <> (AssayPositionsRow.tupled, AssayPositionsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(batteryId), Rep.Some(assayId), Rep.Some(start)).shaped.<>({r=>import r._; _1.map(_=> AssayPositionsRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column battery_id SqlType(SMALLINT UNSIGNED) */
    val batteryId: Rep[Int] = column[Int]("battery_id")
    /** Database column assay_id SqlType(SMALLINT UNSIGNED) */
    val assayId: Rep[Int] = column[Int]("assay_id")
    /** Database column start SqlType(INT UNSIGNED) */
    val start: Rep[Int] = column[Int]("start")

    /** Foreign key referencing Assays (database name assay_in_battery_to_assay) */
    lazy val assaysFk = foreignKey("assay_in_battery_to_assay", assayId, Assays)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Batteries (database name assay_in_battery_to_battery) */
    lazy val batteriesFk = foreignKey("assay_in_battery_to_battery", batteryId, Batteries)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (batteryId,assayId,start) (database name battery_assay_start_unique) */
    val index1 = index("battery_assay_start_unique", (batteryId, assayId, start), unique=true)
    /** Index over (start) (database name start) */
    val index2 = index("start", start)
  }
  /** Collection-like TableQuery object for table AssayPositions */
  lazy val AssayPositions = new TableQuery(tag => new AssayPositions(tag))

  /** Entity class storing rows of table Assays
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(250,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param length Database column length SqlType(INT UNSIGNED)
   *  @param hidden Database column hidden SqlType(BIT), Default(false)
   *  @param templateAssayId Database column template_assay_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param framesSha1 Database column frames_sha1 SqlType(BINARY)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class AssaysRow(id: Int, name: String, description: Option[String] = None, length: Int, hidden: Boolean = false, templateAssayId: Option[Int] = None, framesSha1: java.sql.Blob, created: java.sql.Timestamp)
  /** GetResult implicit for fetching AssaysRow objects using plain SQL queries */
  implicit def GetResultAssaysRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Boolean], e4: GR[Option[Int]], e5: GR[java.sql.Blob], e6: GR[java.sql.Timestamp]): GR[AssaysRow] = GR{
    prs => import prs._
    AssaysRow.tupled((<<[Int], <<[String], <<?[String], <<[Int], <<[Boolean], <<?[Int], <<[java.sql.Blob], <<[java.sql.Timestamp]))
  }
  /** Table description of table assays. Objects of this class serve as prototypes for rows in queries. */
  class Assays(_tableTag: Tag) extends profile.api.Table[AssaysRow](_tableTag, Some("valar"), "assays") {
    def * = (id, name, description, length, hidden, templateAssayId, framesSha1, created) <> (AssaysRow.tupled, AssaysRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(length), Rep.Some(hidden), templateAssayId, Rep.Some(framesSha1), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> AssaysRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6, _7.get, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(250,true) */
    val name: Rep[String] = column[String]("name", O.Length(250,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column length SqlType(INT UNSIGNED) */
    val length: Rep[Int] = column[Int]("length")
    /** Database column hidden SqlType(BIT), Default(false) */
    val hidden: Rep[Boolean] = column[Boolean]("hidden", O.Default(false))
    /** Database column template_assay_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val templateAssayId: Rep[Option[Int]] = column[Option[Int]]("template_assay_id", O.Default(None))
    /** Database column frames_sha1 SqlType(BINARY) */
    val framesSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("frames_sha1")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing TemplateAssays (database name assay_to_template_assay) */
    lazy val templateAssaysFk = foreignKey("assay_to_template_assay", templateAssayId, TemplateAssays)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (framesSha1) (database name hash) */
    val index1 = index("hash", framesSha1)
    /** Index over (name) (database name name) */
    val index2 = index("name", name)
    /** Uniqueness Index over (name,framesSha1) (database name name_frames_sha1_unique) */
    val index3 = index("name_frames_sha1_unique", (name, framesSha1), unique=true)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index4 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Assays */
  lazy val Assays = new TableQuery(tag => new Assays(tag))

  /** Entity class storing rows of table AudioFiles
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param filename Database column filename SqlType(VARCHAR), Length(100,true)
   *  @param notes Database column notes SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param nSeconds Database column n_seconds SqlType(DOUBLE UNSIGNED)
   *  @param data Database column data SqlType(MEDIUMBLOB)
   *  @param sha1 Database column sha1 SqlType(BINARY)
   *  @param creatorId Database column creator_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class AudioFilesRow(id: Int, filename: String, notes: Option[String] = None, nSeconds: Double, data: java.sql.Blob, sha1: java.sql.Blob, creatorId: Option[Int] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching AudioFilesRow objects using plain SQL queries */
  implicit def GetResultAudioFilesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Double], e4: GR[java.sql.Blob], e5: GR[Option[Int]], e6: GR[java.sql.Timestamp]): GR[AudioFilesRow] = GR{
    prs => import prs._
    AudioFilesRow.tupled((<<[Int], <<[String], <<?[String], <<[Double], <<[java.sql.Blob], <<[java.sql.Blob], <<?[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table audio_files. Objects of this class serve as prototypes for rows in queries. */
  class AudioFiles(_tableTag: Tag) extends profile.api.Table[AudioFilesRow](_tableTag, Some("valar"), "audio_files") {
    def * = (id, filename, notes, nSeconds, data, sha1, creatorId, created) <> (AudioFilesRow.tupled, AudioFilesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(filename), notes, Rep.Some(nSeconds), Rep.Some(data), Rep.Some(sha1), creatorId, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> AudioFilesRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6.get, _7, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column filename SqlType(VARCHAR), Length(100,true) */
    val filename: Rep[String] = column[String]("filename", O.Length(100,varying=true))
    /** Database column notes SqlType(VARCHAR), Length(250,true), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Length(250,varying=true), O.Default(None))
    /** Database column n_seconds SqlType(DOUBLE UNSIGNED) */
    val nSeconds: Rep[Double] = column[Double]("n_seconds")
    /** Database column data SqlType(MEDIUMBLOB) */
    val data: Rep[java.sql.Blob] = column[java.sql.Blob]("data")
    /** Database column sha1 SqlType(BINARY) */
    val sha1: Rep[java.sql.Blob] = column[java.sql.Blob]("sha1")
    /** Database column creator_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val creatorId: Rep[Option[Int]] = column[Option[Int]]("creator_id", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Users (database name audio_file_to_user) */
    lazy val usersFk = foreignKey("audio_file_to_user", creatorId, Users)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (filename) (database name filename_unique) */
    val index1 = index("filename_unique", filename, unique=true)
    /** Uniqueness Index over (sha1) (database name sha1_unique) */
    val index2 = index("sha1_unique", sha1, unique=true)
  }
  /** Collection-like TableQuery object for table AudioFiles */
  lazy val AudioFiles = new TableQuery(tag => new AudioFiles(tag))

  /** Entity class storing rows of table Batches
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param lookupHash Database column lookup_hash SqlType(CHAR), Length(14,false)
   *  @param tag Database column tag SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param compoundId Database column compound_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param madeFromId Database column made_from_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param supplierId Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param legacyInternalId Database column legacy_internal_id SqlType(VARCHAR), Length(255,true), Default(None)
   *  @param locationId Database column location_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param boxNumber Database column box_number SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param wellNumber Database column well_number SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param locationNote Database column location_note SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param amount Database column amount SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param concentrationMillimolar Database column concentration_millimolar SqlType(DOUBLE UNSIGNED), Default(None)
   *  @param solventId Database column solvent_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param molecularWeight Database column molecular_weight SqlType(DOUBLE UNSIGNED), Default(None)
   *  @param supplierCatalogNumber Database column supplier_catalog_number SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param personOrdered Database column person_ordered SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param dateOrdered Database column date_ordered SqlType(DATE), Default(None)
   *  @param notes Database column notes SqlType(TEXT), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class BatchesRow(id: Int, lookupHash: String, tag: Option[String] = None, compoundId: Option[Int] = None, madeFromId: Option[Int] = None, supplierId: Option[Int] = None, refId: Option[Int] = None, legacyInternalId: Option[String] = None, locationId: Option[Int] = None, boxNumber: Option[Int] = None, wellNumber: Option[Int] = None, locationNote: Option[String] = None, amount: Option[String] = None, concentrationMillimolar: Option[Double] = None, solventId: Option[Int] = None, molecularWeight: Option[Double] = None, supplierCatalogNumber: Option[String] = None, personOrdered: Option[Int] = None, dateOrdered: Option[java.sql.Date] = None, notes: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching BatchesRow objects using plain SQL queries */
  implicit def GetResultBatchesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[Option[Double]], e5: GR[Option[java.sql.Date]], e6: GR[Boolean], e7: GR[java.sql.Timestamp]): GR[BatchesRow] = GR{
    prs => import prs._
    BatchesRow.tupled((<<[Int], <<[String], <<?[String], <<?[Int], <<?[Int], <<?[Int], <<?[Int], <<?[String], <<?[Int], <<?[Int], <<?[Int], <<?[String], <<?[String], <<?[Double], <<?[Int], <<?[Double], <<?[String], <<?[Int], <<?[java.sql.Date], <<?[String], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table batches. Objects of this class serve as prototypes for rows in queries. */
  class Batches(_tableTag: Tag) extends profile.api.Table[BatchesRow](_tableTag, Some("valar"), "batches") {
    def * = (id, lookupHash, tag, compoundId, madeFromId, supplierId, refId, legacyInternalId, locationId, boxNumber, wellNumber, locationNote, amount, concentrationMillimolar, solventId, molecularWeight, supplierCatalogNumber, personOrdered, dateOrdered, notes, created) <> (BatchesRow.tupled, BatchesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(lookupHash), tag, compoundId, madeFromId, supplierId, refId, legacyInternalId, locationId, boxNumber, wellNumber, locationNote, amount, concentrationMillimolar, solventId, molecularWeight, supplierCatalogNumber, personOrdered, dateOrdered, notes, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> BatchesRow.tupled((_1.get, _2.get, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17, _18, _19, _20, _21.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column lookup_hash SqlType(CHAR), Length(14,false) */
    val lookupHash: Rep[String] = column[String]("lookup_hash", O.Length(14,varying=false))
    /** Database column tag SqlType(VARCHAR), Length(100,true), Default(None) */
    val tag: Rep[Option[String]] = column[Option[String]]("tag", O.Length(100,varying=true), O.Default(None))
    /** Database column compound_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val compoundId: Rep[Option[Int]] = column[Option[Int]]("compound_id", O.Default(None))
    /** Database column made_from_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val madeFromId: Rep[Option[Int]] = column[Option[Int]]("made_from_id", O.Default(None))
    /** Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val supplierId: Rep[Option[Int]] = column[Option[Int]]("supplier_id", O.Default(None))
    /** Database column ref_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val refId: Rep[Option[Int]] = column[Option[Int]]("ref_id", O.Default(None))
    /** Database column legacy_internal_id SqlType(VARCHAR), Length(255,true), Default(None) */
    val legacyInternalId: Rep[Option[String]] = column[Option[String]]("legacy_internal_id", O.Length(255,varying=true), O.Default(None))
    /** Database column location_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val locationId: Rep[Option[Int]] = column[Option[Int]]("location_id", O.Default(None))
    /** Database column box_number SqlType(SMALLINT UNSIGNED), Default(None) */
    val boxNumber: Rep[Option[Int]] = column[Option[Int]]("box_number", O.Default(None))
    /** Database column well_number SqlType(SMALLINT UNSIGNED), Default(None) */
    val wellNumber: Rep[Option[Int]] = column[Option[Int]]("well_number", O.Default(None))
    /** Database column location_note SqlType(VARCHAR), Length(20,true), Default(None) */
    val locationNote: Rep[Option[String]] = column[Option[String]]("location_note", O.Length(20,varying=true), O.Default(None))
    /** Database column amount SqlType(VARCHAR), Length(100,true), Default(None) */
    val amount: Rep[Option[String]] = column[Option[String]]("amount", O.Length(100,varying=true), O.Default(None))
    /** Database column concentration_millimolar SqlType(DOUBLE UNSIGNED), Default(None) */
    val concentrationMillimolar: Rep[Option[Double]] = column[Option[Double]]("concentration_millimolar", O.Default(None))
    /** Database column solvent_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val solventId: Rep[Option[Int]] = column[Option[Int]]("solvent_id", O.Default(None))
    /** Database column molecular_weight SqlType(DOUBLE UNSIGNED), Default(None) */
    val molecularWeight: Rep[Option[Double]] = column[Option[Double]]("molecular_weight", O.Default(None))
    /** Database column supplier_catalog_number SqlType(VARCHAR), Length(20,true), Default(None) */
    val supplierCatalogNumber: Rep[Option[String]] = column[Option[String]]("supplier_catalog_number", O.Length(20,varying=true), O.Default(None))
    /** Database column person_ordered SqlType(SMALLINT UNSIGNED), Default(None) */
    val personOrdered: Rep[Option[Int]] = column[Option[Int]]("person_ordered", O.Default(None))
    /** Database column date_ordered SqlType(DATE), Default(None) */
    val dateOrdered: Rep[Option[java.sql.Date]] = column[Option[java.sql.Date]]("date_ordered", O.Default(None))
    /** Database column notes SqlType(TEXT), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Batches (database name batch_to_batch) */
    lazy val batchesFk = foreignKey("batch_to_batch", madeFromId, Batches)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Compounds (database name ordered_compound_to_solvent) */
    lazy val compoundsFk2 = foreignKey("ordered_compound_to_solvent", solventId, Compounds)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Compounds (database name ordered_compounds_to_compound) */
    lazy val compoundsFk3 = foreignKey("ordered_compounds_to_compound", compoundId, Compounds)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Locations (database name batch_to_location) */
    lazy val locationsFk = foreignKey("batch_to_location", locationId, Locations)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Refs (database name ordered_compound_to_external_source) */
    lazy val refsFk = foreignKey("ordered_compound_to_external_source", refId, Refs)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Suppliers (database name batch_to_supplier) */
    lazy val suppliersFk = foreignKey("batch_to_supplier", supplierId, Suppliers)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name ordered_compound_to_user) */
    lazy val usersFk = foreignKey("ordered_compound_to_user", personOrdered, Users)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (boxNumber) (database name box_number) */
    val index1 = index("box_number", boxNumber)
    /** Uniqueness Index over (boxNumber,wellNumber) (database name box_number_well_number) */
    val index2 = index("box_number_well_number", (boxNumber, wellNumber), unique=true)
    /** Index over (dateOrdered) (database name date_ordered) */
    val index3 = index("date_ordered", dateOrdered)
    /** Index over (legacyInternalId) (database name internal_id) */
    val index4 = index("internal_id", legacyInternalId)
    /** Uniqueness Index over (tag) (database name tag_unique) */
    val index5 = index("tag_unique", tag, unique=true)
    /** Uniqueness Index over (lookupHash) (database name unique_hash) */
    val index6 = index("unique_hash", lookupHash, unique=true)
    /** Index over (wellNumber) (database name well_number) */
    val index7 = index("well_number", wellNumber)
  }
  /** Collection-like TableQuery object for table Batches */
  lazy val Batches = new TableQuery(tag => new Batches(tag))

  /** Entity class storing rows of table BatchLabels
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param batchId Database column batch_id SqlType(MEDIUMINT UNSIGNED)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(250,true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class BatchLabelsRow(id: Int, batchId: Int, refId: Int, name: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching BatchLabelsRow objects using plain SQL queries */
  implicit def GetResultBatchLabelsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[BatchLabelsRow] = GR{
    prs => import prs._
    BatchLabelsRow.tupled((<<[Int], <<[Int], <<[Int], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table batch_labels. Objects of this class serve as prototypes for rows in queries. */
  class BatchLabels(_tableTag: Tag) extends profile.api.Table[BatchLabelsRow](_tableTag, Some("valar"), "batch_labels") {
    def * = (id, batchId, refId, name, created) <> (BatchLabelsRow.tupled, BatchLabelsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(batchId), Rep.Some(refId), Rep.Some(name), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> BatchLabelsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column batch_id SqlType(MEDIUMINT UNSIGNED) */
    val batchId: Rep[Int] = column[Int]("batch_id")
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column name SqlType(VARCHAR), Length(250,true) */
    val name: Rep[String] = column[String]("name", O.Length(250,varying=true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Batches (database name id_to_ordered_compound) */
    lazy val batchesFk = foreignKey("id_to_ordered_compound", batchId, Batches)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name oc_id_to_data_source) */
    lazy val refsFk = foreignKey("oc_id_to_data_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (name) (database name external_id) */
    val index1 = index("external_id", name)
  }
  /** Collection-like TableQuery object for table BatchLabels */
  lazy val BatchLabels = new TableQuery(tag => new BatchLabels(tag))

  /** Entity class storing rows of table Batteries
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param length Database column length SqlType(INT UNSIGNED)
   *  @param authorId Database column author_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param templateId Database column template_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param hidden Database column hidden SqlType(BIT), Default(false)
   *  @param notes Database column notes SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param assaysSha1 Database column assays_sha1 SqlType(BINARY)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class BatteriesRow(id: Int, name: String, description: Option[String] = None, length: Int, authorId: Option[Int] = None, templateId: Option[Int] = None, hidden: Boolean = false, notes: Option[String] = None, assaysSha1: java.sql.Blob, created: java.sql.Timestamp)
  /** GetResult implicit for fetching BatteriesRow objects using plain SQL queries */
  implicit def GetResultBatteriesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[Boolean], e5: GR[java.sql.Blob], e6: GR[java.sql.Timestamp]): GR[BatteriesRow] = GR{
    prs => import prs._
    BatteriesRow.tupled((<<[Int], <<[String], <<?[String], <<[Int], <<?[Int], <<?[Int], <<[Boolean], <<?[String], <<[java.sql.Blob], <<[java.sql.Timestamp]))
  }
  /** Table description of table batteries. Objects of this class serve as prototypes for rows in queries. */
  class Batteries(_tableTag: Tag) extends profile.api.Table[BatteriesRow](_tableTag, Some("valar"), "batteries") {
    def * = (id, name, description, length, authorId, templateId, hidden, notes, assaysSha1, created) <> (BatteriesRow.tupled, BatteriesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(length), authorId, templateId, Rep.Some(hidden), notes, Rep.Some(assaysSha1), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> BatteriesRow.tupled((_1.get, _2.get, _3, _4.get, _5, _6, _7.get, _8, _9.get, _10.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column length SqlType(INT UNSIGNED) */
    val length: Rep[Int] = column[Int]("length")
    /** Database column author_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val authorId: Rep[Option[Int]] = column[Option[Int]]("author_id", O.Default(None))
    /** Database column template_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val templateId: Rep[Option[Int]] = column[Option[Int]]("template_id", O.Default(None))
    /** Database column hidden SqlType(BIT), Default(false) */
    val hidden: Rep[Boolean] = column[Boolean]("hidden", O.Default(false))
    /** Database column notes SqlType(VARCHAR), Length(10000,true), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Length(10000,varying=true), O.Default(None))
    /** Database column assays_sha1 SqlType(BINARY) */
    val assaysSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("assays_sha1")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Users (database name battery_to_user) */
    lazy val usersFk = foreignKey("battery_to_user", authorId, Users)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (assaysSha1) (database name assays_sha1) */
    val index1 = index("assays_sha1", assaysSha1)
    /** Index over (length) (database name length) */
    val index2 = index("length", length)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index3 = index("name_unique", name, unique=true)
    /** Index over (templateId) (database name battery_to_template) */
    val index4 = index("battery_to_template", templateId)
  }
  /** Collection-like TableQuery object for table Batteries */
  lazy val Batteries = new TableQuery(tag => new Batteries(tag))

  /** Entity class storing rows of table CompoundLabels
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param compoundId Database column compound_id SqlType(MEDIUMINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(1000,true)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class CompoundLabelsRow(id: Int, compoundId: Int, name: String, refId: Int, created: java.sql.Timestamp)
  /** GetResult implicit for fetching CompoundLabelsRow objects using plain SQL queries */
  implicit def GetResultCompoundLabelsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[CompoundLabelsRow] = GR{
    prs => import prs._
    CompoundLabelsRow.tupled((<<[Int], <<[Int], <<[String], <<[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table compound_labels. Objects of this class serve as prototypes for rows in queries. */
  class CompoundLabels(_tableTag: Tag) extends profile.api.Table[CompoundLabelsRow](_tableTag, Some("valar"), "compound_labels") {
    def * = (id, compoundId, name, refId, created) <> (CompoundLabelsRow.tupled, CompoundLabelsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(compoundId), Rep.Some(name), Rep.Some(refId), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> CompoundLabelsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column compound_id SqlType(MEDIUMINT UNSIGNED) */
    val compoundId: Rep[Int] = column[Int]("compound_id")
    /** Database column name SqlType(VARCHAR), Length(1000,true) */
    val name: Rep[String] = column[String]("name", O.Length(1000,varying=true))
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Compounds (database name compound_name_to_compound) */
    lazy val compoundsFk = foreignKey("compound_name_to_compound", compoundId, Compounds)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name compound_name_to_external_source) */
    lazy val refsFk = foreignKey("compound_name_to_external_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
  }
  /** Collection-like TableQuery object for table CompoundLabels */
  lazy val CompoundLabels = new TableQuery(tag => new CompoundLabels(tag))

  /** Entity class storing rows of table Compounds
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param inchi Database column inchi SqlType(VARCHAR), Length(2000,true)
   *  @param inchikey Database column inchikey SqlType(CHAR), Length(27,false)
   *  @param inchikeyConnectivity Database column inchikey_connectivity SqlType(CHAR), Length(14,false)
   *  @param chemblId Database column chembl_id SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param chemspiderId Database column chemspider_id SqlType(INT UNSIGNED), Default(None)
   *  @param smiles Database column smiles SqlType(VARCHAR), Length(2000,true), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class CompoundsRow(id: Int, inchi: String, inchikey: String, inchikeyConnectivity: String, chemblId: Option[String] = None, chemspiderId: Option[Int] = None, smiles: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching CompoundsRow objects using plain SQL queries */
  implicit def GetResultCompoundsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[java.sql.Timestamp]): GR[CompoundsRow] = GR{
    prs => import prs._
    CompoundsRow.tupled((<<[Int], <<[String], <<[String], <<[String], <<?[String], <<?[Int], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table compounds. Objects of this class serve as prototypes for rows in queries. */
  class Compounds(_tableTag: Tag) extends profile.api.Table[CompoundsRow](_tableTag, Some("valar"), "compounds") {
    def * = (id, inchi, inchikey, inchikeyConnectivity, chemblId, chemspiderId, smiles, created) <> (CompoundsRow.tupled, CompoundsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(inchi), Rep.Some(inchikey), Rep.Some(inchikeyConnectivity), chemblId, chemspiderId, smiles, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> CompoundsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5, _6, _7, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column inchi SqlType(VARCHAR), Length(2000,true) */
    val inchi: Rep[String] = column[String]("inchi", O.Length(2000,varying=true))
    /** Database column inchikey SqlType(CHAR), Length(27,false) */
    val inchikey: Rep[String] = column[String]("inchikey", O.Length(27,varying=false))
    /** Database column inchikey_connectivity SqlType(CHAR), Length(14,false) */
    val inchikeyConnectivity: Rep[String] = column[String]("inchikey_connectivity", O.Length(14,varying=false))
    /** Database column chembl_id SqlType(VARCHAR), Length(20,true), Default(None) */
    val chemblId: Rep[Option[String]] = column[Option[String]]("chembl_id", O.Length(20,varying=true), O.Default(None))
    /** Database column chemspider_id SqlType(INT UNSIGNED), Default(None) */
    val chemspiderId: Rep[Option[Int]] = column[Option[Int]]("chemspider_id", O.Default(None))
    /** Database column smiles SqlType(VARCHAR), Length(2000,true), Default(None) */
    val smiles: Rep[Option[String]] = column[Option[String]]("smiles", O.Length(2000,varying=true), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Index over (chemblId) (database name chembl_id) */
    val index1 = index("chembl_id", chemblId)
    /** Uniqueness Index over (inchikey) (database name inchikey) */
    val index2 = index("inchikey", inchikey, unique=true)
    /** Index over (inchikeyConnectivity) (database name inchikey_connectivity) */
    val index3 = index("inchikey_connectivity", inchikeyConnectivity)
  }
  /** Collection-like TableQuery object for table Compounds */
  lazy val Compounds = new TableQuery(tag => new Compounds(tag))

  /** Entity class storing rows of table ConfigFiles
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param tomlText Database column toml_text SqlType(MEDIUMTEXT), Length(16777215,true)
   *  @param textSha1 Database column text_sha1 SqlType(BINARY)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class ConfigFilesRow(id: Int, tomlText: String, textSha1: java.sql.Blob, created: java.sql.Timestamp)
  /** GetResult implicit for fetching ConfigFilesRow objects using plain SQL queries */
  implicit def GetResultConfigFilesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Blob], e3: GR[java.sql.Timestamp]): GR[ConfigFilesRow] = GR{
    prs => import prs._
    ConfigFilesRow.tupled((<<[Int], <<[String], <<[java.sql.Blob], <<[java.sql.Timestamp]))
  }
  /** Table description of table config_files. Objects of this class serve as prototypes for rows in queries. */
  class ConfigFiles(_tableTag: Tag) extends profile.api.Table[ConfigFilesRow](_tableTag, Some("valar"), "config_files") {
    def * = (id, tomlText, textSha1, created) <> (ConfigFilesRow.tupled, ConfigFilesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(tomlText), Rep.Some(textSha1), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> ConfigFilesRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column toml_text SqlType(MEDIUMTEXT), Length(16777215,true) */
    val tomlText: Rep[String] = column[String]("toml_text", O.Length(16777215,varying=true))
    /** Database column text_sha1 SqlType(BINARY) */
    val textSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("text_sha1")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Index over (textSha1) (database name text_sha1) */
    val index1 = index("text_sha1", textSha1)
    /** Uniqueness Index over (textSha1) (database name text_sha1_unique) */
    val index2 = index("text_sha1_unique", textSha1, unique=true)
  }
  /** Collection-like TableQuery object for table ConfigFiles */
  lazy val ConfigFiles = new TableQuery(tag => new ConfigFiles(tag))

  /** Entity class storing rows of table ControlTypes
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true)
   *  @param positive Database column positive SqlType(BIT)
   *  @param drugRelated Database column drug_related SqlType(BIT), Default(true)
   *  @param geneticsRelated Database column genetics_related SqlType(BIT) */
  case class ControlTypesRow(id: Byte, name: String, description: String, positive: Boolean, drugRelated: Boolean = true, geneticsRelated: Boolean)
  /** GetResult implicit for fetching ControlTypesRow objects using plain SQL queries */
  implicit def GetResultControlTypesRow(implicit e0: GR[Byte], e1: GR[String], e2: GR[Boolean]): GR[ControlTypesRow] = GR{
    prs => import prs._
    ControlTypesRow.tupled((<<[Byte], <<[String], <<[String], <<[Boolean], <<[Boolean], <<[Boolean]))
  }
  /** Table description of table control_types. Objects of this class serve as prototypes for rows in queries. */
  class ControlTypes(_tableTag: Tag) extends profile.api.Table[ControlTypesRow](_tableTag, Some("valar"), "control_types") {
    def * = (id, name, description, positive, drugRelated, geneticsRelated) <> (ControlTypesRow.tupled, ControlTypesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(description), Rep.Some(positive), Rep.Some(drugRelated), Rep.Some(geneticsRelated)).shaped.<>({r=>import r._; _1.map(_=> ControlTypesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true) */
    val description: Rep[String] = column[String]("description", O.Length(250,varying=true))
    /** Database column positive SqlType(BIT) */
    val positive: Rep[Boolean] = column[Boolean]("positive")
    /** Database column drug_related SqlType(BIT), Default(true) */
    val drugRelated: Rep[Boolean] = column[Boolean]("drug_related", O.Default(true))
    /** Database column genetics_related SqlType(BIT) */
    val geneticsRelated: Rep[Boolean] = column[Boolean]("genetics_related")

    /** Index over (drugRelated) (database name drug_related) */
    val index1 = index("drug_related", drugRelated)
    /** Index over (geneticsRelated) (database name genetics_related) */
    val index2 = index("genetics_related", geneticsRelated)
    /** Index over (name) (database name name) */
    val index3 = index("name", name)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index4 = index("name_unique", name, unique=true)
    /** Index over (positive) (database name positive) */
    val index5 = index("positive", positive)
  }
  /** Collection-like TableQuery object for table ControlTypes */
  lazy val ControlTypes = new TableQuery(tag => new ControlTypes(tag))

  /** Entity class storing rows of table Experiments
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(200,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param creatorId Database column creator_id SqlType(SMALLINT UNSIGNED)
   *  @param projectId Database column project_id SqlType(SMALLINT UNSIGNED)
   *  @param batteryId Database column battery_id SqlType(SMALLINT UNSIGNED)
   *  @param templatePlateId Database column template_plate_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param transferPlateId Database column transfer_plate_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param defaultAcclimationSec Database column default_acclimation_sec SqlType(SMALLINT UNSIGNED)
   *  @param notes Database column notes SqlType(TEXT), Default(None)
   *  @param active Database column active SqlType(BIT), Default(true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class ExperimentsRow(id: Int, name: String, description: Option[String] = None, creatorId: Int, projectId: Int, batteryId: Int, templatePlateId: Option[Int] = None, transferPlateId: Option[Int] = None, defaultAcclimationSec: Int, notes: Option[String] = None, active: Boolean = true, created: java.sql.Timestamp)
  /** GetResult implicit for fetching ExperimentsRow objects using plain SQL queries */
  implicit def GetResultExperimentsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[Boolean], e5: GR[java.sql.Timestamp]): GR[ExperimentsRow] = GR{
    prs => import prs._
    ExperimentsRow.tupled((<<[Int], <<[String], <<?[String], <<[Int], <<[Int], <<[Int], <<?[Int], <<?[Int], <<[Int], <<?[String], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table experiments. Objects of this class serve as prototypes for rows in queries. */
  class Experiments(_tableTag: Tag) extends profile.api.Table[ExperimentsRow](_tableTag, Some("valar"), "experiments") {
    def * = (id, name, description, creatorId, projectId, batteryId, templatePlateId, transferPlateId, defaultAcclimationSec, notes, active, created) <> (ExperimentsRow.tupled, ExperimentsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(creatorId), Rep.Some(projectId), Rep.Some(batteryId), templatePlateId, transferPlateId, Rep.Some(defaultAcclimationSec), notes, Rep.Some(active), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> ExperimentsRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6.get, _7, _8, _9.get, _10, _11.get, _12.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(200,true) */
    val name: Rep[String] = column[String]("name", O.Length(200,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column creator_id SqlType(SMALLINT UNSIGNED) */
    val creatorId: Rep[Int] = column[Int]("creator_id")
    /** Database column project_id SqlType(SMALLINT UNSIGNED) */
    val projectId: Rep[Int] = column[Int]("project_id")
    /** Database column battery_id SqlType(SMALLINT UNSIGNED) */
    val batteryId: Rep[Int] = column[Int]("battery_id")
    /** Database column template_plate_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val templatePlateId: Rep[Option[Int]] = column[Option[Int]]("template_plate_id", O.Default(None))
    /** Database column transfer_plate_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val transferPlateId: Rep[Option[Int]] = column[Option[Int]]("transfer_plate_id", O.Default(None))
    /** Database column default_acclimation_sec SqlType(SMALLINT UNSIGNED) */
    val defaultAcclimationSec: Rep[Int] = column[Int]("default_acclimation_sec")
    /** Database column notes SqlType(TEXT), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Default(None))
    /** Database column active SqlType(BIT), Default(true) */
    val active: Rep[Boolean] = column[Boolean]("active", O.Default(true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Batteries (database name project_to_battery) */
    lazy val batteriesFk = foreignKey("project_to_battery", batteryId, Batteries)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Projects (database name project_to_project) */
    lazy val projectsFk = foreignKey("project_to_project", projectId, Projects)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing TemplatePlates (database name project_to_template_plate) */
    lazy val templatePlatesFk = foreignKey("project_to_template_plate", templatePlateId, TemplatePlates)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing TransferPlates (database name experiment_to_transfer_plate) */
    lazy val transferPlatesFk = foreignKey("experiment_to_transfer_plate", transferPlateId, TransferPlates)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name experiment_to_user) */
    lazy val usersFk = foreignKey("experiment_to_user", creatorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Experiments */
  lazy val Experiments = new TableQuery(tag => new Experiments(tag))

  /** Entity class storing rows of table Features
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true)
   *  @param dimensions Database column dimensions SqlType(VARCHAR), Length(20,true)
   *  @param dataType Database column data_type SqlType(ENUM), Length(15,false), Default(float)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class FeaturesRow(id: Byte, name: String, description: String, dimensions: String, dataType: String = "float", created: java.sql.Timestamp)
  /** GetResult implicit for fetching FeaturesRow objects using plain SQL queries */
  implicit def GetResultFeaturesRow(implicit e0: GR[Byte], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[FeaturesRow] = GR{
    prs => import prs._
    FeaturesRow.tupled((<<[Byte], <<[String], <<[String], <<[String], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table features. Objects of this class serve as prototypes for rows in queries. */
  class Features(_tableTag: Tag) extends profile.api.Table[FeaturesRow](_tableTag, Some("valar"), "features") {
    def * = (id, name, description, dimensions, dataType, created) <> (FeaturesRow.tupled, FeaturesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(description), Rep.Some(dimensions), Rep.Some(dataType), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> FeaturesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true) */
    val description: Rep[String] = column[String]("description", O.Length(250,varying=true))
    /** Database column dimensions SqlType(VARCHAR), Length(20,true) */
    val dimensions: Rep[String] = column[String]("dimensions", O.Length(20,varying=true))
    /** Database column data_type SqlType(ENUM), Length(15,false), Default(float) */
    val dataType: Rep[String] = column[String]("data_type", O.Length(15,varying=false), O.Default("float"))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Features */
  lazy val Features = new TableQuery(tag => new Features(tag))

  /** Entity class storing rows of table GeneticVariants
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(250,true)
   *  @param motherId Database column mother_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param fatherId Database column father_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param lineageType Database column lineage_type SqlType(ENUM), Length(9,false), Default(None)
   *  @param dateCreated Database column date_created SqlType(DATE), Default(None)
   *  @param notes Database column notes SqlType(TEXT), Default(None)
   *  @param creatorId Database column creator_id SqlType(SMALLINT UNSIGNED)
   *  @param fullyAnnotated Database column fully_annotated SqlType(BIT), Default(false)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class GeneticVariantsRow(id: Int, name: String, motherId: Option[Int] = None, fatherId: Option[Int] = None, lineageType: Option[String] = None, dateCreated: Option[java.sql.Date] = None, notes: Option[String] = None, creatorId: Int, fullyAnnotated: Boolean = false, created: java.sql.Timestamp)
  /** GetResult implicit for fetching GeneticVariantsRow objects using plain SQL queries */
  implicit def GetResultGeneticVariantsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Int]], e3: GR[Option[String]], e4: GR[Option[java.sql.Date]], e5: GR[Boolean], e6: GR[java.sql.Timestamp]): GR[GeneticVariantsRow] = GR{
    prs => import prs._
    GeneticVariantsRow.tupled((<<[Int], <<[String], <<?[Int], <<?[Int], <<?[String], <<?[java.sql.Date], <<?[String], <<[Int], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table genetic_variants. Objects of this class serve as prototypes for rows in queries. */
  class GeneticVariants(_tableTag: Tag) extends profile.api.Table[GeneticVariantsRow](_tableTag, Some("valar"), "genetic_variants") {
    def * = (id, name, motherId, fatherId, lineageType, dateCreated, notes, creatorId, fullyAnnotated, created) <> (GeneticVariantsRow.tupled, GeneticVariantsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), motherId, fatherId, lineageType, dateCreated, notes, Rep.Some(creatorId), Rep.Some(fullyAnnotated), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> GeneticVariantsRow.tupled((_1.get, _2.get, _3, _4, _5, _6, _7, _8.get, _9.get, _10.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(250,true) */
    val name: Rep[String] = column[String]("name", O.Length(250,varying=true))
    /** Database column mother_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val motherId: Rep[Option[Int]] = column[Option[Int]]("mother_id", O.Default(None))
    /** Database column father_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val fatherId: Rep[Option[Int]] = column[Option[Int]]("father_id", O.Default(None))
    /** Database column lineage_type SqlType(ENUM), Length(9,false), Default(None) */
    val lineageType: Rep[Option[String]] = column[Option[String]]("lineage_type", O.Length(9,varying=false), O.Default(None))
    /** Database column date_created SqlType(DATE), Default(None) */
    val dateCreated: Rep[Option[java.sql.Date]] = column[Option[java.sql.Date]]("date_created", O.Default(None))
    /** Database column notes SqlType(TEXT), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Default(None))
    /** Database column creator_id SqlType(SMALLINT UNSIGNED) */
    val creatorId: Rep[Int] = column[Int]("creator_id")
    /** Database column fully_annotated SqlType(BIT), Default(false) */
    val fullyAnnotated: Rep[Boolean] = column[Boolean]("fully_annotated", O.Default(false))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing GeneticVariants (database name fish_variant_to_father) */
    lazy val geneticVariantsFk1 = foreignKey("fish_variant_to_father", fatherId, GeneticVariants)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing GeneticVariants (database name fish_variant_to_mother) */
    lazy val geneticVariantsFk2 = foreignKey("fish_variant_to_mother", motherId, GeneticVariants)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name fish_variant_to_user) */
    lazy val usersFk = foreignKey("fish_variant_to_user", creatorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (lineageType) (database name lineage_type) */
    val index1 = index("lineage_type", lineageType)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index2 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table GeneticVariants */
  lazy val GeneticVariants = new TableQuery(tag => new GeneticVariants(tag))

  /** Entity class storing rows of table Locations
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default()
   *  @param purpose Database column purpose SqlType(VARCHAR), Length(250,true), Default()
   *  @param partOf Database column part_of SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param active Database column active SqlType(BIT), Default(true)
   *  @param temporary Database column temporary SqlType(BIT), Default(false)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class LocationsRow(id: Int, name: String, description: String = "", purpose: String = "", partOf: Option[Int] = None, active: Boolean = true, temporary: Boolean = false, created: java.sql.Timestamp)
  /** GetResult implicit for fetching LocationsRow objects using plain SQL queries */
  implicit def GetResultLocationsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Int]], e3: GR[Boolean], e4: GR[java.sql.Timestamp]): GR[LocationsRow] = GR{
    prs => import prs._
    LocationsRow.tupled((<<[Int], <<[String], <<[String], <<[String], <<?[Int], <<[Boolean], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table locations. Objects of this class serve as prototypes for rows in queries. */
  class Locations(_tableTag: Tag) extends profile.api.Table[LocationsRow](_tableTag, Some("valar"), "locations") {
    def * = (id, name, description, purpose, partOf, active, temporary, created) <> (LocationsRow.tupled, LocationsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(description), Rep.Some(purpose), partOf, Rep.Some(active), Rep.Some(temporary), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> LocationsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5, _6.get, _7.get, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default() */
    val description: Rep[String] = column[String]("description", O.Length(250,varying=true), O.Default(""))
    /** Database column purpose SqlType(VARCHAR), Length(250,true), Default() */
    val purpose: Rep[String] = column[String]("purpose", O.Length(250,varying=true), O.Default(""))
    /** Database column part_of SqlType(SMALLINT UNSIGNED), Default(None) */
    val partOf: Rep[Option[Int]] = column[Option[Int]]("part_of", O.Default(None))
    /** Database column active SqlType(BIT), Default(true) */
    val active: Rep[Boolean] = column[Boolean]("active", O.Default(true))
    /** Database column temporary SqlType(BIT), Default(false) */
    val temporary: Rep[Boolean] = column[Boolean]("temporary", O.Default(false))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Locations (database name location_to_location) */
    lazy val locationsFk = foreignKey("location_to_location", partOf, Locations)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.SetNull)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Locations */
  lazy val Locations = new TableQuery(tag => new Locations(tag))

  /** Entity class storing rows of table LogFiles
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param runId Database column run_id SqlType(MEDIUMINT UNSIGNED)
   *  @param text Database column text SqlType(MEDIUMTEXT), Length(16777215,true)
   *  @param textSha1 Database column text_sha1 SqlType(BINARY)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class LogFilesRow(id: Int, runId: Int, text: String, textSha1: java.sql.Blob, created: java.sql.Timestamp)
  /** GetResult implicit for fetching LogFilesRow objects using plain SQL queries */
  implicit def GetResultLogFilesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Blob], e3: GR[java.sql.Timestamp]): GR[LogFilesRow] = GR{
    prs => import prs._
    LogFilesRow.tupled((<<[Int], <<[Int], <<[String], <<[java.sql.Blob], <<[java.sql.Timestamp]))
  }
  /** Table description of table log_files. Objects of this class serve as prototypes for rows in queries. */
  class LogFiles(_tableTag: Tag) extends profile.api.Table[LogFilesRow](_tableTag, Some("valar"), "log_files") {
    def * = (id, runId, text, textSha1, created) <> (LogFilesRow.tupled, LogFilesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(runId), Rep.Some(text), Rep.Some(textSha1), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> LogFilesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column run_id SqlType(MEDIUMINT UNSIGNED) */
    val runId: Rep[Int] = column[Int]("run_id")
    /** Database column text SqlType(MEDIUMTEXT), Length(16777215,true) */
    val text: Rep[String] = column[String]("text", O.Length(16777215,varying=true))
    /** Database column text_sha1 SqlType(BINARY) */
    val textSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("text_sha1")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Runs (database name log_file_to_run) */
    lazy val runsFk = foreignKey("log_file_to_run", runId, Runs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (textSha1) (database name text_sha1) */
    val index1 = index("text_sha1", textSha1)
  }
  /** Collection-like TableQuery object for table LogFiles */
  lazy val LogFiles = new TableQuery(tag => new LogFiles(tag))

  /** Entity class storing rows of table MandosExpression
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param geneId Database column gene_id SqlType(MEDIUMINT UNSIGNED)
   *  @param tissueId Database column tissue_id SqlType(SMALLINT UNSIGNED)
   *  @param developmentalStage Database column developmental_stage SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param level Database column level SqlType(DOUBLE)
   *  @param confidence Database column confidence SqlType(VARCHAR), Length(100,true)
   *  @param externalId Database column external_id SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosExpressionRow(id: Int, geneId: Int, tissueId: Int, developmentalStage: Option[String] = None, level: Double, confidence: String, externalId: Option[String] = None, refId: Int, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosExpressionRow objects using plain SQL queries */
  implicit def GetResultMandosExpressionRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[Double], e3: GR[String], e4: GR[java.sql.Timestamp]): GR[MandosExpressionRow] = GR{
    prs => import prs._
    MandosExpressionRow.tupled((<<[Int], <<[Int], <<[Int], <<?[String], <<[Double], <<[String], <<?[String], <<[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_expression. Objects of this class serve as prototypes for rows in queries. */
  class MandosExpression(_tableTag: Tag) extends profile.api.Table[MandosExpressionRow](_tableTag, Some("valar"), "mandos_expression") {
    def * = (id, geneId, tissueId, developmentalStage, level, confidence, externalId, refId, created) <> (MandosExpressionRow.tupled, MandosExpressionRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(geneId), Rep.Some(tissueId), developmentalStage, Rep.Some(level), Rep.Some(confidence), externalId, Rep.Some(refId), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosExpressionRow.tupled((_1.get, _2.get, _3.get, _4, _5.get, _6.get, _7, _8.get, _9.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column gene_id SqlType(MEDIUMINT UNSIGNED) */
    val geneId: Rep[Int] = column[Int]("gene_id")
    /** Database column tissue_id SqlType(SMALLINT UNSIGNED) */
    val tissueId: Rep[Int] = column[Int]("tissue_id")
    /** Database column developmental_stage SqlType(VARCHAR), Length(100,true), Default(None) */
    val developmentalStage: Rep[Option[String]] = column[Option[String]]("developmental_stage", O.Length(100,varying=true), O.Default(None))
    /** Database column level SqlType(DOUBLE) */
    val level: Rep[Double] = column[Double]("level")
    /** Database column confidence SqlType(VARCHAR), Length(100,true) */
    val confidence: Rep[String] = column[String]("confidence", O.Length(100,varying=true))
    /** Database column external_id SqlType(VARCHAR), Length(100,true), Default(None) */
    val externalId: Rep[Option[String]] = column[Option[String]]("external_id", O.Length(100,varying=true), O.Default(None))
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Genes (database name expression_to_gene) */
    lazy val genesFk = foreignKey("expression_to_gene", geneId, Genes)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name expression_to_ref) */
    lazy val refsFk = foreignKey("expression_to_ref", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Tissues (database name expression_to_tissue) */
    lazy val tissuesFk = foreignKey("expression_to_tissue", tissueId, Tissues)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (confidence) (database name confidence) */
    val index1 = index("confidence", confidence)
    /** Uniqueness Index over (externalId,refId) (database name external_id_ref_unique) */
    val index2 = index("external_id_ref_unique", (externalId, refId), unique=true)
    /** Uniqueness Index over (geneId,tissueId,developmentalStage,refId) (database name gene_tissue_stage_ref_unique) */
    val index3 = index("gene_tissue_stage_ref_unique", (geneId, tissueId, developmentalStage, refId), unique=true)
  }
  /** Collection-like TableQuery object for table MandosExpression */
  lazy val MandosExpression = new TableQuery(tag => new MandosExpression(tag))

  /** Entity class storing rows of table MandosInfo
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param compoundId Database column compound_id SqlType(MEDIUMINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param value Database column value SqlType(VARCHAR), Length(1000,true)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosInfoRow(id: Int, compoundId: Int, name: String, value: String, refId: Int, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosInfoRow objects using plain SQL queries */
  implicit def GetResultMandosInfoRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[MandosInfoRow] = GR{
    prs => import prs._
    MandosInfoRow.tupled((<<[Int], <<[Int], <<[String], <<[String], <<[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_info. Objects of this class serve as prototypes for rows in queries. */
  class MandosInfo(_tableTag: Tag) extends profile.api.Table[MandosInfoRow](_tableTag, Some("valar"), "mandos_info") {
    def * = (id, compoundId, name, value, refId, created) <> (MandosInfoRow.tupled, MandosInfoRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(compoundId), Rep.Some(name), Rep.Some(value), Rep.Some(refId), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosInfoRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column compound_id SqlType(MEDIUMINT UNSIGNED) */
    val compoundId: Rep[Int] = column[Int]("compound_id")
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column value SqlType(VARCHAR), Length(1000,true) */
    val value: Rep[String] = column[String]("value", O.Length(1000,varying=true))
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Compounds (database name mandos_info_to_compound) */
    lazy val compoundsFk = foreignKey("mandos_info_to_compound", compoundId, Compounds)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name mandos_chem_info_to_data_source) */
    lazy val refsFk = foreignKey("mandos_chem_info_to_data_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (name,refId,compoundId) (database name mandos_chem_info_name_source_compound_unique) */
    val index1 = index("mandos_chem_info_name_source_compound_unique", (name, refId, compoundId), unique=true)
    /** Index over (name) (database name name) */
    val index2 = index("name", name)
    /** Index over (value) (database name value) */
    val index3 = index("value", value)
  }
  /** Collection-like TableQuery object for table MandosInfo */
  lazy val MandosInfo = new TableQuery(tag => new MandosInfo(tag))

  /** Entity class storing rows of table MandosObjectLinks
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param parentId Database column parent_id SqlType(MEDIUMINT UNSIGNED)
   *  @param childId Database column child_id SqlType(MEDIUMINT UNSIGNED)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED) */
  case class MandosObjectLinksRow(id: Int, parentId: Int, childId: Int, refId: Int)
  /** GetResult implicit for fetching MandosObjectLinksRow objects using plain SQL queries */
  implicit def GetResultMandosObjectLinksRow(implicit e0: GR[Int]): GR[MandosObjectLinksRow] = GR{
    prs => import prs._
    MandosObjectLinksRow.tupled((<<[Int], <<[Int], <<[Int], <<[Int]))
  }
  /** Table description of table mandos_object_links. Objects of this class serve as prototypes for rows in queries. */
  class MandosObjectLinks(_tableTag: Tag) extends profile.api.Table[MandosObjectLinksRow](_tableTag, Some("valar"), "mandos_object_links") {
    def * = (id, parentId, childId, refId) <> (MandosObjectLinksRow.tupled, MandosObjectLinksRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(parentId), Rep.Some(childId), Rep.Some(refId)).shaped.<>({r=>import r._; _1.map(_=> MandosObjectLinksRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column parent_id SqlType(MEDIUMINT UNSIGNED) */
    val parentId: Rep[Int] = column[Int]("parent_id")
    /** Database column child_id SqlType(MEDIUMINT UNSIGNED) */
    val childId: Rep[Int] = column[Int]("child_id")
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")

    /** Foreign key referencing MandosObjects (database name mandos_object_links_ibfk_1) */
    lazy val mandosObjectsFk1 = foreignKey("mandos_object_links_ibfk_1", childId, MandosObjects)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing MandosObjects (database name mandos_object_links_ibfk_2) */
    lazy val mandosObjectsFk2 = foreignKey("mandos_object_links_ibfk_2", parentId, MandosObjects)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name mandos_object_links_ibfk_3) */
    lazy val refsFk = foreignKey("mandos_object_links_ibfk_3", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
  }
  /** Collection-like TableQuery object for table MandosObjectLinks */
  lazy val MandosObjectLinks = new TableQuery(tag => new MandosObjectLinks(tag))

  /** Entity class storing rows of table MandosObjects
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param externalId Database column external_id SqlType(VARCHAR), Length(250,true)
   *  @param name Database column name SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosObjectsRow(id: Int, refId: Int, externalId: String, name: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosObjectsRow objects using plain SQL queries */
  implicit def GetResultMandosObjectsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[java.sql.Timestamp]): GR[MandosObjectsRow] = GR{
    prs => import prs._
    MandosObjectsRow.tupled((<<[Int], <<[Int], <<[String], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_objects. Objects of this class serve as prototypes for rows in queries. */
  class MandosObjects(_tableTag: Tag) extends profile.api.Table[MandosObjectsRow](_tableTag, Some("valar"), "mandos_objects") {
    def * = (id, refId, externalId, name, created) <> (MandosObjectsRow.tupled, MandosObjectsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(refId), Rep.Some(externalId), name, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosObjectsRow.tupled((_1.get, _2.get, _3.get, _4, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column external_id SqlType(VARCHAR), Length(250,true) */
    val externalId: Rep[String] = column[String]("external_id", O.Length(250,varying=true))
    /** Database column name SqlType(VARCHAR), Length(250,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(250,varying=true), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Refs (database name mandos_key_to_data_source) */
    lazy val refsFk = foreignKey("mandos_key_to_data_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (refId,externalId) (database name data_source_external_id_unique) */
    val index1 = index("data_source_external_id_unique", (refId, externalId), unique=true)
    /** Index over (externalId) (database name external_id) */
    val index2 = index("external_id", externalId)
  }
  /** Collection-like TableQuery object for table MandosObjects */
  lazy val MandosObjects = new TableQuery(tag => new MandosObjects(tag))

  /** Entity class storing rows of table MandosObjectTags
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param `object` Database column object SqlType(MEDIUMINT UNSIGNED)
   *  @param ref Database column ref SqlType(SMALLINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(150,true)
   *  @param value Database column value SqlType(VARCHAR), Length(250,true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosObjectTagsRow(id: Int, `object`: Int, ref: Int, name: String, value: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosObjectTagsRow objects using plain SQL queries */
  implicit def GetResultMandosObjectTagsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[MandosObjectTagsRow] = GR{
    prs => import prs._
    MandosObjectTagsRow.tupled((<<[Int], <<[Int], <<[Int], <<[String], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_object_tags. Objects of this class serve as prototypes for rows in queries.
   *  NOTE: The following names collided with Scala keywords and were escaped: object */
  class MandosObjectTags(_tableTag: Tag) extends profile.api.Table[MandosObjectTagsRow](_tableTag, Some("valar"), "mandos_object_tags") {
    def * = (id, `object`, ref, name, value, created) <> (MandosObjectTagsRow.tupled, MandosObjectTagsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(`object`), Rep.Some(ref), Rep.Some(name), Rep.Some(value), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosObjectTagsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column object SqlType(MEDIUMINT UNSIGNED)
     *  NOTE: The name was escaped because it collided with a Scala keyword. */
    val `object`: Rep[Int] = column[Int]("object")
    /** Database column ref SqlType(SMALLINT UNSIGNED) */
    val ref: Rep[Int] = column[Int]("ref")
    /** Database column name SqlType(VARCHAR), Length(150,true) */
    val name: Rep[String] = column[String]("name", O.Length(150,varying=true))
    /** Database column value SqlType(VARCHAR), Length(250,true) */
    val value: Rep[String] = column[String]("value", O.Length(250,varying=true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing MandosObjects (database name mandos_object_tag_to_object) */
    lazy val mandosObjectsFk = foreignKey("mandos_object_tag_to_object", `object`, MandosObjects)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name mandos_object_tag_to_ref) */
    lazy val refsFk = foreignKey("mandos_object_tag_to_ref", ref, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (value) (database name label) */
    val index1 = index("label", value)
    /** Uniqueness Index over (`object`,ref,name,value) (database name object_ref_name_value_unique) */
    val index2 = index("object_ref_name_value_unique", (`object`, ref, name, value), unique=true)
  }
  /** Collection-like TableQuery object for table MandosObjectTags */
  lazy val MandosObjectTags = new TableQuery(tag => new MandosObjectTags(tag))

  /** Entity class storing rows of table MandosPredicates
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param externalId Database column external_id SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param name Database column name SqlType(VARCHAR), Length(250,true)
   *  @param kind Database column kind SqlType(ENUM), Length(10,false)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosPredicatesRow(id: Byte, refId: Int, externalId: Option[String] = None, name: String, kind: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosPredicatesRow objects using plain SQL queries */
  implicit def GetResultMandosPredicatesRow(implicit e0: GR[Byte], e1: GR[Int], e2: GR[Option[String]], e3: GR[String], e4: GR[java.sql.Timestamp]): GR[MandosPredicatesRow] = GR{
    prs => import prs._
    MandosPredicatesRow.tupled((<<[Byte], <<[Int], <<?[String], <<[String], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_predicates. Objects of this class serve as prototypes for rows in queries. */
  class MandosPredicates(_tableTag: Tag) extends profile.api.Table[MandosPredicatesRow](_tableTag, Some("valar"), "mandos_predicates") {
    def * = (id, refId, externalId, name, kind, created) <> (MandosPredicatesRow.tupled, MandosPredicatesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(refId), externalId, Rep.Some(name), Rep.Some(kind), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosPredicatesRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column external_id SqlType(VARCHAR), Length(250,true), Default(None) */
    val externalId: Rep[Option[String]] = column[Option[String]]("external_id", O.Length(250,varying=true), O.Default(None))
    /** Database column name SqlType(VARCHAR), Length(250,true) */
    val name: Rep[String] = column[String]("name", O.Length(250,varying=true))
    /** Database column kind SqlType(ENUM), Length(10,false) */
    val kind: Rep[String] = column[String]("kind", O.Length(10,varying=false))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Refs (database name mandos_mode_to_source) */
    lazy val refsFk = foreignKey("mandos_mode_to_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (externalId) (database name external_id) */
    val index1 = index("external_id", externalId)
    /** Uniqueness Index over (externalId,refId) (database name external_id_source_unique) */
    val index2 = index("external_id_source_unique", (externalId, refId), unique=true)
    /** Index over (name) (database name name) */
    val index3 = index("name", name)
    /** Uniqueness Index over (name,refId) (database name name_source_unique) */
    val index4 = index("name_source_unique", (name, refId), unique=true)
  }
  /** Collection-like TableQuery object for table MandosPredicates */
  lazy val MandosPredicates = new TableQuery(tag => new MandosPredicates(tag))

  /** Entity class storing rows of table MandosRules
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param compoundId Database column compound_id SqlType(MEDIUMINT UNSIGNED)
   *  @param objectId Database column object_id SqlType(MEDIUMINT UNSIGNED)
   *  @param externalId Database column external_id SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param predicateId Database column predicate_id SqlType(TINYINT UNSIGNED)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosRulesRow(id: Int, refId: Int, compoundId: Int, objectId: Int, externalId: Option[String] = None, predicateId: Byte, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosRulesRow objects using plain SQL queries */
  implicit def GetResultMandosRulesRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[Byte], e3: GR[java.sql.Timestamp]): GR[MandosRulesRow] = GR{
    prs => import prs._
    MandosRulesRow.tupled((<<[Int], <<[Int], <<[Int], <<[Int], <<?[String], <<[Byte], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_rules. Objects of this class serve as prototypes for rows in queries. */
  class MandosRules(_tableTag: Tag) extends profile.api.Table[MandosRulesRow](_tableTag, Some("valar"), "mandos_rules") {
    def * = (id, refId, compoundId, objectId, externalId, predicateId, created) <> (MandosRulesRow.tupled, MandosRulesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(refId), Rep.Some(compoundId), Rep.Some(objectId), externalId, Rep.Some(predicateId), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosRulesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5, _6.get, _7.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column compound_id SqlType(MEDIUMINT UNSIGNED) */
    val compoundId: Rep[Int] = column[Int]("compound_id")
    /** Database column object_id SqlType(MEDIUMINT UNSIGNED) */
    val objectId: Rep[Int] = column[Int]("object_id")
    /** Database column external_id SqlType(VARCHAR), Length(250,true), Default(None) */
    val externalId: Rep[Option[String]] = column[Option[String]]("external_id", O.Length(250,varying=true), O.Default(None))
    /** Database column predicate_id SqlType(TINYINT UNSIGNED) */
    val predicateId: Rep[Byte] = column[Byte]("predicate_id")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Compounds (database name mandos_association_to_compound) */
    lazy val compoundsFk = foreignKey("mandos_association_to_compound", compoundId, Compounds)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing MandosObjects (database name mandos_association_to_key) */
    lazy val mandosObjectsFk = foreignKey("mandos_association_to_key", objectId, MandosObjects)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing MandosPredicates (database name mandos_association_to_mode) */
    lazy val mandosPredicatesFk = foreignKey("mandos_association_to_mode", predicateId, MandosPredicates)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name mandos_association_to_data_source) */
    lazy val refsFk = foreignKey("mandos_association_to_data_source", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (refId,compoundId,objectId,predicateId) (database name data_source_compound_mode_unique) */
    val index1 = index("data_source_compound_mode_unique", (refId, compoundId, objectId, predicateId), unique=true)
    /** Index over (externalId) (database name external_id) */
    val index2 = index("external_id", externalId)
  }
  /** Collection-like TableQuery object for table MandosRules */
  lazy val MandosRules = new TableQuery(tag => new MandosRules(tag))

  /** Entity class storing rows of table MandosRuleTags
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param rule Database column rule SqlType(INT UNSIGNED)
   *  @param ref Database column ref SqlType(SMALLINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(150,true)
   *  @param value Database column value SqlType(VARCHAR), Length(250,true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class MandosRuleTagsRow(id: Int, rule: Int, ref: Int, name: String, value: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching MandosRuleTagsRow objects using plain SQL queries */
  implicit def GetResultMandosRuleTagsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[MandosRuleTagsRow] = GR{
    prs => import prs._
    MandosRuleTagsRow.tupled((<<[Int], <<[Int], <<[Int], <<[String], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table mandos_rule_tags. Objects of this class serve as prototypes for rows in queries. */
  class MandosRuleTags(_tableTag: Tag) extends profile.api.Table[MandosRuleTagsRow](_tableTag, Some("valar"), "mandos_rule_tags") {
    def * = (id, rule, ref, name, value, created) <> (MandosRuleTagsRow.tupled, MandosRuleTagsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(rule), Rep.Some(ref), Rep.Some(name), Rep.Some(value), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> MandosRuleTagsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column rule SqlType(INT UNSIGNED) */
    val rule: Rep[Int] = column[Int]("rule")
    /** Database column ref SqlType(SMALLINT UNSIGNED) */
    val ref: Rep[Int] = column[Int]("ref")
    /** Database column name SqlType(VARCHAR), Length(150,true) */
    val name: Rep[String] = column[String]("name", O.Length(150,varying=true))
    /** Database column value SqlType(VARCHAR), Length(250,true) */
    val value: Rep[String] = column[String]("value", O.Length(250,varying=true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing MandosRules (database name mandos_rule_tag_to_object) */
    lazy val mandosRulesFk = foreignKey("mandos_rule_tag_to_object", rule, MandosRules)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Refs (database name mandos_rule_tag_to_ref) */
    lazy val refsFk = foreignKey("mandos_rule_tag_to_ref", ref, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (value) (database name label) */
    val index1 = index("label", value)
    /** Uniqueness Index over (rule,ref,name,value) (database name rule_ref_name_value_unique) */
    val index2 = index("rule_ref_name_value_unique", (rule, ref, name, value), unique=true)
  }
  /** Collection-like TableQuery object for table MandosRuleTags */
  lazy val MandosRuleTags = new TableQuery(tag => new MandosRuleTags(tag))

  /** Entity class storing rows of table Plates
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param plateTypeId Database column plate_type_id SqlType(TINYINT UNSIGNED), Default(None)
   *  @param personPlatedId Database column person_plated_id SqlType(SMALLINT UNSIGNED)
   *  @param datetimePlated Database column datetime_plated SqlType(DATETIME), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class PlatesRow(id: Int, plateTypeId: Option[Byte] = None, personPlatedId: Int, datetimePlated: Option[java.sql.Timestamp] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching PlatesRow objects using plain SQL queries */
  implicit def GetResultPlatesRow(implicit e0: GR[Int], e1: GR[Option[Byte]], e2: GR[Option[java.sql.Timestamp]], e3: GR[java.sql.Timestamp]): GR[PlatesRow] = GR{
    prs => import prs._
    PlatesRow.tupled((<<[Int], <<?[Byte], <<[Int], <<?[java.sql.Timestamp], <<[java.sql.Timestamp]))
  }
  /** Table description of table plates. Objects of this class serve as prototypes for rows in queries. */
  class Plates(_tableTag: Tag) extends profile.api.Table[PlatesRow](_tableTag, Some("valar"), "plates") {
    def * = (id, plateTypeId, personPlatedId, datetimePlated, created) <> (PlatesRow.tupled, PlatesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), plateTypeId, Rep.Some(personPlatedId), datetimePlated, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> PlatesRow.tupled((_1.get, _2, _3.get, _4, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column plate_type_id SqlType(TINYINT UNSIGNED), Default(None) */
    val plateTypeId: Rep[Option[Byte]] = column[Option[Byte]]("plate_type_id", O.Default(None))
    /** Database column person_plated_id SqlType(SMALLINT UNSIGNED) */
    val personPlatedId: Rep[Int] = column[Int]("person_plated_id")
    /** Database column datetime_plated SqlType(DATETIME), Default(None) */
    val datetimePlated: Rep[Option[java.sql.Timestamp]] = column[Option[java.sql.Timestamp]]("datetime_plated", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing PlateTypes (database name plate_to_plate_type) */
    lazy val plateTypesFk = foreignKey("plate_to_plate_type", plateTypeId, PlateTypes)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name plate_to_user) */
    lazy val usersFk = foreignKey("plate_to_user", personPlatedId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (datetimePlated) (database name datetime_fish_plated) */
    val index1 = index("datetime_fish_plated", datetimePlated)
  }
  /** Collection-like TableQuery object for table Plates */
  lazy val Plates = new TableQuery(tag => new Plates(tag))

  /** Entity class storing rows of table PlateTypes
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param supplierId Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param partNumber Database column part_number SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param nRows Database column n_rows SqlType(SMALLINT UNSIGNED)
   *  @param nColumns Database column n_columns SqlType(SMALLINT UNSIGNED)
   *  @param wellShape Database column well_shape SqlType(ENUM), Length(11,false)
   *  @param opacity Database column opacity SqlType(ENUM), Length(11,false) */
  case class PlateTypesRow(id: Byte, name: Option[String] = None, supplierId: Option[Int] = None, partNumber: Option[String] = None, nRows: Int, nColumns: Int, wellShape: String, opacity: String)
  /** GetResult implicit for fetching PlateTypesRow objects using plain SQL queries */
  implicit def GetResultPlateTypesRow(implicit e0: GR[Byte], e1: GR[Option[String]], e2: GR[Option[Int]], e3: GR[Int], e4: GR[String]): GR[PlateTypesRow] = GR{
    prs => import prs._
    PlateTypesRow.tupled((<<[Byte], <<?[String], <<?[Int], <<?[String], <<[Int], <<[Int], <<[String], <<[String]))
  }
  /** Table description of table plate_types. Objects of this class serve as prototypes for rows in queries. */
  class PlateTypes(_tableTag: Tag) extends profile.api.Table[PlateTypesRow](_tableTag, Some("valar"), "plate_types") {
    def * = (id, name, supplierId, partNumber, nRows, nColumns, wellShape, opacity) <> (PlateTypesRow.tupled, PlateTypesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), name, supplierId, partNumber, Rep.Some(nRows), Rep.Some(nColumns), Rep.Some(wellShape), Rep.Some(opacity)).shaped.<>({r=>import r._; _1.map(_=> PlateTypesRow.tupled((_1.get, _2, _3, _4, _5.get, _6.get, _7.get, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(100,varying=true), O.Default(None))
    /** Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val supplierId: Rep[Option[Int]] = column[Option[Int]]("supplier_id", O.Default(None))
    /** Database column part_number SqlType(VARCHAR), Length(100,true), Default(None) */
    val partNumber: Rep[Option[String]] = column[Option[String]]("part_number", O.Length(100,varying=true), O.Default(None))
    /** Database column n_rows SqlType(SMALLINT UNSIGNED) */
    val nRows: Rep[Int] = column[Int]("n_rows")
    /** Database column n_columns SqlType(SMALLINT UNSIGNED) */
    val nColumns: Rep[Int] = column[Int]("n_columns")
    /** Database column well_shape SqlType(ENUM), Length(11,false) */
    val wellShape: Rep[String] = column[String]("well_shape", O.Length(11,varying=false))
    /** Database column opacity SqlType(ENUM), Length(11,false) */
    val opacity: Rep[String] = column[String]("opacity", O.Length(11,varying=false))

    /** Foreign key referencing Suppliers (database name plate_type_to_supplier) */
    lazy val suppliersFk = foreignKey("plate_type_to_supplier", supplierId, Suppliers)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (partNumber) (database name manufacturer) */
    val index1 = index("manufacturer", partNumber)
    /** Index over (nRows,nColumns) (database name n_rows) */
    val index2 = index("n_rows", (nRows, nColumns))
  }
  /** Collection-like TableQuery object for table PlateTypes */
  lazy val PlateTypes = new TableQuery(tag => new PlateTypes(tag))

  /** Entity class storing rows of table ProjectTypes
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param description Database column description SqlType(TEXT) */
  case class ProjectTypesRow(id: Byte, name: String, description: String)
  /** GetResult implicit for fetching ProjectTypesRow objects using plain SQL queries */
  implicit def GetResultProjectTypesRow(implicit e0: GR[Byte], e1: GR[String]): GR[ProjectTypesRow] = GR{
    prs => import prs._
    ProjectTypesRow.tupled((<<[Byte], <<[String], <<[String]))
  }
  /** Table description of table project_types. Objects of this class serve as prototypes for rows in queries. */
  class ProjectTypes(_tableTag: Tag) extends profile.api.Table[ProjectTypesRow](_tableTag, Some("valar"), "project_types") {
    def * = (id, name, description) <> (ProjectTypesRow.tupled, ProjectTypesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(description)).shaped.<>({r=>import r._; _1.map(_=> ProjectTypesRow.tupled((_1.get, _2.get, _3.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column description SqlType(TEXT) */
    val description: Rep[String] = column[String]("description")

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table ProjectTypes */
  lazy val ProjectTypes = new TableQuery(tag => new ProjectTypes(tag))

  /** Entity class storing rows of table Refs
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param datetimeDownloaded Database column datetime_downloaded SqlType(DATETIME), Default(None)
   *  @param externalVersion Database column external_version SqlType(VARCHAR), Length(50,true), Default(None)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param url Database column url SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class RefsRow(id: Int, name: String, datetimeDownloaded: Option[java.sql.Timestamp] = None, externalVersion: Option[String] = None, description: Option[String] = None, url: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching RefsRow objects using plain SQL queries */
  implicit def GetResultRefsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[java.sql.Timestamp]], e3: GR[Option[String]], e4: GR[java.sql.Timestamp]): GR[RefsRow] = GR{
    prs => import prs._
    RefsRow.tupled((<<[Int], <<[String], <<?[java.sql.Timestamp], <<?[String], <<?[String], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table refs. Objects of this class serve as prototypes for rows in queries. */
  class Refs(_tableTag: Tag) extends profile.api.Table[RefsRow](_tableTag, Some("valar"), "refs") {
    def * = (id, name, datetimeDownloaded, externalVersion, description, url, created) <> (RefsRow.tupled, RefsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), datetimeDownloaded, externalVersion, description, url, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> RefsRow.tupled((_1.get, _2.get, _3, _4, _5, _6, _7.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column datetime_downloaded SqlType(DATETIME), Default(None) */
    val datetimeDownloaded: Rep[Option[java.sql.Timestamp]] = column[Option[java.sql.Timestamp]]("datetime_downloaded", O.Default(None))
    /** Database column external_version SqlType(VARCHAR), Length(50,true), Default(None) */
    val externalVersion: Rep[Option[String]] = column[Option[String]]("external_version", O.Length(50,varying=true), O.Default(None))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(250,varying=true), O.Default(None))
    /** Database column url SqlType(VARCHAR), Length(100,true), Default(None) */
    val url: Rep[Option[String]] = column[Option[String]]("url", O.Length(100,varying=true), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Index over (externalVersion) (database name external_version) */
    val index1 = index("external_version", externalVersion)
    /** Index over (name) (database name name) */
    val index2 = index("name", name)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index3 = index("name_unique", name, unique=true)
    /** Index over (url) (database name url) */
    val index4 = index("url", url)
  }
  /** Collection-like TableQuery object for table Refs */
  lazy val Refs = new TableQuery(tag => new Refs(tag))

  /** Entity class storing rows of table Rois
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param wellId Database column well_id SqlType(MEDIUMINT UNSIGNED)
   *  @param y0 Database column y0 SqlType(SMALLINT)
   *  @param x0 Database column x0 SqlType(SMALLINT)
   *  @param y1 Database column y1 SqlType(SMALLINT)
   *  @param x1 Database column x1 SqlType(SMALLINT)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED) */
  case class RoisRow(id: Int, wellId: Int, y0: Int, x0: Int, y1: Int, x1: Int, refId: Int)
  /** GetResult implicit for fetching RoisRow objects using plain SQL queries */
  implicit def GetResultRoisRow(implicit e0: GR[Int]): GR[RoisRow] = GR{
    prs => import prs._
    RoisRow.tupled((<<[Int], <<[Int], <<[Int], <<[Int], <<[Int], <<[Int], <<[Int]))
  }
  /** Table description of table rois. Objects of this class serve as prototypes for rows in queries. */
  class Rois(_tableTag: Tag) extends profile.api.Table[RoisRow](_tableTag, Some("valar"), "rois") {
    def * = (id, wellId, y0, x0, y1, x1, refId) <> (RoisRow.tupled, RoisRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(wellId), Rep.Some(y0), Rep.Some(x0), Rep.Some(y1), Rep.Some(x1), Rep.Some(refId)).shaped.<>({r=>import r._; _1.map(_=> RoisRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6.get, _7.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column well_id SqlType(MEDIUMINT UNSIGNED) */
    val wellId: Rep[Int] = column[Int]("well_id")
    /** Database column y0 SqlType(SMALLINT) */
    val y0: Rep[Int] = column[Int]("y0")
    /** Database column x0 SqlType(SMALLINT) */
    val x0: Rep[Int] = column[Int]("x0")
    /** Database column y1 SqlType(SMALLINT) */
    val y1: Rep[Int] = column[Int]("y1")
    /** Database column x1 SqlType(SMALLINT) */
    val x1: Rep[Int] = column[Int]("x1")
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")

    /** Foreign key referencing Wells (database name roi_to_well) */
    lazy val wellsFk = foreignKey("roi_to_well", wellId, Wells)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (refId) (database name lorien_config) */
    val index1 = index("lorien_config", refId)
  }
  /** Collection-like TableQuery object for table Rois */
  lazy val Rois = new TableQuery(tag => new Rois(tag))

  /** Entity class storing rows of table Runs
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param experimentId Database column experiment_id SqlType(SMALLINT UNSIGNED)
   *  @param plateId Database column plate_id SqlType(SMALLINT UNSIGNED)
   *  @param description Database column description SqlType(VARCHAR), Length(200,true)
   *  @param experimentalistId Database column experimentalist_id SqlType(SMALLINT UNSIGNED)
   *  @param submissionId Database column submission_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param datetimeRun Database column datetime_run SqlType(DATETIME)
   *  @param datetimeDosed Database column datetime_dosed SqlType(DATETIME), Default(None)
   *  @param name Database column name SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param tag Database column tag SqlType(VARCHAR), Length(100,true), Default()
   *  @param sauronConfigId Database column sauron_config_id SqlType(SMALLINT UNSIGNED)
   *  @param configFileId Database column config_file_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param incubationMin Database column incubation_min SqlType(MEDIUMINT), Default(None)
   *  @param acclimationSec Database column acclimation_sec SqlType(INT UNSIGNED), Default(None)
   *  @param notes Database column notes SqlType(TEXT), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class RunsRow(id: Int, experimentId: Int, plateId: Int, description: String, experimentalistId: Int, submissionId: Option[Int] = None, datetimeRun: java.sql.Timestamp, datetimeDosed: Option[java.sql.Timestamp] = None, name: Option[String] = None, tag: String = "", sauronConfigId: Int, configFileId: Option[Int] = None, incubationMin: Option[Int] = None, acclimationSec: Option[Int] = None, notes: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching RunsRow objects using plain SQL queries */
  implicit def GetResultRunsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Int]], e3: GR[java.sql.Timestamp], e4: GR[Option[java.sql.Timestamp]], e5: GR[Option[String]]): GR[RunsRow] = GR{
    prs => import prs._
    RunsRow.tupled((<<[Int], <<[Int], <<[Int], <<[String], <<[Int], <<?[Int], <<[java.sql.Timestamp], <<?[java.sql.Timestamp], <<?[String], <<[String], <<[Int], <<?[Int], <<?[Int], <<?[Int], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table runs. Objects of this class serve as prototypes for rows in queries. */
  class Runs(_tableTag: Tag) extends profile.api.Table[RunsRow](_tableTag, Some("valar"), "runs") {
    def * = (id, experimentId, plateId, description, experimentalistId, submissionId, datetimeRun, datetimeDosed, name, tag, sauronConfigId, configFileId, incubationMin, acclimationSec, notes, created) <> (RunsRow.tupled, RunsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(experimentId), Rep.Some(plateId), Rep.Some(description), Rep.Some(experimentalistId), submissionId, Rep.Some(datetimeRun), datetimeDosed, name, Rep.Some(tag), Rep.Some(sauronConfigId), configFileId, incubationMin, acclimationSec, notes, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> RunsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6, _7.get, _8, _9, _10.get, _11.get, _12, _13, _14, _15, _16.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column experiment_id SqlType(SMALLINT UNSIGNED) */
    val experimentId: Rep[Int] = column[Int]("experiment_id")
    /** Database column plate_id SqlType(SMALLINT UNSIGNED) */
    val plateId: Rep[Int] = column[Int]("plate_id")
    /** Database column description SqlType(VARCHAR), Length(200,true) */
    val description: Rep[String] = column[String]("description", O.Length(200,varying=true))
    /** Database column experimentalist_id SqlType(SMALLINT UNSIGNED) */
    val experimentalistId: Rep[Int] = column[Int]("experimentalist_id")
    /** Database column submission_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val submissionId: Rep[Option[Int]] = column[Option[Int]]("submission_id", O.Default(None))
    /** Database column datetime_run SqlType(DATETIME) */
    val datetimeRun: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("datetime_run")
    /** Database column datetime_dosed SqlType(DATETIME), Default(None) */
    val datetimeDosed: Rep[Option[java.sql.Timestamp]] = column[Option[java.sql.Timestamp]]("datetime_dosed", O.Default(None))
    /** Database column name SqlType(VARCHAR), Length(100,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(100,varying=true), O.Default(None))
    /** Database column tag SqlType(VARCHAR), Length(100,true), Default() */
    val tag: Rep[String] = column[String]("tag", O.Length(100,varying=true), O.Default(""))
    /** Database column sauron_config_id SqlType(SMALLINT UNSIGNED) */
    val sauronConfigId: Rep[Int] = column[Int]("sauron_config_id")
    /** Database column config_file_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val configFileId: Rep[Option[Int]] = column[Option[Int]]("config_file_id", O.Default(None))
    /** Database column incubation_min SqlType(MEDIUMINT), Default(None) */
    val incubationMin: Rep[Option[Int]] = column[Option[Int]]("incubation_min", O.Default(None))
    /** Database column acclimation_sec SqlType(INT UNSIGNED), Default(None) */
    val acclimationSec: Rep[Option[Int]] = column[Option[Int]]("acclimation_sec", O.Default(None))
    /** Database column notes SqlType(TEXT), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing ConfigFiles (database name plate_run_to_sauronx_toml) */
    lazy val configFilesFk = foreignKey("plate_run_to_sauronx_toml", configFileId, ConfigFiles)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Experiments (database name plate_run_to_project) */
    lazy val experimentsFk = foreignKey("plate_run_to_project", experimentId, Experiments)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Plates (database name plate_run_to_plate) */
    lazy val platesFk = foreignKey("plate_run_to_plate", plateId, Plates)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing SauronConfigs (database name plate_run_to_sauron_config) */
    lazy val sauronConfigsFk = foreignKey("plate_run_to_sauron_config", sauronConfigId, SauronConfigs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Submissions (database name plate_run_to_sauronx_submission) */
    lazy val submissionsFk = foreignKey("plate_run_to_sauronx_submission", submissionId, Submissions)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name plate_run_to_user) */
    lazy val usersFk = foreignKey("plate_run_to_user", experimentalistId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Index over (acclimationSec) (database name dark_adaptation_seconds) */
    val index1 = index("dark_adaptation_seconds", acclimationSec)
    /** Index over (datetimeDosed) (database name datetime_dosed) */
    val index2 = index("datetime_dosed", datetimeDosed)
    /** Index over (datetimeRun) (database name datetime_run) */
    val index3 = index("datetime_run", datetimeRun)
    /** Index over (incubationMin) (database name legacy_incubation_minutes) */
    val index4 = index("legacy_incubation_minutes", incubationMin)
    /** Index over (name) (database name legacy_name) */
    val index5 = index("legacy_name", name)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index6 = index("name_unique", name, unique=true)
    /** Uniqueness Index over (submissionId) (database name submission_unique) */
    val index7 = index("submission_unique", submissionId, unique=true)
    /** Uniqueness Index over (tag) (database name tag_unique) */
    val index8 = index("tag_unique", tag, unique=true)
  }
  /** Collection-like TableQuery object for table Runs */
  lazy val Runs = new TableQuery(tag => new Runs(tag))

  /** Entity class storing rows of table RunTags
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param runId Database column run_id SqlType(MEDIUMINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param value Database column value SqlType(VARCHAR), Length(10000,true) */
  case class RunTagsRow(id: Int, runId: Int, name: String, value: String)
  /** GetResult implicit for fetching RunTagsRow objects using plain SQL queries */
  implicit def GetResultRunTagsRow(implicit e0: GR[Int], e1: GR[String]): GR[RunTagsRow] = GR{
    prs => import prs._
    RunTagsRow.tupled((<<[Int], <<[Int], <<[String], <<[String]))
  }
  /** Table description of table run_tags. Objects of this class serve as prototypes for rows in queries. */
  class RunTags(_tableTag: Tag) extends profile.api.Table[RunTagsRow](_tableTag, Some("valar"), "run_tags") {
    def * = (id, runId, name, value) <> (RunTagsRow.tupled, RunTagsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(runId), Rep.Some(name), Rep.Some(value)).shaped.<>({r=>import r._; _1.map(_=> RunTagsRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column run_id SqlType(MEDIUMINT UNSIGNED) */
    val runId: Rep[Int] = column[Int]("run_id")
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column value SqlType(VARCHAR), Length(10000,true) */
    val value: Rep[String] = column[String]("value", O.Length(10000,varying=true))

    /** Foreign key referencing Runs (database name run_tag_to_run) */
    lazy val runsFk = foreignKey("run_tag_to_run", runId, Runs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (runId,name) (database name plate_run_name_unique) */
    val index1 = index("plate_run_name_unique", (runId, name), unique=true)
  }
  /** Collection-like TableQuery object for table RunTags */
  lazy val RunTags = new TableQuery(tag => new RunTags(tag))

  /** Entity class storing rows of table SauronConfigs
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param sauronId Database column sauron_id SqlType(TINYINT UNSIGNED)
   *  @param datetimeChanged Database column datetime_changed SqlType(DATETIME)
   *  @param description Database column description SqlType(TEXT)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SauronConfigsRow(id: Int, sauronId: Byte, datetimeChanged: java.sql.Timestamp, description: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SauronConfigsRow objects using plain SQL queries */
  implicit def GetResultSauronConfigsRow(implicit e0: GR[Int], e1: GR[Byte], e2: GR[java.sql.Timestamp], e3: GR[String]): GR[SauronConfigsRow] = GR{
    prs => import prs._
    SauronConfigsRow.tupled((<<[Int], <<[Byte], <<[java.sql.Timestamp], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table sauron_configs. Objects of this class serve as prototypes for rows in queries. */
  class SauronConfigs(_tableTag: Tag) extends profile.api.Table[SauronConfigsRow](_tableTag, Some("valar"), "sauron_configs") {
    def * = (id, sauronId, datetimeChanged, description, created) <> (SauronConfigsRow.tupled, SauronConfigsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(sauronId), Rep.Some(datetimeChanged), Rep.Some(description), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SauronConfigsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column sauron_id SqlType(TINYINT UNSIGNED) */
    val sauronId: Rep[Byte] = column[Byte]("sauron_id")
    /** Database column datetime_changed SqlType(DATETIME) */
    val datetimeChanged: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("datetime_changed")
    /** Database column description SqlType(TEXT) */
    val description: Rep[String] = column[String]("description")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Saurons (database name sauron_config_to_sauron) */
    lazy val sauronsFk = foreignKey("sauron_config_to_sauron", sauronId, Saurons)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (sauronId,datetimeChanged) (database name sauron_datetime_changed_unique) */
    val index1 = index("sauron_datetime_changed_unique", (sauronId, datetimeChanged), unique=true)
  }
  /** Collection-like TableQuery object for table SauronConfigs */
  lazy val SauronConfigs = new TableQuery(tag => new SauronConfigs(tag))

  /** Entity class storing rows of table Saurons
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param active Database column active SqlType(BIT), Default(false)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SauronsRow(id: Byte, name: String, active: Boolean = false, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SauronsRow objects using plain SQL queries */
  implicit def GetResultSauronsRow(implicit e0: GR[Byte], e1: GR[String], e2: GR[Boolean], e3: GR[java.sql.Timestamp]): GR[SauronsRow] = GR{
    prs => import prs._
    SauronsRow.tupled((<<[Byte], <<[String], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table saurons. Objects of this class serve as prototypes for rows in queries. */
  class Saurons(_tableTag: Tag) extends profile.api.Table[SauronsRow](_tableTag, Some("valar"), "saurons") {
    def * = (id, name, active, created) <> (SauronsRow.tupled, SauronsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(active), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SauronsRow.tupled((_1.get, _2.get, _3.get, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column active SqlType(BIT), Default(false) */
    val active: Rep[Boolean] = column[Boolean]("active", O.Default(false))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Index over (active) (database name current) */
    val index1 = index("current", active)
    /** Index over (name) (database name number) */
    val index2 = index("number", name)
  }
  /** Collection-like TableQuery object for table Saurons */
  lazy val Saurons = new TableQuery(tag => new Saurons(tag))

  /** Entity class storing rows of table SauronSettings
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param sauron Database column sauron SqlType(TINYINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(255,true)
   *  @param value Database column value SqlType(VARCHAR), Length(255,true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SauronSettingsRow(id: Int, sauron: Byte, name: String, value: String, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SauronSettingsRow objects using plain SQL queries */
  implicit def GetResultSauronSettingsRow(implicit e0: GR[Int], e1: GR[Byte], e2: GR[String], e3: GR[java.sql.Timestamp]): GR[SauronSettingsRow] = GR{
    prs => import prs._
    SauronSettingsRow.tupled((<<[Int], <<[Byte], <<[String], <<[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table sauron_settings. Objects of this class serve as prototypes for rows in queries. */
  class SauronSettings(_tableTag: Tag) extends profile.api.Table[SauronSettingsRow](_tableTag, Some("valar"), "sauron_settings") {
    def * = (id, sauron, name, value, created) <> (SauronSettingsRow.tupled, SauronSettingsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(sauron), Rep.Some(name), Rep.Some(value), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SauronSettingsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column sauron SqlType(TINYINT UNSIGNED) */
    val sauron: Rep[Byte] = column[Byte]("sauron")
    /** Database column name SqlType(VARCHAR), Length(255,true) */
    val name: Rep[String] = column[String]("name", O.Length(255,varying=true))
    /** Database column value SqlType(VARCHAR), Length(255,true) */
    val value: Rep[String] = column[String]("value", O.Length(255,varying=true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Saurons (database name sauron_setting_to_sauron) */
    lazy val sauronsFk = foreignKey("sauron_setting_to_sauron", sauron, Saurons)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (sauron,name) (database name sauron_name_unique) */
    val index1 = index("sauron_name_unique", (sauron, name), unique=true)
    /** Index over (name) (database name sauron_setting_name) */
    val index2 = index("sauron_setting_name", name)
  }
  /** Collection-like TableQuery object for table SauronSettings */
  lazy val SauronSettings = new TableQuery(tag => new SauronSettings(tag))

  /** Entity class storing rows of table SensorData
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param runId Database column run_id SqlType(MEDIUMINT UNSIGNED)
   *  @param sensorId Database column sensor_id SqlType(TINYINT UNSIGNED)
   *  @param floats Database column floats SqlType(LONGBLOB)
   *  @param floatsSha1 Database column floats_sha1 SqlType(BINARY) */
  case class SensorDataRow(id: Int, runId: Int, sensorId: Byte, floats: java.sql.Blob, floatsSha1: java.sql.Blob)
  /** GetResult implicit for fetching SensorDataRow objects using plain SQL queries */
  implicit def GetResultSensorDataRow(implicit e0: GR[Int], e1: GR[Byte], e2: GR[java.sql.Blob]): GR[SensorDataRow] = GR{
    prs => import prs._
    SensorDataRow.tupled((<<[Int], <<[Int], <<[Byte], <<[java.sql.Blob], <<[java.sql.Blob]))
  }
  /** Table description of table sensor_data. Objects of this class serve as prototypes for rows in queries. */
  class SensorData(_tableTag: Tag) extends profile.api.Table[SensorDataRow](_tableTag, Some("valar"), "sensor_data") {
    def * = (id, runId, sensorId, floats, floatsSha1) <> (SensorDataRow.tupled, SensorDataRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(runId), Rep.Some(sensorId), Rep.Some(floats), Rep.Some(floatsSha1)).shaped.<>({r=>import r._; _1.map(_=> SensorDataRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column run_id SqlType(MEDIUMINT UNSIGNED) */
    val runId: Rep[Int] = column[Int]("run_id")
    /** Database column sensor_id SqlType(TINYINT UNSIGNED) */
    val sensorId: Rep[Byte] = column[Byte]("sensor_id")
    /** Database column floats SqlType(LONGBLOB) */
    val floats: Rep[java.sql.Blob] = column[java.sql.Blob]("floats")
    /** Database column floats_sha1 SqlType(BINARY) */
    val floatsSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("floats_sha1")

    /** Foreign key referencing Runs (database name sensor_data_to_plate_run) */
    lazy val runsFk = foreignKey("sensor_data_to_plate_run", runId, Runs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Sensors (database name sensor_data_to_sensor) */
    lazy val sensorsFk = foreignKey("sensor_data_to_sensor", sensorId, Sensors)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (floatsSha1) (database name floats_sha1) */
    val index1 = index("floats_sha1", floatsSha1)
  }
  /** Collection-like TableQuery object for table SensorData */
  lazy val SensorData = new TableQuery(tag => new SensorData(tag))

  /** Entity class storing rows of table Sensors
   *  @param id Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param dataType Database column data_type SqlType(ENUM), Length(15,false)
   *  @param blobType Database column blob_type SqlType(ENUM), Length(20,false), Default(None)
   *  @param nBetween Database column n_between SqlType(INT UNSIGNED), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SensorsRow(id: Byte, name: String, description: Option[String] = None, dataType: String, blobType: Option[String] = None, nBetween: Option[Int] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SensorsRow objects using plain SQL queries */
  implicit def GetResultSensorsRow(implicit e0: GR[Byte], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[java.sql.Timestamp]): GR[SensorsRow] = GR{
    prs => import prs._
    SensorsRow.tupled((<<[Byte], <<[String], <<?[String], <<[String], <<?[String], <<?[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table sensors. Objects of this class serve as prototypes for rows in queries. */
  class Sensors(_tableTag: Tag) extends profile.api.Table[SensorsRow](_tableTag, Some("valar"), "sensors") {
    def * = (id, name, description, dataType, blobType, nBetween, created) <> (SensorsRow.tupled, SensorsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(dataType), blobType, nBetween, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SensorsRow.tupled((_1.get, _2.get, _3, _4.get, _5, _6, _7.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(TINYINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Byte] = column[Byte]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(250,varying=true), O.Default(None))
    /** Database column data_type SqlType(ENUM), Length(15,false) */
    val dataType: Rep[String] = column[String]("data_type", O.Length(15,varying=false))
    /** Database column blob_type SqlType(ENUM), Length(20,false), Default(None) */
    val blobType: Rep[Option[String]] = column[Option[String]]("blob_type", O.Length(20,varying=false), O.Default(None))
    /** Database column n_between SqlType(INT UNSIGNED), Default(None) */
    val nBetween: Rep[Option[Int]] = column[Option[Int]]("n_between", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Uniqueness Index over (name) (database name name) */
    val index1 = index("name", name, unique=true)
  }
  /** Collection-like TableQuery object for table Sensors */
  lazy val Sensors = new TableQuery(tag => new Sensors(tag))

  /** Entity class storing rows of table Stimuli
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param defaultColor Database column default_color SqlType(CHAR), Length(6,false)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param analog Database column analog SqlType(BIT), Default(false)
   *  @param rgb Database column rgb SqlType(BINARY), Default(None)
   *  @param wavelengthNm Database column wavelength_nm SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param audioFileId Database column audio_file_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class StimuliRow(id: Int, name: String, defaultColor: String, description: Option[String] = None, analog: Boolean = false, rgb: Option[java.sql.Blob] = None, wavelengthNm: Option[Int] = None, audioFileId: Option[Int] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching StimuliRow objects using plain SQL queries */
  implicit def GetResultStimuliRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Boolean], e4: GR[Option[java.sql.Blob]], e5: GR[Option[Int]], e6: GR[java.sql.Timestamp]): GR[StimuliRow] = GR{
    prs => import prs._
    StimuliRow.tupled((<<[Int], <<[String], <<[String], <<?[String], <<[Boolean], <<?[java.sql.Blob], <<?[Int], <<?[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table stimuli. Objects of this class serve as prototypes for rows in queries. */
  class Stimuli(_tableTag: Tag) extends profile.api.Table[StimuliRow](_tableTag, Some("valar"), "stimuli") {
    def * = (id, name, defaultColor, description, analog, rgb, wavelengthNm, audioFileId, created) <> (StimuliRow.tupled, StimuliRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(defaultColor), description, Rep.Some(analog), rgb, wavelengthNm, audioFileId, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> StimuliRow.tupled((_1.get, _2.get, _3.get, _4, _5.get, _6, _7, _8, _9.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column default_color SqlType(CHAR), Length(6,false) */
    val defaultColor: Rep[String] = column[String]("default_color", O.Length(6,varying=false))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(250,varying=true), O.Default(None))
    /** Database column analog SqlType(BIT), Default(false) */
    val analog: Rep[Boolean] = column[Boolean]("analog", O.Default(false))
    /** Database column rgb SqlType(BINARY), Default(None) */
    val rgb: Rep[Option[java.sql.Blob]] = column[Option[java.sql.Blob]]("rgb", O.Default(None))
    /** Database column wavelength_nm SqlType(SMALLINT UNSIGNED), Default(None) */
    val wavelengthNm: Rep[Option[Int]] = column[Option[Int]]("wavelength_nm", O.Default(None))
    /** Database column audio_file_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val audioFileId: Rep[Option[Int]] = column[Option[Int]]("audio_file_id", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing AudioFiles (database name stimulus_to_audio_file) */
    lazy val audioFilesFk = foreignKey("stimulus_to_audio_file", audioFileId, AudioFiles)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (audioFileId) (database name audio_file_id_unique) */
    val index1 = index("audio_file_id_unique", audioFileId, unique=true)
    /** Uniqueness Index over (name) (database name name_unique) */
    val index2 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Stimuli */
  lazy val Stimuli = new TableQuery(tag => new Stimuli(tag))

  /** Entity class storing rows of table StimulusFrames
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param assayId Database column assay_id SqlType(SMALLINT UNSIGNED)
   *  @param stimulusId Database column stimulus_id SqlType(SMALLINT UNSIGNED)
   *  @param frames Database column frames SqlType(LONGBLOB)
   *  @param framesSha1 Database column frames_sha1 SqlType(BINARY) */
  case class StimulusFramesRow(id: Int, assayId: Int, stimulusId: Int, frames: java.sql.Blob, framesSha1: java.sql.Blob)
  /** GetResult implicit for fetching StimulusFramesRow objects using plain SQL queries */
  implicit def GetResultStimulusFramesRow(implicit e0: GR[Int], e1: GR[java.sql.Blob]): GR[StimulusFramesRow] = GR{
    prs => import prs._
    StimulusFramesRow.tupled((<<[Int], <<[Int], <<[Int], <<[java.sql.Blob], <<[java.sql.Blob]))
  }
  /** Table description of table stimulus_frames. Objects of this class serve as prototypes for rows in queries. */
  class StimulusFrames(_tableTag: Tag) extends profile.api.Table[StimulusFramesRow](_tableTag, Some("valar"), "stimulus_frames") {
    def * = (id, assayId, stimulusId, frames, framesSha1) <> (StimulusFramesRow.tupled, StimulusFramesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(assayId), Rep.Some(stimulusId), Rep.Some(frames), Rep.Some(framesSha1)).shaped.<>({r=>import r._; _1.map(_=> StimulusFramesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column assay_id SqlType(SMALLINT UNSIGNED) */
    val assayId: Rep[Int] = column[Int]("assay_id")
    /** Database column stimulus_id SqlType(SMALLINT UNSIGNED) */
    val stimulusId: Rep[Int] = column[Int]("stimulus_id")
    /** Database column frames SqlType(LONGBLOB) */
    val frames: Rep[java.sql.Blob] = column[java.sql.Blob]("frames")
    /** Database column frames_sha1 SqlType(BINARY) */
    val framesSha1: Rep[java.sql.Blob] = column[java.sql.Blob]("frames_sha1")

    /** Foreign key referencing Assays (database name stimulus_frames_to_assay) */
    lazy val assaysFk = foreignKey("stimulus_frames_to_assay", assayId, Assays)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
    /** Foreign key referencing Stimuli (database name stimulus_frames_to_stimulus) */
    lazy val stimuliFk = foreignKey("stimulus_frames_to_stimulus", stimulusId, Stimuli)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (assayId,stimulusId) (database name assay_id_stimulus_id) */
    val index1 = index("assay_id_stimulus_id", (assayId, stimulusId), unique=true)
    /** Index over (framesSha1) (database name frames_sha1) */
    val index2 = index("frames_sha1", framesSha1)
  }
  /** Collection-like TableQuery object for table StimulusFrames */
  lazy val StimulusFrames = new TableQuery(tag => new StimulusFrames(tag))

  /** Entity class storing rows of table SubmissionParams
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param submissionId Database column submission_id SqlType(MEDIUMINT UNSIGNED)
   *  @param name Database column name SqlType(VARCHAR), Length(250,true)
   *  @param paramType Database column param_type SqlType(ENUM), Length(8,false)
   *  @param value Database column value SqlType(VARCHAR), Length(4000,true) */
  case class SubmissionParamsRow(id: Int, submissionId: Int, name: String, paramType: String, value: String)
  /** GetResult implicit for fetching SubmissionParamsRow objects using plain SQL queries */
  implicit def GetResultSubmissionParamsRow(implicit e0: GR[Int], e1: GR[String]): GR[SubmissionParamsRow] = GR{
    prs => import prs._
    SubmissionParamsRow.tupled((<<[Int], <<[Int], <<[String], <<[String], <<[String]))
  }
  /** Table description of table submission_params. Objects of this class serve as prototypes for rows in queries. */
  class SubmissionParams(_tableTag: Tag) extends profile.api.Table[SubmissionParamsRow](_tableTag, Some("valar"), "submission_params") {
    def * = (id, submissionId, name, paramType, value) <> (SubmissionParamsRow.tupled, SubmissionParamsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(submissionId), Rep.Some(name), Rep.Some(paramType), Rep.Some(value)).shaped.<>({r=>import r._; _1.map(_=> SubmissionParamsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column submission_id SqlType(MEDIUMINT UNSIGNED) */
    val submissionId: Rep[Int] = column[Int]("submission_id")
    /** Database column name SqlType(VARCHAR), Length(250,true) */
    val name: Rep[String] = column[String]("name", O.Length(250,varying=true))
    /** Database column param_type SqlType(ENUM), Length(8,false) */
    val paramType: Rep[String] = column[String]("param_type", O.Length(8,varying=false))
    /** Database column value SqlType(VARCHAR), Length(4000,true) */
    val value: Rep[String] = column[String]("value", O.Length(4000,varying=true))

    /** Foreign key referencing Submissions (database name sauronx_submission_parameter_to_sauronx_submission) */
    lazy val submissionsFk = foreignKey("sauronx_submission_parameter_to_sauronx_submission", submissionId, Submissions)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (submissionId,name) (database name sauronx_submission_name_unique) */
    val index1 = index("sauronx_submission_name_unique", (submissionId, name), unique=true)
  }
  /** Collection-like TableQuery object for table SubmissionParams */
  lazy val SubmissionParams = new TableQuery(tag => new SubmissionParams(tag))

  /** Entity class storing rows of table SubmissionRecords
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param submissionId Database column submission_id SqlType(MEDIUMINT UNSIGNED)
   *  @param status Database column status VARCHAR(100), Length(100,false), Default(None)
   *  @param sauronId Database column sauron_id SqlType(TINYINT UNSIGNED)
   *  @param datetimeModified Database column datetime_modified SqlType(DATETIME)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SubmissionRecordsRow(id: Int, submissionId: Int, status: Option[String] = None, sauronId: Byte, datetimeModified: java.sql.Timestamp, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SubmissionRecordsRow objects using plain SQL queries */
  implicit def GetResultSubmissionRecordsRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[Byte], e3: GR[java.sql.Timestamp]): GR[SubmissionRecordsRow] = GR{
    prs => import prs._
    SubmissionRecordsRow.tupled((<<[Int], <<[Int], <<?[String], <<[Byte], <<[java.sql.Timestamp], <<[java.sql.Timestamp]))
  }
  /** Table description of table submission_records. Objects of this class serve as prototypes for rows in queries. */
  class SubmissionRecords(_tableTag: Tag) extends profile.api.Table[SubmissionRecordsRow](_tableTag, Some("valar"), "submission_records") {
    def * = (id, submissionId, status, sauronId, datetimeModified, created) <> (SubmissionRecordsRow.tupled, SubmissionRecordsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(submissionId), status, Rep.Some(sauronId), Rep.Some(datetimeModified), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SubmissionRecordsRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column submission_id SqlType(MEDIUMINT UNSIGNED) */
    val submissionId: Rep[Int] = column[Int]("submission_id")
    /** Database column status SqlType(ENUM), Length(28,false), Default(None) */
    val status: Rep[Option[String]] = column[Option[String]]("status", O.Length(100,varying=false), O.Default(None))
    /** Database column sauron_id SqlType(TINYINT UNSIGNED) */
    val sauronId: Rep[Byte] = column[Byte]("sauron_id")
    /** Database column datetime_modified SqlType(DATETIME) */
    val datetimeModified: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("datetime_modified")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Saurons (database name sauronx_submission_history_to_sauron) */
    lazy val sauronsFk = foreignKey("sauronx_submission_history_to_sauron", sauronId, Saurons)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Submissions (database name sauronx_submission_history_to_submission) */
    lazy val submissionsFk = foreignKey("sauronx_submission_history_to_submission", submissionId, Submissions)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (submissionId,status,datetimeModified) (database name all_unique) */
    val index1 = index("all_unique", (submissionId, status, datetimeModified), unique=true)
  }
  /** Collection-like TableQuery object for table SubmissionRecords */
  lazy val SubmissionRecords = new TableQuery(tag => new SubmissionRecords(tag))

  /** Entity class storing rows of table Submissions
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param lookupHash Database column lookup_hash SqlType(CHAR), Length(12,false)
   *  @param experimentId Database column experiment_id SqlType(SMALLINT UNSIGNED)
   *  @param userId Database column user_id SqlType(SMALLINT UNSIGNED)
   *  @param personPlatedId Database column person_plated_id SqlType(SMALLINT UNSIGNED)
   *  @param continuingId Database column continuing_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param datetimePlated Database column datetime_plated SqlType(DATETIME)
   *  @param datetimeDosed Database column datetime_dosed SqlType(DATETIME), Default(None)
   *  @param acclimationSec Database column acclimation_sec SqlType(INT UNSIGNED), Default(None)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true)
   *  @param notes Database column notes SqlType(MEDIUMTEXT), Length(16777215,true), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class SubmissionsRow(id: Int, lookupHash: String, experimentId: Int, userId: Int, personPlatedId: Int, continuingId: Option[Int] = None, datetimePlated: java.sql.Timestamp, datetimeDosed: Option[java.sql.Timestamp] = None, acclimationSec: Option[Int] = None, description: String, notes: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SubmissionsRow objects using plain SQL queries */
  implicit def GetResultSubmissionsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Int]], e3: GR[java.sql.Timestamp], e4: GR[Option[java.sql.Timestamp]], e5: GR[Option[String]]): GR[SubmissionsRow] = GR{
    prs => import prs._
    SubmissionsRow.tupled((<<[Int], <<[String], <<[Int], <<[Int], <<[Int], <<?[Int], <<[java.sql.Timestamp], <<?[java.sql.Timestamp], <<?[Int], <<[String], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table submissions. Objects of this class serve as prototypes for rows in queries. */
  class Submissions(_tableTag: Tag) extends profile.api.Table[SubmissionsRow](_tableTag, Some("valar"), "submissions") {
    def * = (id, lookupHash, experimentId, userId, personPlatedId, continuingId, datetimePlated, datetimeDosed, acclimationSec, description, notes, created) <> (SubmissionsRow.tupled, SubmissionsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(lookupHash), Rep.Some(experimentId), Rep.Some(userId), Rep.Some(personPlatedId), continuingId, Rep.Some(datetimePlated), datetimeDosed, acclimationSec, Rep.Some(description), notes, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SubmissionsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6, _7.get, _8, _9, _10.get, _11, _12.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column lookup_hash SqlType(CHAR), Length(12,false) */
    val lookupHash: Rep[String] = column[String]("lookup_hash", O.Length(12,varying=false))
    /** Database column experiment_id SqlType(SMALLINT UNSIGNED) */
    val experimentId: Rep[Int] = column[Int]("experiment_id")
    /** Database column user_id SqlType(SMALLINT UNSIGNED) */
    val userId: Rep[Int] = column[Int]("user_id")
    /** Database column person_plated_id SqlType(SMALLINT UNSIGNED) */
    val personPlatedId: Rep[Int] = column[Int]("person_plated_id")
    /** Database column continuing_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val continuingId: Rep[Option[Int]] = column[Option[Int]]("continuing_id", O.Default(None))
    /** Database column datetime_plated SqlType(DATETIME) */
    val datetimePlated: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("datetime_plated")
    /** Database column datetime_dosed SqlType(DATETIME), Default(None) */
    val datetimeDosed: Rep[Option[java.sql.Timestamp]] = column[Option[java.sql.Timestamp]]("datetime_dosed", O.Default(None))
    /** Database column acclimation_sec SqlType(INT UNSIGNED), Default(None) */
    val acclimationSec: Rep[Option[Int]] = column[Option[Int]]("acclimation_sec", O.Default(None))
    /** Database column description SqlType(VARCHAR), Length(250,true) */
    val description: Rep[String] = column[String]("description", O.Length(250,varying=true))
    /** Database column notes SqlType(MEDIUMTEXT), Length(16777215,true), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Length(16777215,varying=true), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Experiments (database name sauronx_submission_to_project) */
    lazy val experimentsFk = foreignKey("sauronx_submission_to_project", experimentId, Experiments)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Submissions (database name matched_submission) */
    lazy val submissionsFk = foreignKey("matched_submission", continuingId, Submissions)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name sauronx_submission_to_person_plated) */
    lazy val usersFk3 = foreignKey("sauronx_submission_to_person_plated", personPlatedId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name sauronx_submission_to_user) */
    lazy val usersFk4 = foreignKey("sauronx_submission_to_user", userId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (lookupHash) (database name id_hash_hex) */
    val index1 = index("id_hash_hex", lookupHash, unique=true)
  }
  /** Collection-like TableQuery object for table Submissions */
  lazy val Submissions = new TableQuery(tag => new Submissions(tag))

  /** Entity class storing rows of table Projects
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param typeId Database column type_id SqlType(TINYINT UNSIGNED), Default(None)
   *  @param creatorId Database column creator_id SqlType(SMALLINT UNSIGNED)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param reason Database column reason SqlType(MEDIUMTEXT), Length(16777215,true), Default(None)
   *  @param methods Database column methods SqlType(MEDIUMTEXT), Length(16777215,true), Default(None)
   *  @param active Database column active SqlType(BIT), Default(true)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class ProjectsRow(id: Int, name: String, typeId: Option[Byte] = None, creatorId: Int, description: Option[String] = None, reason: Option[String] = None, methods: Option[String] = None, active: Boolean = true, created: java.sql.Timestamp)
  /** GetResult implicit for fetching ProjectsRow objects using plain SQL queries */
  implicit def GetResultProjectsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Byte]], e3: GR[Option[String]], e4: GR[Boolean], e5: GR[java.sql.Timestamp]): GR[ProjectsRow] = GR{
    prs => import prs._
    ProjectsRow.tupled((<<[Int], <<[String], <<?[Byte], <<[Int], <<?[String], <<?[String], <<?[String], <<[Boolean], <<[java.sql.Timestamp]))
  }
  /** Table description of table projects. Objects of this class serve as prototypes for rows in queries. */
  class Projects(_tableTag: Tag) extends profile.api.Table[ProjectsRow](_tableTag, Some("valar"), "projects") {
    def * = (id, name, typeId, creatorId, description, reason, methods, active, created) <> (ProjectsRow.tupled, ProjectsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), typeId, Rep.Some(creatorId), description, reason, methods, Rep.Some(active), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> ProjectsRow.tupled((_1.get, _2.get, _3, _4.get, _5, _6, _7, _8.get, _9.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column type_id SqlType(TINYINT UNSIGNED), Default(None) */
    val typeId: Rep[Option[Byte]] = column[Option[Byte]]("type_id", O.Default(None))
    /** Database column creator_id SqlType(SMALLINT UNSIGNED) */
    val creatorId: Rep[Int] = column[Int]("creator_id")
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column reason SqlType(MEDIUMTEXT), Length(16777215,true), Default(None) */
    val reason: Rep[Option[String]] = column[Option[String]]("reason", O.Length(16777215,varying=true), O.Default(None))
    /** Database column methods SqlType(MEDIUMTEXT), Length(16777215,true), Default(None) */
    val methods: Rep[Option[String]] = column[Option[String]]("methods", O.Length(16777215,varying=true), O.Default(None))
    /** Database column active SqlType(BIT), Default(true) */
    val active: Rep[Boolean] = column[Boolean]("active", O.Default(true))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing ProjectTypes (database name project_to_project_type) */
    lazy val projectTypesFk = foreignKey("project_to_project_type", typeId, ProjectTypes)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name project_to_user) */
    lazy val usersFk = foreignKey("project_to_user", creatorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table Projects */
  lazy val Projects = new TableQuery(tag => new Projects(tag))

  /** Entity class storing rows of table Suppliers
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(50,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param created Database column created SqlType(DATETIME) */
  case class SuppliersRow(id: Int, name: String, description: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching SuppliersRow objects using plain SQL queries */
  implicit def GetResultSuppliersRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[java.sql.Timestamp]): GR[SuppliersRow] = GR{
    prs => import prs._
    SuppliersRow.tupled((<<[Int], <<[String], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table suppliers. Objects of this class serve as prototypes for rows in queries. */
  class Suppliers(_tableTag: Tag) extends profile.api.Table[SuppliersRow](_tableTag, Some("valar"), "suppliers") {
    def * = (id, name, description, created) <> (SuppliersRow.tupled, SuppliersRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> SuppliersRow.tupled((_1.get, _2.get, _3, _4.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(50,true) */
    val name: Rep[String] = column[String]("name", O.Length(50,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(250,varying=true), O.Default(None))
    /** Database column created SqlType(DATETIME) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Uniqueness Index over (name) (database name name) */
    val index1 = index("name", name, unique=true)
  }
  /** Collection-like TableQuery object for table Suppliers */
  lazy val Suppliers = new TableQuery(tag => new Suppliers(tag))

  /** Entity class storing rows of table TemplateAssays
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param authorId Database column author_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param specializes Database column specializes SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class TemplateAssaysRow(id: Int, name: String, description: Option[String] = None, authorId: Option[Int] = None, specializes: Option[Int] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching TemplateAssaysRow objects using plain SQL queries */
  implicit def GetResultTemplateAssaysRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Option[Int]], e4: GR[java.sql.Timestamp]): GR[TemplateAssaysRow] = GR{
    prs => import prs._
    TemplateAssaysRow.tupled((<<[Int], <<[String], <<?[String], <<?[Int], <<?[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table template_assays. Objects of this class serve as prototypes for rows in queries. */
  class TemplateAssays(_tableTag: Tag) extends profile.api.Table[TemplateAssaysRow](_tableTag, Some("valar"), "template_assays") {
    def * = (id, name, description, authorId, specializes, created) <> (TemplateAssaysRow.tupled, TemplateAssaysRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, authorId, specializes, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> TemplateAssaysRow.tupled((_1.get, _2.get, _3, _4, _5, _6.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column author_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val authorId: Rep[Option[Int]] = column[Option[Int]]("author_id", O.Default(None))
    /** Database column specializes SqlType(SMALLINT UNSIGNED), Default(None) */
    val specializes: Rep[Option[Int]] = column[Option[Int]]("specializes", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing TemplateAssays (database name template_assay_specialization) */
    lazy val templateAssaysFk = foreignKey("template_assay_specialization", specializes, TemplateAssays)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.SetNull)
    /** Foreign key referencing Users (database name template_assay_to_user) */
    lazy val usersFk = foreignKey("template_assay_to_user", authorId, Users)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.SetNull)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table TemplateAssays */
  lazy val TemplateAssays = new TableQuery(tag => new TemplateAssays(tag))

  /** Entity class storing rows of table TemplatePlates
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param plateTypeId Database column plate_type_id SqlType(TINYINT UNSIGNED)
   *  @param authorId Database column author_id SqlType(SMALLINT UNSIGNED)
   *  @param hidden Database column hidden SqlType(BIT), Default(false)
   *  @param created Database column created SqlType(TIMESTAMP)
   *  @param specializes Database column specializes SqlType(SMALLINT UNSIGNED), Default(None) */
  case class TemplatePlatesRow(id: Int, name: String, description: Option[String] = None, plateTypeId: Byte, authorId: Int, hidden: Boolean = false, created: java.sql.Timestamp, specializes: Option[Int] = None)
  /** GetResult implicit for fetching TemplatePlatesRow objects using plain SQL queries */
  implicit def GetResultTemplatePlatesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Byte], e4: GR[Boolean], e5: GR[java.sql.Timestamp], e6: GR[Option[Int]]): GR[TemplatePlatesRow] = GR{
    prs => import prs._
    TemplatePlatesRow.tupled((<<[Int], <<[String], <<?[String], <<[Byte], <<[Int], <<[Boolean], <<[java.sql.Timestamp], <<?[Int]))
  }
  /** Table description of table template_plates. Objects of this class serve as prototypes for rows in queries. */
  class TemplatePlates(_tableTag: Tag) extends profile.api.Table[TemplatePlatesRow](_tableTag, Some("valar"), "template_plates") {
    def * = (id, name, description, plateTypeId, authorId, hidden, created, specializes) <> (TemplatePlatesRow.tupled, TemplatePlatesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(plateTypeId), Rep.Some(authorId), Rep.Some(hidden), Rep.Some(created), specializes).shaped.<>({r=>import r._; _1.map(_=> TemplatePlatesRow.tupled((_1.get, _2.get, _3, _4.get, _5.get, _6.get, _7.get, _8)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column plate_type_id SqlType(TINYINT UNSIGNED) */
    val plateTypeId: Rep[Byte] = column[Byte]("plate_type_id")
    /** Database column author_id SqlType(SMALLINT UNSIGNED) */
    val authorId: Rep[Int] = column[Int]("author_id")
    /** Database column hidden SqlType(BIT), Default(false) */
    val hidden: Rep[Boolean] = column[Boolean]("hidden", O.Default(false))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")
    /** Database column specializes SqlType(SMALLINT UNSIGNED), Default(None) */
    val specializes: Rep[Option[Int]] = column[Option[Int]]("specializes", O.Default(None))

    /** Foreign key referencing PlateTypes (database name template_plate_to_plate_type) */
    lazy val plateTypesFk = foreignKey("template_plate_to_plate_type", plateTypeId, PlateTypes)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing TemplatePlates (database name template_plate_specialization) */
    lazy val templatePlatesFk = foreignKey("template_plate_specialization", specializes, TemplatePlates)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.SetNull)
    /** Foreign key referencing Users (database name template_plate_to_user) */
    lazy val usersFk = foreignKey("template_plate_to_user", authorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table TemplatePlates */
  lazy val TemplatePlates = new TableQuery(tag => new TemplatePlates(tag))

  /** Entity class storing rows of table TemplateStimulusFrames
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param templateAssayId Database column template_assay_id SqlType(SMALLINT UNSIGNED)
   *  @param rangeExpression Database column range_expression SqlType(VARCHAR), Length(150,true)
   *  @param stimulusId Database column stimulus_id SqlType(SMALLINT UNSIGNED)
   *  @param valueExpression Database column value_expression SqlType(VARCHAR), Length(250,true) */
  case class TemplateStimulusFramesRow(id: Int, templateAssayId: Int, rangeExpression: String, stimulusId: Int, valueExpression: String)
  /** GetResult implicit for fetching TemplateStimulusFramesRow objects using plain SQL queries */
  implicit def GetResultTemplateStimulusFramesRow(implicit e0: GR[Int], e1: GR[String]): GR[TemplateStimulusFramesRow] = GR{
    prs => import prs._
    TemplateStimulusFramesRow.tupled((<<[Int], <<[Int], <<[String], <<[Int], <<[String]))
  }
  /** Table description of table template_stimulus_frames. Objects of this class serve as prototypes for rows in queries. */
  class TemplateStimulusFrames(_tableTag: Tag) extends profile.api.Table[TemplateStimulusFramesRow](_tableTag, Some("valar"), "template_stimulus_frames") {
    def * = (id, templateAssayId, rangeExpression, stimulusId, valueExpression) <> (TemplateStimulusFramesRow.tupled, TemplateStimulusFramesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(templateAssayId), Rep.Some(rangeExpression), Rep.Some(stimulusId), Rep.Some(valueExpression)).shaped.<>({r=>import r._; _1.map(_=> TemplateStimulusFramesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column template_assay_id SqlType(SMALLINT UNSIGNED) */
    val templateAssayId: Rep[Int] = column[Int]("template_assay_id")
    /** Database column range_expression SqlType(VARCHAR), Length(150,true) */
    val rangeExpression: Rep[String] = column[String]("range_expression", O.Length(150,varying=true))
    /** Database column stimulus_id SqlType(SMALLINT UNSIGNED) */
    val stimulusId: Rep[Int] = column[Int]("stimulus_id")
    /** Database column value_expression SqlType(VARCHAR), Length(250,true) */
    val valueExpression: Rep[String] = column[String]("value_expression", O.Length(250,varying=true))

    /** Foreign key referencing Stimuli (database name template_stimulus_frames_to_stimulus) */
    lazy val stimuliFk = foreignKey("template_stimulus_frames_to_stimulus", stimulusId, Stimuli)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing TemplateAssays (database name template_frames_to_template_assay) */
    lazy val templateAssaysFk = foreignKey("template_frames_to_template_assay", templateAssayId, TemplateAssays)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
  }
  /** Collection-like TableQuery object for table TemplateStimulusFrames */
  lazy val TemplateStimulusFrames = new TableQuery(tag => new TemplateStimulusFrames(tag))

  /** Entity class storing rows of table TemplateTreatments
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param templatePlateId Database column template_plate_id SqlType(SMALLINT UNSIGNED)
   *  @param wellRangeExpression Database column well_range_expression SqlType(VARCHAR), Length(100,true)
   *  @param batchExpression Database column batch_expression SqlType(VARCHAR), Length(250,true)
   *  @param doseExpression Database column dose_expression SqlType(VARCHAR), Length(200,true) */
  case class TemplateTreatmentsRow(id: Int, templatePlateId: Int, wellRangeExpression: String, batchExpression: String, doseExpression: String)
  /** GetResult implicit for fetching TemplateTreatmentsRow objects using plain SQL queries */
  implicit def GetResultTemplateTreatmentsRow(implicit e0: GR[Int], e1: GR[String]): GR[TemplateTreatmentsRow] = GR{
    prs => import prs._
    TemplateTreatmentsRow.tupled((<<[Int], <<[Int], <<[String], <<[String], <<[String]))
  }
  /** Table description of table template_treatments. Objects of this class serve as prototypes for rows in queries. */
  class TemplateTreatments(_tableTag: Tag) extends profile.api.Table[TemplateTreatmentsRow](_tableTag, Some("valar"), "template_treatments") {
    def * = (id, templatePlateId, wellRangeExpression, batchExpression, doseExpression) <> (TemplateTreatmentsRow.tupled, TemplateTreatmentsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(templatePlateId), Rep.Some(wellRangeExpression), Rep.Some(batchExpression), Rep.Some(doseExpression)).shaped.<>({r=>import r._; _1.map(_=> TemplateTreatmentsRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column template_plate_id SqlType(SMALLINT UNSIGNED) */
    val templatePlateId: Rep[Int] = column[Int]("template_plate_id")
    /** Database column well_range_expression SqlType(VARCHAR), Length(100,true) */
    val wellRangeExpression: Rep[String] = column[String]("well_range_expression", O.Length(100,varying=true))
    /** Database column batch_expression SqlType(VARCHAR), Length(250,true) */
    val batchExpression: Rep[String] = column[String]("batch_expression", O.Length(250,varying=true))
    /** Database column dose_expression SqlType(VARCHAR), Length(200,true) */
    val doseExpression: Rep[String] = column[String]("dose_expression", O.Length(200,varying=true))

    /** Foreign key referencing TemplatePlates (database name template_well_to_template_plate) */
    lazy val templatePlatesFk = foreignKey("template_well_to_template_plate", templatePlateId, TemplatePlates)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
  }
  /** Collection-like TableQuery object for table TemplateTreatments */
  lazy val TemplateTreatments = new TableQuery(tag => new TemplateTreatments(tag))

  /** Entity class storing rows of table TemplateWells
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param templatePlateId Database column template_plate_id SqlType(SMALLINT UNSIGNED)
   *  @param wellRangeExpression Database column well_range_expression SqlType(VARCHAR), Length(255,true)
   *  @param controlType Database column control_type SqlType(TINYINT UNSIGNED), Default(None)
   *  @param nExpression Database column n_expression SqlType(VARCHAR), Length(250,true)
   *  @param variantExpression Database column variant_expression SqlType(VARCHAR), Length(250,true)
   *  @param ageExpression Database column age_expression SqlType(VARCHAR), Length(255,true)
   *  @param groupExpression Database column group_expression SqlType(VARCHAR), Length(255,true) */
  case class TemplateWellsRow(id: Int, templatePlateId: Int, wellRangeExpression: String, controlType: Option[Byte] = None, nExpression: String, variantExpression: String, ageExpression: String, groupExpression: String)
  /** GetResult implicit for fetching TemplateWellsRow objects using plain SQL queries */
  implicit def GetResultTemplateWellsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[Byte]]): GR[TemplateWellsRow] = GR{
    prs => import prs._
    TemplateWellsRow.tupled((<<[Int], <<[Int], <<[String], <<?[Byte], <<[String], <<[String], <<[String], <<[String]))
  }
  /** Table description of table template_wells. Objects of this class serve as prototypes for rows in queries. */
  class TemplateWells(_tableTag: Tag) extends profile.api.Table[TemplateWellsRow](_tableTag, Some("valar"), "template_wells") {
    def * = (id, templatePlateId, wellRangeExpression, controlType, nExpression, variantExpression, ageExpression, groupExpression) <> (TemplateWellsRow.tupled, TemplateWellsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(templatePlateId), Rep.Some(wellRangeExpression), controlType, Rep.Some(nExpression), Rep.Some(variantExpression), Rep.Some(ageExpression), Rep.Some(groupExpression)).shaped.<>({r=>import r._; _1.map(_=> TemplateWellsRow.tupled((_1.get, _2.get, _3.get, _4, _5.get, _6.get, _7.get, _8.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column template_plate_id SqlType(SMALLINT UNSIGNED) */
    val templatePlateId: Rep[Int] = column[Int]("template_plate_id")
    /** Database column well_range_expression SqlType(VARCHAR), Length(255,true) */
    val wellRangeExpression: Rep[String] = column[String]("well_range_expression", O.Length(255,varying=true))
    /** Database column control_type SqlType(TINYINT UNSIGNED), Default(None) */
    val controlType: Rep[Option[Byte]] = column[Option[Byte]]("control_type", O.Default(None))
    /** Database column n_expression SqlType(VARCHAR), Length(250,true) */
    val nExpression: Rep[String] = column[String]("n_expression", O.Length(250,varying=true))
    /** Database column variant_expression SqlType(VARCHAR), Length(250,true) */
    val variantExpression: Rep[String] = column[String]("variant_expression", O.Length(250,varying=true))
    /** Database column age_expression SqlType(VARCHAR), Length(255,true) */
    val ageExpression: Rep[String] = column[String]("age_expression", O.Length(255,varying=true))
    /** Database column group_expression SqlType(VARCHAR), Length(255,true) */
    val groupExpression: Rep[String] = column[String]("group_expression", O.Length(255,varying=true))

    /** Foreign key referencing ControlTypes (database name template_well_to_control_type) */
    lazy val controlTypesFk = foreignKey("template_well_to_control_type", controlType, ControlTypes)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing TemplatePlates (database name tw_to_tp) */
    lazy val templatePlatesFk = foreignKey("tw_to_tp", templatePlateId, TemplatePlates)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)
  }
  /** Collection-like TableQuery object for table TemplateWells */
  lazy val TemplateWells = new TableQuery(tag => new TemplateWells(tag))

  /** Entity class storing rows of table Tissues
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(200,true)
   *  @param externalId Database column external_id SqlType(VARCHAR), Length(100,true)
   *  @param refId Database column ref_id SqlType(SMALLINT UNSIGNED)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class TissuesRow(id: Int, name: String, externalId: String, refId: Int, created: java.sql.Timestamp)
  /** GetResult implicit for fetching TissuesRow objects using plain SQL queries */
  implicit def GetResultTissuesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[java.sql.Timestamp]): GR[TissuesRow] = GR{
    prs => import prs._
    TissuesRow.tupled((<<[Int], <<[String], <<[String], <<[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table tissues. Objects of this class serve as prototypes for rows in queries. */
  class Tissues(_tableTag: Tag) extends profile.api.Table[TissuesRow](_tableTag, Some("valar"), "tissues") {
    def * = (id, name, externalId, refId, created) <> (TissuesRow.tupled, TissuesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), Rep.Some(externalId), Rep.Some(refId), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> TissuesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(200,true) */
    val name: Rep[String] = column[String]("name", O.Length(200,varying=true))
    /** Database column external_id SqlType(VARCHAR), Length(100,true) */
    val externalId: Rep[String] = column[String]("external_id", O.Length(100,varying=true))
    /** Database column ref_id SqlType(SMALLINT UNSIGNED) */
    val refId: Rep[Int] = column[Int]("ref_id")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing Refs (database name tissue_to_ref) */
    lazy val refsFk = foreignKey("tissue_to_ref", refId, Refs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (externalId,refId) (database name external_id_ref_unique) */
    val index1 = index("external_id_ref_unique", (externalId, refId), unique=true)
    /** Index over (name) (database name name) */
    val index2 = index("name", name)
  }
  /** Collection-like TableQuery object for table Tissues */
  lazy val Tissues = new TableQuery(tag => new Tissues(tag))

  /** Entity class storing rows of table TransferPlates
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param name Database column name SqlType(VARCHAR), Length(100,true)
   *  @param description Database column description SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param plateTypeId Database column plate_type_id SqlType(TINYINT UNSIGNED)
   *  @param supplierId Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param parentId Database column parent_id SqlType(SMALLINT UNSIGNED), Default(None)
   *  @param dilutionFactorFromParent Database column dilution_factor_from_parent SqlType(DOUBLE UNSIGNED), Default(None)
   *  @param initialUlPerWell Database column initial_ul_per_well SqlType(DOUBLE UNSIGNED)
   *  @param creatorId Database column creator_id SqlType(SMALLINT UNSIGNED)
   *  @param datetimeCreated Database column datetime_created SqlType(DATETIME)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class TransferPlatesRow(id: Int, name: String, description: Option[String] = None, plateTypeId: Byte, supplierId: Option[Int] = None, parentId: Option[Int] = None, dilutionFactorFromParent: Option[Double] = None, initialUlPerWell: Double, creatorId: Int, datetimeCreated: java.sql.Timestamp, created: java.sql.Timestamp)
  /** GetResult implicit for fetching TransferPlatesRow objects using plain SQL queries */
  implicit def GetResultTransferPlatesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Byte], e4: GR[Option[Int]], e5: GR[Option[Double]], e6: GR[Double], e7: GR[java.sql.Timestamp]): GR[TransferPlatesRow] = GR{
    prs => import prs._
    TransferPlatesRow.tupled((<<[Int], <<[String], <<?[String], <<[Byte], <<?[Int], <<?[Int], <<?[Double], <<[Double], <<[Int], <<[java.sql.Timestamp], <<[java.sql.Timestamp]))
  }
  /** Table description of table transfer_plates. Objects of this class serve as prototypes for rows in queries. */
  class TransferPlates(_tableTag: Tag) extends profile.api.Table[TransferPlatesRow](_tableTag, Some("valar"), "transfer_plates") {
    def * = (id, name, description, plateTypeId, supplierId, parentId, dilutionFactorFromParent, initialUlPerWell, creatorId, datetimeCreated, created) <> (TransferPlatesRow.tupled, TransferPlatesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(name), description, Rep.Some(plateTypeId), supplierId, parentId, dilutionFactorFromParent, Rep.Some(initialUlPerWell), Rep.Some(creatorId), Rep.Some(datetimeCreated), Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> TransferPlatesRow.tupled((_1.get, _2.get, _3, _4.get, _5, _6, _7, _8.get, _9.get, _10.get, _11.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column name SqlType(VARCHAR), Length(100,true) */
    val name: Rep[String] = column[String]("name", O.Length(100,varying=true))
    /** Database column description SqlType(VARCHAR), Length(250,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(250,varying=true), O.Default(None))
    /** Database column plate_type_id SqlType(TINYINT UNSIGNED) */
    val plateTypeId: Rep[Byte] = column[Byte]("plate_type_id")
    /** Database column supplier_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val supplierId: Rep[Option[Int]] = column[Option[Int]]("supplier_id", O.Default(None))
    /** Database column parent_id SqlType(SMALLINT UNSIGNED), Default(None) */
    val parentId: Rep[Option[Int]] = column[Option[Int]]("parent_id", O.Default(None))
    /** Database column dilution_factor_from_parent SqlType(DOUBLE UNSIGNED), Default(None) */
    val dilutionFactorFromParent: Rep[Option[Double]] = column[Option[Double]]("dilution_factor_from_parent", O.Default(None))
    /** Database column initial_ul_per_well SqlType(DOUBLE UNSIGNED) */
    val initialUlPerWell: Rep[Double] = column[Double]("initial_ul_per_well")
    /** Database column creator_id SqlType(SMALLINT UNSIGNED) */
    val creatorId: Rep[Int] = column[Int]("creator_id")
    /** Database column datetime_created SqlType(DATETIME) */
    val datetimeCreated: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("datetime_created")
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing PlateTypes (database name transfer_plate_to_plate_type) */
    lazy val plateTypesFk = foreignKey("transfer_plate_to_plate_type", plateTypeId, PlateTypes)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Suppliers (database name transfer_plate_to_supplier) */
    lazy val suppliersFk = foreignKey("transfer_plate_to_supplier", supplierId, Suppliers)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing TransferPlates (database name transfer_plate_to_parent) */
    lazy val transferPlatesFk = foreignKey("transfer_plate_to_parent", parentId, TransferPlates)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Users (database name transfer_plate_to_creator) */
    lazy val usersFk = foreignKey("transfer_plate_to_creator", creatorId, Users)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)

    /** Uniqueness Index over (name) (database name name_unique) */
    val index1 = index("name_unique", name, unique=true)
  }
  /** Collection-like TableQuery object for table TransferPlates */
  lazy val TransferPlates = new TableQuery(tag => new TransferPlates(tag))

  /** Entity class storing rows of table Users
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey
   *  @param username Database column username SqlType(VARCHAR), Length(20,true)
   *  @param firstName Database column first_name SqlType(VARCHAR), Length(30,true)
   *  @param lastName Database column last_name SqlType(VARCHAR), Length(30,true)
   *  @param writeAccess Database column write_access SqlType(BIT), Default(true)
   *  @param bcryptHash Database column bcrypt_hash SqlType(CHAR), Length(60,false), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class UsersRow(id: Int, username: String, firstName: String, lastName: String, writeAccess: Boolean = true, bcryptHash: Option[String] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching UsersRow objects using plain SQL queries */
  implicit def GetResultUsersRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Boolean], e3: GR[Option[String]], e4: GR[java.sql.Timestamp]): GR[UsersRow] = GR{
    prs => import prs._
    UsersRow.tupled((<<[Int], <<[String], <<[String], <<[String], <<[Boolean], <<?[String], <<[java.sql.Timestamp]))
  }
  /** Table description of table users. Objects of this class serve as prototypes for rows in queries. */
  class Users(_tableTag: Tag) extends profile.api.Table[UsersRow](_tableTag, Some("valar"), "users") {
    def * = (id, username, firstName, lastName, writeAccess, bcryptHash, created) <> (UsersRow.tupled, UsersRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(username), Rep.Some(firstName), Rep.Some(lastName), Rep.Some(writeAccess), bcryptHash, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> UsersRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get, _6, _7.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column username SqlType(VARCHAR), Length(20,true) */
    val username: Rep[String] = column[String]("username", O.Length(20,varying=true))
    /** Database column first_name SqlType(VARCHAR), Length(30,true) */
    val firstName: Rep[String] = column[String]("first_name", O.Length(30,varying=true))
    /** Database column last_name SqlType(VARCHAR), Length(30,true) */
    val lastName: Rep[String] = column[String]("last_name", O.Length(30,varying=true))
    /** Database column write_access SqlType(BIT), Default(true) */
    val writeAccess: Rep[Boolean] = column[Boolean]("write_access", O.Default(true))
    /** Database column bcrypt_hash SqlType(CHAR), Length(60,false), Default(None) */
    val bcryptHash: Rep[Option[String]] = column[Option[String]]("bcrypt_hash", O.Length(60,varying=false), O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Index over (bcryptHash) (database name bcrypt_hash) */
    val index1 = index("bcrypt_hash", bcryptHash)
    /** Index over (firstName) (database name first_name) */
    val index2 = index("first_name", firstName)
    /** Index over (lastName) (database name last_name) */
    val index3 = index("last_name", lastName)
    /** Uniqueness Index over (username) (database name username_unique) */
    val index4 = index("username_unique", username, unique=true)
    /** Index over (writeAccess) (database name write_access) */
    val index5 = index("write_access", writeAccess)
  }
  /** Collection-like TableQuery object for table Users */
  lazy val Users = new TableQuery(tag => new Users(tag))

  /** Entity class storing rows of table VAnnotations
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), Default(0)
   *  @param name Database column name SqlType(VARCHAR), Length(255,true), Default(None)
   *  @param value Database column value SqlType(VARCHAR), Length(255,true), Default(None)
   *  @param level Database column level SqlType(ENUM), Length(9,false), Default(1:note)
   *  @param run Database column run SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param submission Database column submission SqlType(CHAR), Length(12,false), Default(None)
   *  @param wellId Database column well_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param assay Database column assay SqlType(VARCHAR), Length(250,true), Default(None)
   *  @param annotator Database column annotator SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param description Database column description SqlType(MEDIUMTEXT), Length(16777215,true), Default(None)
   *  @param date Database column date SqlType(VARCHAR), Length(19,true), Default(None)
   *  @param time Database column time SqlType(VARCHAR), Length(19,true), Default(None) */
  case class VAnnotationsRow(id: Int = 0, name: Option[String] = None, value: Option[String] = None, level: String = "1:note", run: Option[String] = None, submission: Option[String] = None, wellId: Option[Int] = None, assay: Option[String] = None, annotator: Option[String] = None, description: Option[String] = None, date: Option[String] = None, time: Option[String] = None)
  /** GetResult implicit for fetching VAnnotationsRow objects using plain SQL queries */
  implicit def GetResultVAnnotationsRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[String], e3: GR[Option[Int]]): GR[VAnnotationsRow] = GR{
    prs => import prs._
    VAnnotationsRow.tupled((<<[Int], <<?[String], <<?[String], <<[String], <<?[String], <<?[String], <<?[Int], <<?[String], <<?[String], <<?[String], <<?[String], <<?[String]))
  }
  /** Table description of table v_annotations. Objects of this class serve as prototypes for rows in queries. */
  class VAnnotations(_tableTag: Tag) extends profile.api.Table[VAnnotationsRow](_tableTag, Some("valar"), "v_annotations") {
    def * = (id, name, value, level, run, submission, wellId, assay, annotator, description, date, time) <> (VAnnotationsRow.tupled, VAnnotationsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), name, value, Rep.Some(level), run, submission, wellId, assay, annotator, description, date, time).shaped.<>({r=>import r._; _1.map(_=> VAnnotationsRow.tupled((_1.get, _2, _3, _4.get, _5, _6, _7, _8, _9, _10, _11, _12)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), Default(0) */
    val id: Rep[Int] = column[Int]("id", O.Default(0))
    /** Database column name SqlType(VARCHAR), Length(255,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(255,varying=true), O.Default(None))
    /** Database column value SqlType(VARCHAR), Length(255,true), Default(None) */
    val value: Rep[Option[String]] = column[Option[String]]("value", O.Length(255,varying=true), O.Default(None))
    /** Database column level SqlType(ENUM), Length(9,false), Default(1:note) */
    val level: Rep[String] = column[String]("level", O.Length(9,varying=false), O.Default("1:note"))
    /** Database column run SqlType(VARCHAR), Length(100,true), Default(None) */
    val run: Rep[Option[String]] = column[Option[String]]("run", O.Length(100,varying=true), O.Default(None))
    /** Database column submission SqlType(CHAR), Length(12,false), Default(None) */
    val submission: Rep[Option[String]] = column[Option[String]]("submission", O.Length(12,varying=false), O.Default(None))
    /** Database column well_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val wellId: Rep[Option[Int]] = column[Option[Int]]("well_id", O.Default(None))
    /** Database column assay SqlType(VARCHAR), Length(250,true), Default(None) */
    val assay: Rep[Option[String]] = column[Option[String]]("assay", O.Length(250,varying=true), O.Default(None))
    /** Database column annotator SqlType(VARCHAR), Length(20,true), Default(None) */
    val annotator: Rep[Option[String]] = column[Option[String]]("annotator", O.Length(20,varying=true), O.Default(None))
    /** Database column description SqlType(MEDIUMTEXT), Length(16777215,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(16777215,varying=true), O.Default(None))
    /** Database column date SqlType(VARCHAR), Length(19,true), Default(None) */
    val date: Rep[Option[String]] = column[Option[String]]("date", O.Length(19,varying=true), O.Default(None))
    /** Database column time SqlType(VARCHAR), Length(19,true), Default(None) */
    val time: Rep[Option[String]] = column[Option[String]]("time", O.Length(19,varying=true), O.Default(None))
  }
  /** Collection-like TableQuery object for table VAnnotations */
  lazy val VAnnotations = new TableQuery(tag => new VAnnotations(tag))

  /** Entity class storing rows of table VExperiments
   *  @param id Database column id SqlType(SMALLINT UNSIGNED), Default(0)
   *  @param experiment Database column experiment SqlType(VARCHAR), Length(200,true)
   *  @param description Database column description SqlType(VARCHAR), Length(10000,true), Default(None)
   *  @param creator Database column creator SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param project Database column project SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param battery Database column battery SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param templatePlate Database column template_plate SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param transferPlate Database column transfer_plate SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param defaultAcclimationSec Database column default_acclimation_sec SqlType(SMALLINT UNSIGNED)
   *  @param notes Database column notes SqlType(TEXT), Default(None)
   *  @param active Database column active SqlType(BIT), Default(true)
   *  @param date Database column date SqlType(VARCHAR), Length(19,true), Default(None)
   *  @param time Database column time SqlType(VARCHAR), Length(19,true), Default(None) */
  case class VExperimentsRow(id: Int = 0, experiment: String, description: Option[String] = None, creator: Option[String] = None, project: Option[String] = None, battery: Option[String] = None, templatePlate: Option[String] = None, transferPlate: Option[String] = None, defaultAcclimationSec: Int, notes: Option[String] = None, active: Boolean = true, date: Option[String] = None, time: Option[String] = None)
  /** GetResult implicit for fetching VExperimentsRow objects using plain SQL queries */
  implicit def GetResultVExperimentsRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Boolean]): GR[VExperimentsRow] = GR{
    prs => import prs._
    VExperimentsRow.tupled((<<[Int], <<[String], <<?[String], <<?[String], <<?[String], <<?[String], <<?[String], <<?[String], <<[Int], <<?[String], <<[Boolean], <<?[String], <<?[String]))
  }
  /** Table description of table v_experiments. Objects of this class serve as prototypes for rows in queries. */
  class VExperiments(_tableTag: Tag) extends profile.api.Table[VExperimentsRow](_tableTag, Some("valar"), "v_experiments") {
    def * = (id, experiment, description, creator, project, battery, templatePlate, transferPlate, defaultAcclimationSec, notes, active, date, time) <> (VExperimentsRow.tupled, VExperimentsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(experiment), description, creator, project, battery, templatePlate, transferPlate, Rep.Some(defaultAcclimationSec), notes, Rep.Some(active), date, time).shaped.<>({r=>import r._; _1.map(_=> VExperimentsRow.tupled((_1.get, _2.get, _3, _4, _5, _6, _7, _8, _9.get, _10, _11.get, _12, _13)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(SMALLINT UNSIGNED), Default(0) */
    val id: Rep[Int] = column[Int]("id", O.Default(0))
    /** Database column experiment SqlType(VARCHAR), Length(200,true) */
    val experiment: Rep[String] = column[String]("experiment", O.Length(200,varying=true))
    /** Database column description SqlType(VARCHAR), Length(10000,true), Default(None) */
    val description: Rep[Option[String]] = column[Option[String]]("description", O.Length(10000,varying=true), O.Default(None))
    /** Database column creator SqlType(VARCHAR), Length(20,true), Default(None) */
    val creator: Rep[Option[String]] = column[Option[String]]("creator", O.Length(20,varying=true), O.Default(None))
    /** Database column project SqlType(VARCHAR), Length(100,true), Default(None) */
    val project: Rep[Option[String]] = column[Option[String]]("project", O.Length(100,varying=true), O.Default(None))
    /** Database column battery SqlType(VARCHAR), Length(100,true), Default(None) */
    val battery: Rep[Option[String]] = column[Option[String]]("battery", O.Length(100,varying=true), O.Default(None))
    /** Database column template_plate SqlType(VARCHAR), Length(100,true), Default(None) */
    val templatePlate: Rep[Option[String]] = column[Option[String]]("template_plate", O.Length(100,varying=true), O.Default(None))
    /** Database column transfer_plate SqlType(VARCHAR), Length(100,true), Default(None) */
    val transferPlate: Rep[Option[String]] = column[Option[String]]("transfer_plate", O.Length(100,varying=true), O.Default(None))
    /** Database column default_acclimation_sec SqlType(SMALLINT UNSIGNED) */
    val defaultAcclimationSec: Rep[Int] = column[Int]("default_acclimation_sec")
    /** Database column notes SqlType(TEXT), Default(None) */
    val notes: Rep[Option[String]] = column[Option[String]]("notes", O.Default(None))
    /** Database column active SqlType(BIT), Default(true) */
    val active: Rep[Boolean] = column[Boolean]("active", O.Default(true))
    /** Database column date SqlType(VARCHAR), Length(19,true), Default(None) */
    val date: Rep[Option[String]] = column[Option[String]]("date", O.Length(19,varying=true), O.Default(None))
    /** Database column time SqlType(VARCHAR), Length(19,true), Default(None) */
    val time: Rep[Option[String]] = column[Option[String]]("time", O.Length(19,varying=true), O.Default(None))
  }
  /** Collection-like TableQuery object for table VExperiments */
  lazy val VExperiments = new TableQuery(tag => new VExperiments(tag))

  /** Entity class storing rows of table VMandosRules
   *  @param id Database column id SqlType(INT UNSIGNED), Default(0)
   *  @param ref Database column ref SqlType(VARCHAR), Length(50,true)
   *  @param compoundId Database column compound_id SqlType(MEDIUMINT UNSIGNED)
   *  @param chemblId Database column chembl_id SqlType(VARCHAR), Length(20,true), Default(None)
   *  @param predicateId Database column predicate_id SqlType(TINYINT UNSIGNED), Default(0)
   *  @param predicate Database column predicate SqlType(VARCHAR), Length(250,true)
   *  @param objId Database column obj_id SqlType(MEDIUMINT UNSIGNED), Default(0)
   *  @param obj Database column obj SqlType(VARCHAR), Length(250,true)
   *  @param objName Database column obj_name SqlType(VARCHAR), Length(250,true), Default(None) */
  case class VMandosRulesRow(id: Int = 0, ref: String, compoundId: Int, chemblId: Option[String] = None, predicateId: Byte = 0, predicate: String, objId: Int = 0, obj: String, objName: Option[String] = None)
  /** GetResult implicit for fetching VMandosRulesRow objects using plain SQL queries */
  implicit def GetResultVMandosRulesRow(implicit e0: GR[Int], e1: GR[String], e2: GR[Option[String]], e3: GR[Byte]): GR[VMandosRulesRow] = GR{
    prs => import prs._
    VMandosRulesRow.tupled((<<[Int], <<[String], <<[Int], <<?[String], <<[Byte], <<[String], <<[Int], <<[String], <<?[String]))
  }
  /** Table description of table v_mandos_rules. Objects of this class serve as prototypes for rows in queries. */
  class VMandosRules(_tableTag: Tag) extends profile.api.Table[VMandosRulesRow](_tableTag, Some("valar"), "v_mandos_rules") {
    def * = (id, ref, compoundId, chemblId, predicateId, predicate, objId, obj, objName) <> (VMandosRulesRow.tupled, VMandosRulesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(ref), Rep.Some(compoundId), chemblId, Rep.Some(predicateId), Rep.Some(predicate), Rep.Some(objId), Rep.Some(obj), objName).shaped.<>({r=>import r._; _1.map(_=> VMandosRulesRow.tupled((_1.get, _2.get, _3.get, _4, _5.get, _6.get, _7.get, _8.get, _9)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), Default(0) */
    val id: Rep[Int] = column[Int]("id", O.Default(0))
    /** Database column ref SqlType(VARCHAR), Length(50,true) */
    val ref: Rep[String] = column[String]("ref", O.Length(50,varying=true))
    /** Database column compound_id SqlType(MEDIUMINT UNSIGNED) */
    val compoundId: Rep[Int] = column[Int]("compound_id")
    /** Database column chembl_id SqlType(VARCHAR), Length(20,true), Default(None) */
    val chemblId: Rep[Option[String]] = column[Option[String]]("chembl_id", O.Length(20,varying=true), O.Default(None))
    /** Database column predicate_id SqlType(TINYINT UNSIGNED), Default(0) */
    val predicateId: Rep[Byte] = column[Byte]("predicate_id", O.Default(0))
    /** Database column predicate SqlType(VARCHAR), Length(250,true) */
    val predicate: Rep[String] = column[String]("predicate", O.Length(250,varying=true))
    /** Database column obj_id SqlType(MEDIUMINT UNSIGNED), Default(0) */
    val objId: Rep[Int] = column[Int]("obj_id", O.Default(0))
    /** Database column obj SqlType(VARCHAR), Length(250,true) */
    val obj: Rep[String] = column[String]("obj", O.Length(250,varying=true))
    /** Database column obj_name SqlType(VARCHAR), Length(250,true), Default(None) */
    val objName: Rep[Option[String]] = column[Option[String]]("obj_name", O.Length(250,varying=true), O.Default(None))
  }
  /** Collection-like TableQuery object for table VMandosRules */
  lazy val VMandosRules = new TableQuery(tag => new VMandosRules(tag))

  /** Entity class storing rows of table VRuns
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), Default(0)
   *  @param name Database column name SqlType(VARCHAR), Length(100,true), Default(None)
   *  @param submission Database column submission SqlType(CHAR), Length(12,false), Default(None)
   *  @param description Database column description SqlType(VARCHAR), Length(200,true)
   *  @param experiment Database column experiment SqlType(VARCHAR), Length(200,true)
   *  @param date Database column date SqlType(DATE), Default(None)
   *  @param timeRun Database column time_run SqlType(TIME), Default(None)
   *  @param timeDosed Database column time_dosed SqlType(TIME), Default(None)
   *  @param timePlated Database column time_plated SqlType(TIME), Default(None)
   *  @param incubation Database column incubation SqlType(TIME), Default(None) */
  case class VRunsRow(id: Int = 0, name: Option[String] = None, submission: Option[String] = None, description: String, experiment: String, date: Option[java.sql.Date] = None, timeRun: Option[java.sql.Time] = None, timeDosed: Option[java.sql.Time] = None, timePlated: Option[java.sql.Time] = None, incubation: Option[java.sql.Time] = None)
  /** GetResult implicit for fetching VRunsRow objects using plain SQL queries */
  implicit def GetResultVRunsRow(implicit e0: GR[Int], e1: GR[Option[String]], e2: GR[String], e3: GR[Option[java.sql.Date]], e4: GR[Option[java.sql.Time]]): GR[VRunsRow] = GR{
    prs => import prs._
    VRunsRow.tupled((<<[Int], <<?[String], <<?[String], <<[String], <<[String], <<?[java.sql.Date], <<?[java.sql.Time], <<?[java.sql.Time], <<?[java.sql.Time], <<?[java.sql.Time]))
  }
  /** Table description of table v_runs. Objects of this class serve as prototypes for rows in queries. */
  class VRuns(_tableTag: Tag) extends profile.api.Table[VRunsRow](_tableTag, Some("valar"), "v_runs") {
    def * = (id, name, submission, description, experiment, date, timeRun, timeDosed, timePlated, incubation) <> (VRunsRow.tupled, VRunsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), name, submission, Rep.Some(description), Rep.Some(experiment), date, timeRun, timeDosed, timePlated, incubation).shaped.<>({r=>import r._; _1.map(_=> VRunsRow.tupled((_1.get, _2, _3, _4.get, _5.get, _6, _7, _8, _9, _10)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), Default(0) */
    val id: Rep[Int] = column[Int]("id", O.Default(0))
    /** Database column name SqlType(VARCHAR), Length(100,true), Default(None) */
    val name: Rep[Option[String]] = column[Option[String]]("name", O.Length(100,varying=true), O.Default(None))
    /** Database column submission SqlType(CHAR), Length(12,false), Default(None) */
    val submission: Rep[Option[String]] = column[Option[String]]("submission", O.Length(12,varying=false), O.Default(None))
    /** Database column description SqlType(VARCHAR), Length(200,true) */
    val description: Rep[String] = column[String]("description", O.Length(200,varying=true))
    /** Database column experiment SqlType(VARCHAR), Length(200,true) */
    val experiment: Rep[String] = column[String]("experiment", O.Length(200,varying=true))
    /** Database column date SqlType(DATE), Default(None) */
    val date: Rep[Option[java.sql.Date]] = column[Option[java.sql.Date]]("date", O.Default(None))
    /** Database column time_run SqlType(TIME), Default(None) */
    val timeRun: Rep[Option[java.sql.Time]] = column[Option[java.sql.Time]]("time_run", O.Default(None))
    /** Database column time_dosed SqlType(TIME), Default(None) */
    val timeDosed: Rep[Option[java.sql.Time]] = column[Option[java.sql.Time]]("time_dosed", O.Default(None))
    /** Database column time_plated SqlType(TIME), Default(None) */
    val timePlated: Rep[Option[java.sql.Time]] = column[Option[java.sql.Time]]("time_plated", O.Default(None))
    /** Database column incubation SqlType(TIME), Default(None) */
    val incubation: Rep[Option[java.sql.Time]] = column[Option[java.sql.Time]]("incubation", O.Default(None))
  }
  /** Collection-like TableQuery object for table VRuns */
  lazy val VRuns = new TableQuery(tag => new VRuns(tag))

  /** Entity class storing rows of table WellFeatures
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param wellId Database column well_id SqlType(MEDIUMINT UNSIGNED)
   *  @param typeId Database column type_id SqlType(TINYINT UNSIGNED)
   *  @param floats Database column floats SqlType(LONGBLOB)
   *  @param sha1 Database column sha1 SqlType(BINARY) */
  case class WellFeaturesRow(id: Int, wellId: Int, typeId: Byte, floats: java.sql.Blob, sha1: java.sql.Blob)
  /** GetResult implicit for fetching WellFeaturesRow objects using plain SQL queries */
  implicit def GetResultWellFeaturesRow(implicit e0: GR[Int], e1: GR[Byte], e2: GR[java.sql.Blob]): GR[WellFeaturesRow] = GR{
    prs => import prs._
    WellFeaturesRow.tupled((<<[Int], <<[Int], <<[Byte], <<[java.sql.Blob], <<[java.sql.Blob]))
  }
  /** Table description of table well_features. Objects of this class serve as prototypes for rows in queries. */
  class WellFeatures(_tableTag: Tag) extends profile.api.Table[WellFeaturesRow](_tableTag, Some("valar"), "well_features") {
    def * = (id, wellId, typeId, floats, sha1) <> (WellFeaturesRow.tupled, WellFeaturesRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(wellId), Rep.Some(typeId), Rep.Some(floats), Rep.Some(sha1)).shaped.<>({r=>import r._; _1.map(_=> WellFeaturesRow.tupled((_1.get, _2.get, _3.get, _4.get, _5.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column well_id SqlType(MEDIUMINT UNSIGNED) */
    val wellId: Rep[Int] = column[Int]("well_id")
    /** Database column type_id SqlType(TINYINT UNSIGNED) */
    val typeId: Rep[Byte] = column[Byte]("type_id")
    /** Database column floats SqlType(LONGBLOB) */
    val floats: Rep[java.sql.Blob] = column[java.sql.Blob]("floats")
    /** Database column sha1 SqlType(BINARY) */
    val sha1: Rep[java.sql.Blob] = column[java.sql.Blob]("sha1")

    /** Foreign key referencing Features (database name well_feature_to_type) */
    lazy val featuresFk = foreignKey("well_feature_to_type", typeId, Features)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Wells (database name well_feature_to_well) */
    lazy val wellsFk = foreignKey("well_feature_to_well", wellId, Wells)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (sha1) (database name sha1) */
    val index1 = index("sha1", sha1)
  }
  /** Collection-like TableQuery object for table WellFeatures */
  lazy val WellFeatures = new TableQuery(tag => new WellFeatures(tag))

  /** Entity class storing rows of table Wells
   *  @param id Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey
   *  @param runId Database column run_id SqlType(MEDIUMINT UNSIGNED)
   *  @param wellIndex Database column well_index SqlType(SMALLINT UNSIGNED)
   *  @param controlTypeId Database column control_type_id SqlType(TINYINT UNSIGNED), Default(None)
   *  @param variantId Database column variant_id SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param wellGroup Database column well_group SqlType(VARCHAR), Length(50,true), Default(None)
   *  @param n Database column n SqlType(MEDIUMINT), Default(0)
   *  @param age Database column age SqlType(MEDIUMINT UNSIGNED), Default(None)
   *  @param created Database column created SqlType(TIMESTAMP) */
  case class WellsRow(id: Int, runId: Int, wellIndex: Int, controlTypeId: Option[Byte] = None, variantId: Option[Int] = None, wellGroup: Option[String] = None, n: Int = 0, age: Option[Int] = None, created: java.sql.Timestamp)
  /** GetResult implicit for fetching WellsRow objects using plain SQL queries */
  implicit def GetResultWellsRow(implicit e0: GR[Int], e1: GR[Option[Byte]], e2: GR[Option[Int]], e3: GR[Option[String]], e4: GR[java.sql.Timestamp]): GR[WellsRow] = GR{
    prs => import prs._
    WellsRow.tupled((<<[Int], <<[Int], <<[Int], <<?[Byte], <<?[Int], <<?[String], <<[Int], <<?[Int], <<[java.sql.Timestamp]))
  }
  /** Table description of table wells. Objects of this class serve as prototypes for rows in queries. */
  class Wells(_tableTag: Tag) extends profile.api.Table[WellsRow](_tableTag, Some("valar"), "wells") {
    def * = (id, runId, wellIndex, controlTypeId, variantId, wellGroup, n, age, created) <> (WellsRow.tupled, WellsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(runId), Rep.Some(wellIndex), controlTypeId, variantId, wellGroup, Rep.Some(n), age, Rep.Some(created)).shaped.<>({r=>import r._; _1.map(_=> WellsRow.tupled((_1.get, _2.get, _3.get, _4, _5, _6, _7.get, _8, _9.get)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(MEDIUMINT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column run_id SqlType(MEDIUMINT UNSIGNED) */
    val runId: Rep[Int] = column[Int]("run_id")
    /** Database column well_index SqlType(SMALLINT UNSIGNED) */
    val wellIndex: Rep[Int] = column[Int]("well_index")
    /** Database column control_type_id SqlType(TINYINT UNSIGNED), Default(None) */
    val controlTypeId: Rep[Option[Byte]] = column[Option[Byte]]("control_type_id", O.Default(None))
    /** Database column variant_id SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val variantId: Rep[Option[Int]] = column[Option[Int]]("variant_id", O.Default(None))
    /** Database column well_group SqlType(VARCHAR), Length(50,true), Default(None) */
    val wellGroup: Rep[Option[String]] = column[Option[String]]("well_group", O.Length(50,varying=true), O.Default(None))
    /** Database column n SqlType(MEDIUMINT), Default(0) */
    val n: Rep[Int] = column[Int]("n", O.Default(0))
    /** Database column age SqlType(MEDIUMINT UNSIGNED), Default(None) */
    val age: Rep[Option[Int]] = column[Option[Int]]("age", O.Default(None))
    /** Database column created SqlType(TIMESTAMP) */
    val created: Rep[java.sql.Timestamp] = column[java.sql.Timestamp]("created")

    /** Foreign key referencing ControlTypes (database name well_to_control_type) */
    lazy val controlTypesFk = foreignKey("well_to_control_type", controlTypeId, ControlTypes)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing GeneticVariants (database name well_to_fish_variant) */
    lazy val geneticVariantsFk = foreignKey("well_to_fish_variant", variantId, GeneticVariants)(r => Rep.Some(r.id), onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Runs (database name well_to_run) */
    lazy val runsFk = foreignKey("well_to_run", runId, Runs)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Index over (n) (database name approx_n_fish) */
    val index1 = index("approx_n_fish", n)
    /** Uniqueness Index over (runId,wellIndex) (database name plate_well_index_unique) */
    val index2 = index("plate_well_index_unique", (runId, wellIndex), unique=true)
    /** Index over (wellGroup) (database name well_group) */
    val index3 = index("well_group", wellGroup)
    /** Index over (wellIndex) (database name well_index) */
    val index4 = index("well_index", wellIndex)
  }
  /** Collection-like TableQuery object for table Wells */
  lazy val Wells = new TableQuery(tag => new Wells(tag))

  /** Entity class storing rows of table WellTreatments
   *  @param id Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey
   *  @param wellId Database column well_id SqlType(MEDIUMINT UNSIGNED)
   *  @param batchId Database column batch_id SqlType(MEDIUMINT UNSIGNED)
   *  @param micromolarDose Database column micromolar_dose SqlType(DOUBLE UNSIGNED), Default(None) */
  case class WellTreatmentsRow(id: Int, wellId: Int, batchId: Int, micromolarDose: Option[Double] = None)
  /** GetResult implicit for fetching WellTreatmentsRow objects using plain SQL queries */
  implicit def GetResultWellTreatmentsRow(implicit e0: GR[Int], e1: GR[Option[Double]]): GR[WellTreatmentsRow] = GR{
    prs => import prs._
    WellTreatmentsRow.tupled((<<[Int], <<[Int], <<[Int], <<?[Double]))
  }
  /** Table description of table well_treatments. Objects of this class serve as prototypes for rows in queries. */
  class WellTreatments(_tableTag: Tag) extends profile.api.Table[WellTreatmentsRow](_tableTag, Some("valar"), "well_treatments") {
    def * = (id, wellId, batchId, micromolarDose) <> (WellTreatmentsRow.tupled, WellTreatmentsRow.unapply)
    /** Maps whole row to an option. Useful for outer joins. */
    def ? = (Rep.Some(id), Rep.Some(wellId), Rep.Some(batchId), micromolarDose).shaped.<>({r=>import r._; _1.map(_=> WellTreatmentsRow.tupled((_1.get, _2.get, _3.get, _4)))}, (_:Any) =>  throw new Exception("Inserting into ? projection not supported."))

    /** Database column id SqlType(INT UNSIGNED), AutoInc, PrimaryKey */
    val id: Rep[Int] = column[Int]("id", O.AutoInc, O.PrimaryKey)
    /** Database column well_id SqlType(MEDIUMINT UNSIGNED) */
    val wellId: Rep[Int] = column[Int]("well_id")
    /** Database column batch_id SqlType(MEDIUMINT UNSIGNED) */
    val batchId: Rep[Int] = column[Int]("batch_id")
    /** Database column micromolar_dose SqlType(DOUBLE UNSIGNED), Default(None) */
    val micromolarDose: Rep[Option[Double]] = column[Option[Double]]("micromolar_dose", O.Default(None))

    /** Foreign key referencing Batches (database name well_treatment_to_ordered_compound) */
    lazy val batchesFk = foreignKey("well_treatment_to_ordered_compound", batchId, Batches)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.NoAction)
    /** Foreign key referencing Wells (database name well_treatment_to_well) */
    lazy val wellsFk = foreignKey("well_treatment_to_well", wellId, Wells)(r => r.id, onUpdate=ForeignKeyAction.NoAction, onDelete=ForeignKeyAction.Cascade)

    /** Uniqueness Index over (wellId,batchId) (database name well_id) */
    val index1 = index("well_id", (wellId, batchId), unique=true)
  }
  /** Collection-like TableQuery object for table WellTreatments */
  lazy val WellTreatments = new TableQuery(tag => new WellTreatments(tag))
}
