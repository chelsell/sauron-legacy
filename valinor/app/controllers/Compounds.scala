package controllers

import java.time.format.DateTimeFormatter
import java.util.regex.Pattern

import java.io.File
import javax.inject.Inject
import kokellab.valar.core.DateTimeUtils
import org.openscience.cdk.exception.CDKException
import kokellab.utils.chem.{Chem, Inchi}
import kokellab.utils.core._
import kokellab.utils.webservices.{BasicChemspiderInfo, Chemspider}
import kokellab.valar.core.loadDb
import kokellab.valar.core.CommonQueries
import kokellab.valar.insertion.{CompoundData, CompoundInsertion, CompoundLabelInsertion, ValarChangeException, CompoundLabelData}
import play.api.Logger
import play.api.data.Form
import play.api.data.format.Formats._
import play.api.data.Forms.{number, _}
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}
import play.twirl.api.Html


import scala.util.{Failure, Success, Try}

class Compounds @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._
	import kokellab.valar.core.DateTimeUtils._
	import kokellab.valar.core._


	/******************************************************
	  * views
	  ******************************************************/

	def methodNotAllowed = Action {implicit request =>
		MethodNotAllowed(compoundsView()(request))
	}

	def compounds = Action {implicit request =>
		if (isAuthorized(request)) Ok(compoundsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def compound(cid: Int) = Action {implicit request =>
		if (isAuthorized(request)) {
		    exec((Compounds filter (_.id === cid)).result).headOption map { c =>
			    val compoundNames = CommonQueries.matchingNames(cid)
			    val mandosInfo = exec((MandosInfo filter (_.compoundId === cid)).result)
			    // TODO extremely inefficient
			    val mandosRules = exec((MandosRules filter (_.compoundId === cid)).result)
			    val mandosPredicates = (exec(MandosPredicates.result) map (p => p.id -> p.name)).toMap
			    val mandosObjects = (exec(MandosObjects.result) map (o => o.id -> o.externalId)).toMap
			    val mandosObjectNames = (exec(MandosObjects.result) map (o => o.id -> o.name)).toMap
			    val rules: Seq[(Int, String, String, Option[String])] = mandosRules map { rule => (rule.compoundId, mandosPredicates(rule.predicateId), mandosObjects(rule.objectId), mandosObjectNames(rule.objectId)) }
			    Ok(views.html.compound(c, compoundNames, mandosInfo, rules, CommonQueries.dataSourceNames, username(request), userId(request)))
			} getOrElse Results.NotFound
		} else ErrorRelay.apply(401, username(request))(request)
	}

	def structure(cid: Int) = Action {implicit request =>
		if (isAuthorized(request)) {
			Redirect(s"/assets/images/structures/$cid.svg")
		}
		else ErrorRelay.apply(401, username(request))(request)
	}

	def library(name: String) = Action {implicit request =>
		if (isAuthorized(request)) {
			if (name forall Character.isDigit) {
				val mo = CommonQueries.dataSourceNames.get(name.toInt)
				if (mo.isDefined) {
					Results.Redirect(routes.Compounds.library(mo.get))
				} else {
					Results.NotFound
				}
			} else {
				val id = CommonQueries.dataSourceIds.get(name)
				val results = exec((for {
					(o, c) <- Batches joinLeft Compounds on (_.compoundId === _.id)
					if o.refId === id
				} yield (o, c)).result)
				if (id.isDefined) Ok(views.html.library(name, results, CommonQueries.userNames, CommonQueries.dataSourceNames, CommonQueries.supplierNames, username(request)))
				else Results.NotFound
			}
		}
		else ErrorRelay.apply(401, username(request))(request)
	}

	def compoundById(cid: Int) = Action {implicit request =>
		if (isAuthorized(request)) {
			val results = exec((for {
				(o, c) <- Batches joinLeft Compounds on (_.compoundId === _.id)
				if o.compoundId === cid
			} yield (o, c)).result)
			val cs = exec((Compounds filter (_.id === cid)).result)
			if (cs.nonEmpty) Ok(views.html.library(cid.toString, results, CommonQueries.userNames, CommonQueries.dataSourceNames, CommonQueries.supplierNames, username(request)))
			else Results.NotFound
		}
		else ErrorRelay.apply(401, username(request))(request)
	}

	def search = Action {implicit request => if (isAuthorized(request)) {

		compoundSearchForm.bindFromRequest().fold(
			formWithErrors => BadRequest(compoundsView(searchForm = formWithErrors)(request)),

			txt => {

				val supplierId = CommonQueries.supplierIds.get(txt)
				val matchingUsers = CommonQueries.listUsers filter (u =>
					u.username.toLowerCase == txt.toLowerCase
						|| u.lastName.toLowerCase == txt.toLowerCase
						|| u.firstName.toLowerCase == txt.toLowerCase
						|| s"${u.firstName} ${u.lastName}".toLowerCase == txt.toLowerCase
					) map (_.id)

				val results: Seq[(BatchesRow, Option[CompoundsRow])] = CommonQueries.listBatches filter {case (oc: BatchesRow, c: Option[CompoundsRow]) => (
						c.isDefined && ((c.get.inchikey contains txt) || (c.get.inchi contains txt) || (c.get.smiles.isDefined && (c.get.smiles contains txt)))
						|| c.isDefined && c.get.chemspiderId.isDefined && c.get.chemspiderId.get.toString == txt
						|| c.isDefined && c.get.chemblId.isDefined && c.get.chemblId.get.toString == txt
						|| oc.lookupHash == txt
						|| oc.id.toString == txt
						|| c.isDefined && c.get.id.toString == txt
						|| oc.dateOrdered.isDefined && oc.dateOrdered.get.toLocalDate.format(DateTimeFormatter.ofPattern("YYYY-MM-dd")) == txt
						|| oc.boxNumber.isDefined && (txt == oc.boxNumber.get.toString)
						|| oc.wellNumber.isDefined && (txt == oc.wellNumber.get.toString)
						|| oc.wellNumber.isDefined && oc.boxNumber.isDefined && (txt.count(_ == ',') == 1) && txt.split(",").head == oc.boxNumber.get.toString  && txt.split(",").last == oc.wellNumber.get.toString
						|| oc.supplierId.isDefined && supplierId.isDefined && oc.supplierId.get == supplierId.get
						|| oc.legacyInternalId.isDefined && oc.legacyInternalId.get.toLowerCase == txt.toLowerCase
						|| oc.supplierCatalogNumber.isDefined && oc.supplierCatalogNumber.get.toLowerCase == txt.toLowerCase
						|| oc.personOrdered.isDefined && (matchingUsers contains oc.personOrdered.get)
						|| txt.startsWith("\"") && txt.endsWith("\"") && (
							oc.notes.isDefined && oc.notes.get.toLowerCase.contains(txt.substring(1, txt.length - 1).toLowerCase)
						)
					)}

				val resultsByName: Set[(BatchesRow, Option[CompoundsRow])] = (lookup(txt) map (z => (z._1, Some(z._2)))).toSet
				val resultsByTreatmentName: Set[(BatchesRow, Option[CompoundsRow])] = lookupT(txt).toSet

				Ok(views.html.library(txt, (results ++ resultsByName ++ resultsByTreatmentName).toSeq, CommonQueries.userNames, CommonQueries.dataSourceNames, CommonQueries.supplierNames, username(request)))
			}
		)
	}
	else ErrorRelay.apply(401, username(request))(request)
	}


	private def lookup(name: String): Seq[(BatchesRow, CompoundsRow)] = {
		val byName = exec((CompoundLabels filter (_.name.toLowerCase like s"%${name.toLowerCase}%")).result)
		byName flatMap {n =>
			val q = for {
				(o, c) <- Batches join Compounds on (_.compoundId === _.id)
				if c.id === n.compoundId
			} yield (o, c)
			exec(q.result)
		}
	}


	private def lookupT(name: String): Seq[(BatchesRow, Option[CompoundsRow])] = {
		val byName = exec((BatchLabels filter (_.name.toLowerCase like s"%${name.toLowerCase}%")).result)
		byName flatMap {n =>
			exec((for {
				(o, c) <- Batches joinLeft Compounds on (_.compoundId === _.id)
				if o.id === n.batchId
			} yield (o, c)).result)
		}
	}


	def newCompound = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newCompoundForm.bindFromRequest()
			bound.fold(
				formWithErrors => {
					BadRequest(compoundsView(newForm = formWithErrors)(request))
				},
				data => try {
					val results = insertOc(data)
					Ok(views.html.new_compound(results._1, results._2, "30.0", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(compoundsView(newForm = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def newCompoundLabel = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = compoundLabelForm.bindFromRequest()
			bound.fold(
				formWithErrors => {
					ErrorRelay.apply(400, username(request))(request)
				},
				data => try {
					val results = insertCompoundLabel(data)
					Ok(views.html.success(s"Added compound label ${results.id}", username))
				} catch {
					case e: ValarChangeException =>
						//val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						ErrorRelay.apply(400, username(request))(request)
					case e: Throwable => throw e
				}
			)
		}
	}

	def setConcentration = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			setConcentrationForm.bindFromRequest().fold(
				formWithErrors => {
					ErrorRelay.apply(400, username(request))(request)
				},
				data => {
					// only allow when it's DMSO stocks and the concentration is currently null
					exec((Batches filter (_.id === data.ocId) filter (_.concentrationMillimolar.isEmpty)).result).headOption map { oc =>
						Try(data.concentration.toDouble) map { conc =>
							exec(Batches filter (_.id === data.ocId) map (_.concentrationMillimolar) update Some(conc))
							Ok(views.html.success(s"${data.hash} is ready", username))
						} getOrElse {
							ErrorRelay.apply(400, username(request))(request)
						}
					} getOrElse {
						ErrorRelay.apply(400, username(request))(request)
					}
				}
			)
		}
	}


	def batch(string: String) = Action {implicit request => if (isAuthorized(request)) {
		if (string forall (_.isDigit)) {
			val id = string.toInt
			val oc = CommonQueries.matchingBatch(id)
			if (oc.isDefined) {
				val c = oc.get.compoundId flatMap (compoundId => CommonQueries.matchingCompound(compoundId))
				val bestOc: Option[Int] = if (oc.get.dateOrdered.isDefined && oc.get.boxNumber.isDefined && oc.get.wellNumber.isDefined) {
					val otherOcs: Seq[BatchesRow] = exec((Batches filter (_.dateOrdered.isDefined) filter (_.compoundId === c.map(_.id)) filter (_.boxNumber.isDefined) filter (_.wellNumber.isDefined)).result)
					val highestOcs = (otherOcs filter (_.id != id) sortBy (o => o.dateOrdered.get.toLocalDate.atStartOfDay(DateTimeUtils.dbZone).toEpochSecond)).toList
					if (highestOcs.nonEmpty && highestOcs.last.dateOrdered.isDefined && highestOcs.last.dateOrdered.get.toLocalDate.isAfter(oc.get.dateOrdered.get.toLocalDate)) {
						Some(highestOcs.last.id)
					} else None
				} else None
				val compoundNames = if (oc.get.compoundId.isDefined) CommonQueries.matchingNames(oc.get.compoundId.get) else Seq.empty
				val compoundIds = exec((
					BatchLabels filter (_.batchId === oc.get.id)
				).result)
				val compoundSourceName = oc.get.supplierId map (compoundSourceId => CommonQueries.supplierNames(compoundSourceId))
				val locations = (exec(Locations.result) map (ell => ell.id -> ell.name)).toMap
				val dataSourceName = oc.get.refId map (dataSourceId => CommonQueries.dataSourceNames(dataSourceId))
				val personOrdered = oc.get.personOrdered map (personId => (CommonQueries.listUsers filter (_.id == personId)).head)
				Ok(views.html.batch(oc.get, c, compoundNames, compoundIds, dataSourceName, compoundSourceName, personOrdered, CommonQueries.dataSourceNames, locations, username(request), bestOc))
			} else ErrorRelay.apply(404, username(request))(request)
		} else {
			val id = CommonQueries.batchByHash(string) map (_.id)
			if (id.isDefined) Results.Redirect(routes.Compounds.batch(id.get.toString))
			else ErrorRelay.apply(404, username(request))(request)
		}
	} else ErrorRelay.apply(401, username(request))(request)
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertOc(data: CompoundData): (BatchesRow, Option[CompoundsRow]) = {
		CompoundInsertion.insert(data, 10)
	}

	private def insertCompoundLabel(data: CompoundLabelData): CompoundLabelsRow = {
		CompoundLabelInsertion.insert(data, 10)
	}

	/******************************************************
	  * forms
	  ******************************************************/

	private val compoundSearchForm = Form(
		"text" -> text
	)

	case class ConcentrationData(ocId: Int, hash: String, concentration: Double)

	private val setConcentrationForm = Form(mapping(
		"oc_id" -> number,
		"hash" -> nonEmptyText(14, 14),
		"concentration" -> of(doubleFormat).verifying("Concentration must be nonnegative", c => c >= 0) //nonEmptyText(0, 10)    
	)(ConcentrationData.apply)(ConcentrationData.unapply))

	private val compoundLabelForm = Form(mapping(
		"compound_id" -> number,
		"name" -> nonEmptyText(0, 1000),
		"ref" -> number(0)
	)(CompoundLabelData.apply)(CompoundLabelData.unapply))

	private val newCompoundForm = Form(mapping(
		"is_dry_stock" -> boolean,
		"type" -> nonEmptyText(1, 10),
		"supplier" -> number,
		"catalog_number" -> optional(text(0, 100)),
		"inchi" -> nonEmptyText(1, 2000),
		"date_ordered" -> localDate,
		"box_number" -> optional(number(0)),
		"well_number" -> optional(number(0)),
		"batch_location" -> optional(number(0)),
		"location_note" -> optional(text(0, 50)),
		"amount" -> text(0, 50),
		"made_from" -> optional(text),
		"molecular_weight" -> optional(of(doubleFormat)).verifying("Molecular weight must be nonnegative", c => c forall (_ >= 0)),
		"concentration_micromolar" -> optional(of(doubleFormat)),
		"solvent" -> number,
		"labels_for_structure" -> optional(text(0, 10000)),
		"labels_for_batch" -> optional(text(0, 10000)),
		"notes" -> optional(text(0, 10000)),
		"suspicious" -> boolean,
		"creator" -> number
	)(CompoundData.apply)(CompoundData.unapply))

	private def compoundsView(searchForm: Form[String] = compoundSearchForm, newForm: Form[CompoundData] = newCompoundForm)(implicit request: RequestHeader) = {
		val tubes = exec((Batches filter (_.boxNumber.isDefined) filter (_.wellNumber.isDefined)).result) filter (_.boxNumber.get < 99) filter (_.wellNumber.get < 99) sortBy (tube => (tube.boxNumber, tube.wellNumber))
		val lastBox = tubes.last.boxNumber.get
		val lastWell = tubes.last.wellNumber.get
		val nextTube: (Int, Int) = if (lastWell < 81) (lastBox, (lastWell + 1).toInt) else ((lastBox + 1).toInt, 1)
		views.html.compounds(
			CommonQueries.listBatches filter (occ => (occ._1.refId contains 3) || (occ._1.refId contains 10) || (occ._1.refId contains 1)),
			CommonQueries.listCommonSolvents, CommonQueries.listDataSources, CommonQueries.listCompoundSources, exec(Locations.result) filter (ell => ell.partOf contains 6),
			CommonQueries.nCompounds, CommonQueries.nCompoundsPerDataSource,
			userId(request), username(request), searchForm, newForm, nextTube
		)
	}

	private lazy val inchikeyPattern = Pattern.compile("[A-Z]{14}-[A-Z]{10}-[A-Z]?")
	private lazy val inchikeyConnectivityPattern = Pattern.compile("[A-Z]{14}")
	private lazy val ocPattern = Pattern.compile("oc_[0-9a-z]{11}")

}
