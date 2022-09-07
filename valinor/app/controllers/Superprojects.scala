package controllers

import javax.inject.Inject
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.core.CommonQueries._
import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.insertion.{ProjectInsertion, SuperprojectData, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader}

class Superprojects @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def superprojects = Action {implicit request =>
		if (isAuthorized(request)) Ok(superprojectsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def newSuperproject = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newSuperprojectForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(superprojectsView(form = formWithErrors)(request)),
				data => try {
					val newProject = insertSuperproject(data)
					Ok(views.html.success(s"Inserted project ${newProject.id} (${newProject.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(superprojectsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(superprojectsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertSuperproject(data: SuperprojectData)(implicit request: RequestHeader): SuperprojectsRow = {
		ProjectInsertion.insert(data)
	}


	/******************************************************
	  * forms
	  ******************************************************/

	private val newSuperprojectForm: Form[SuperprojectData] = Form(mapping(
		"name" -> nonEmptyText(1, 100),
		"type" -> byteNumber(0),
		"description" -> optional(text(0, 25100000)),
		"reason" -> optional(text(0, 10000)),
		"methods" -> optional(text(0, 10000)),
		"active" -> boolean,
		"creator" -> number(1)
	)(SuperprojectData.apply)(SuperprojectData.unapply))

	private def superprojectsView(form: Form[SuperprojectData] = newSuperprojectForm)(implicit request: RequestHeader) = {
		views.html.superprojects(listSuperprojects, exec(ProjectTypes.result), form, userId(request), username(request))
	}

}
