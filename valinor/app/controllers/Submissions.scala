package controllers

import javax.inject.Inject
import kokellab.valar.core.{CommonQueries, DateTimeUtils, exec, loadDb}
import kokellab.valar.insertion.{SubmissionData, SubmissionInsertion, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}

import scala.util.{Failure, Success, Try}

class Submissions @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	/******************************************************
	  * views
	  ******************************************************/

	def methodNotAllowed = Action {implicit request =>
		MethodNotAllowed(submissionsView()(request))
	}

	def submissionHash(hash: String) = Action { implicit request =>
		if (isAuthorized(request)) {
			val found = (CommonQueries.listSubmissions filter (_.lookupHash == hash) map (_.id)).headOption
			if (found.isEmpty) ErrorRelay.apply(404, username(request), message = Some(s"The submission hash $hash does not exist"))(request)
			else {
				val plate = exec((Runs filter (_.submissionId === found) map (_.id)).result).headOption
				if (plate.isDefined) ErrorRelay.apply(404, username(request), message = Some(s"The submission hash $hash exists but was already used for plate ${plate.get}"))(request)
				else Results.Created(views.html.submissionhash(hash, username(request)))
			}
		}
		else ErrorRelay.apply(401, username(request))(request)
	}

	def submissions = Action {implicit request =>
		if (isAuthorized(request)) Ok(submissionsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def _submissions = Action {implicit request =>
		if (isAuthorized(request)) Ok(views.js._submissions(CommonQueries.listActiveExperiments, CommonQueries.listTemplateWells, CommonQueries.listTemplateTreatments))
		else Results.Unauthorized("") // it's better to have an empty JS filter than to insert HTML into the source
	}

	def newSubmission = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = submissionForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(submissionsView(form = formWithErrors)(request)),
				data => try {
					val subHash = insertSubmission(data).lookupHash
					Redirect(s"/newsubmission/$subHash")
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(submissionsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}


	/******************************************************
	  * logic
	  ******************************************************/

	private def insertSubmission(data: SubmissionData): SubmissionsRow = {
		SubmissionInsertion.insert(data)
	}


	/******************************************************
	  * forms
	  ******************************************************/

	private val submissionForm = Form(
		mapping(
			"experiment" -> number,
			"well_parameters" -> text(0, 10000),
			"treatment_parameters" -> text(0, 10000),
			"datetime_plated" -> localDateTime("yyyy-MM-dd'T'HH:mm").verifying("I don’t believe you. You didn’t plate this at exactly midnight.", dt => dt != Utils.midnight),
			"datetime_dosed" -> optional(localDateTime("yyyy-MM-dd'T'HH:mm")).verifying("I don’t believe you. You didn’t dose this at exactly midnight.", dt => !(dt contains Utils.midnight)),
			"acclimation_sec" -> number(0, 60*60*24*365),
			"creator" -> number(1),
			"person_plated" -> number(0),
			"description" -> text(0, 250),
			"notes" -> optional(text(0, 100000)),
			"rerunning" -> boolean
		)(SubmissionData.apply)(SubmissionData.unapply)
	)

	private def submissionsView(form: Form[SubmissionData] = submissionForm)(implicit request: RequestHeader) = {
		views.html.submissions(CommonQueries.listSubmissions, CommonQueries.listActiveExperiments, CommonQueries.listLoginUsers, form, userId(request), username(request))
	}

}
