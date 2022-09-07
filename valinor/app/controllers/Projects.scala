package controllers

import javax.inject.Inject
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.core.CommonQueries
import kokellab.valar.core.DateTimeUtils._
import kokellab.valar.insertion.{ExperimentData, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}
import play.twirl.api.Html

class Projects @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def projects = Action {implicit request =>
		if (isAuthorized(request)) Ok(projectsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def newProject = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newProjectForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(projectsView(form = formWithErrors)(request)),
				data => try {
					val newProject = insertProject(data, userId(request).get)
					Ok(views.html.success(s"Inserted experiment ${newProject.id} (${newProject.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(projectsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(projectsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertProject(data: ExperimentData, userId: Int): ExperimentsRow = {
		val query = Experiments returning (Experiments map (_.id)) into ((newRow, id) => newRow.copy(id = id))
		exec(query += ExperimentsRow(
			id = 0,
			name = data.name,
			description = data.description,
			projectId = data.project,
			batteryId = data.battery,
			defaultAcclimationSec = data.acclimationSecs,
			templatePlateId = Some(data.templatePlate),
			creatorId = userId,
			notes = data.notes,
			created = timestamp()
		))
	}


	/******************************************************
	  * forms
	  ******************************************************/

	private val newProjectForm: Form[ExperimentData] = Form(mapping(
		"name" -> nonEmptyText(1, 100),
		"description" -> optional(text(0, 10000)),
		"project" -> number,
		"battery" -> number,
		"layout" -> number,
		"transfer_plate" -> optional(number),
		"acclimation" -> number,
		"notes" -> optional(text(0, 10000)),
		"creator" -> number(1)
	)(ExperimentData.apply)(ExperimentData.unapply))

	private def projectsView(form: Form[ExperimentData] = newProjectForm)(implicit request: RequestHeader) = {
		views.html.projects(CommonQueries.listSuperprojects, exec(Experiments.result), exec((Batteries filter (b => !b.hidden)).result), CommonQueries.listActiveTemplatePlates, exec((TransferPlates sortBy (_.datetimeCreated)).result), form, userId(request), username(request))
	}

}
