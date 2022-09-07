package valar.core

import com.typesafe.scalalogging.Logger
import slick.jdbc.JdbcBackend.Database

import java.util.Locale

object CommonQueries {

  val logger: Logger = Logger(getClass)
  implicit val db: Database = loadDb()
  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def nPlates: Int = exec(Plates.length.result)
  def nProjects: Int = exec(Experiments.length.result)
  def nCompounds: Int = exec(Compounds.length.result)
  def nOrderedCompounds: Int = exec(Batches.length.result)

  def nCompoundsPerDataSource: Map[String, Int] = {
    exec((
      Batches join Refs on (_.refId === _.id)
        groupBy (_._2.name) map (g => (g._1, g._2.size))
      ).result).toMap
  }

  def listCommonSolvents: Seq[(Int, String)] = Seq(
    (1, "water"),
    (2, "DMSO"),
    (3, "methanol"),
    (4, "ethanol")
  )

  def dataSourceIds: Map[String, Int] = (exec((
    Refs map (s => (s.name, s.id))
  ).result) map (s => s._1 -> s._2)).toMap

  def refIds: Map[String, Int] = (exec((
    Refs map (s => (s.name, s.id))
  ).result) map (s => s._1 -> s._2)).toMap
  
  def refNames: Map[Int, String] = dataSourceIds map (e => e._2 -> e._1)
  
  def dataSourceNames: Map[Int, String] = dataSourceIds map (e => e._2 -> e._1)

  def userNames: Map[Int, String] = (listUsers map (u => u.id -> s"${u.firstName} ${u.lastName}")).toMap

  def supplierNames: Map[Int, String] = exec((Suppliers map (r => r.id -> r.name)).result).toMap

  def supplierIds: Map[String, Int] = supplierNames map (cs => cs._2 -> cs._1)

  def batchByHash(string: String): Option[BatchesRow] = exec((Batches filter (_.lookupHash === string)).result).headOption
  def matchingBatch(id: Int): Option[BatchesRow] = exec((Batches filter (_.id === id)).result).headOption
  def matchingCompound(id: Int): Option[CompoundsRow] = exec((Compounds filter (_.id === id)).result).headOption

  def matchingNames(id: Int): Seq[CompoundLabelsRow] = exec((CompoundLabels filter (_.compoundId === id)).result)

  def listDataSources: Seq[RefsRow] = exec(Refs.result)

  // this is huge
  def listBatches: Seq[(BatchesRow, Option[CompoundsRow])] = {
    val q = for {
      (o, c) <- Batches joinLeft Compounds on (_.compoundId === _.id)
    } yield (o, c)
    exec(q.result)
  }

  def listCompoundNames =  exec(CompoundLabels.result)

  def batchesByLowercaseName: Map[String, Seq[(BatchesRow, Option[CompoundsRow])]] = {
    val mp = listBatches filter (_._2.isDefined) groupBy (_._2.get.id)
    listCompoundNames map {compoundName =>
      val ocs = if (mp contains compoundName.compoundId) mp(compoundName.compoundId) else Seq.empty
      compoundName.name.toLowerCase(Locale.ENGLISH) -> ocs
    }
  }.toMap

  def listCompoundSources: Seq[SuppliersRow] = exec(Suppliers.result)

  def listSubmissions: Seq[SubmissionsRow] = exec(Submissions.result)

  def listProjects: Seq[ProjectsRow] = exec(Projects.result)

  def listActiveExperiments: Seq[ExperimentsRow] = exec((Experiments filter (_.active)).result)

  def assayParamsWithAssays: Seq[(AssayParamsRow, AssaysRow)] = {
    val q = for {
      (o, c) <- AssayParams join Assays on (_.assayId === _.id)
    } yield (o, c)
    exec(q.result)
  }

  def listTemplateAssays: Seq[TemplateAssaysRow] = exec(TemplateAssays.result)

  def listTemplateStimulusFrames: Seq[TemplateStimulusFramesRow] = exec(TemplateStimulusFrames.result)

  def listBatteries: Seq[BatteriesRow] = exec(Batteries.result)

  def listAssays: Seq[AssaysRow] = exec(Assays.result)

  def listTemplatePlates: Seq[TemplatePlatesRow] = exec(TemplatePlates.result)

  def listActiveTemplatePlates: Seq[TemplatePlatesRow] = exec((TemplatePlates filter (!_.hidden)).result)

  def listVariants: Seq[GeneticVariantsRow] = exec(GeneticVariants.result)

  def listControlTypes: Seq[ControlTypesRow] = exec(ControlTypes.result)

  def listPlateTypes: Seq[PlateTypesRow] = exec(PlateTypes.result)

  def listTemplateWells: Seq[TemplateWellsRow] = exec(TemplateWells.result)

  def listTemplateTreatments: Seq[TemplateTreatmentsRow] = exec(TemplateTreatments.result)

}
