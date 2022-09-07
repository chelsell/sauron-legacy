package controllers

import javax.inject.Inject
import kokellab.utils.grammars._
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.core.CommonQueries._
import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.insertion.{LayoutData, LayoutInsertion, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._

import scala.util.control.NonFatal
import play.api.data.validation.{Constraint, Invalid, Valid, ValidationError}
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}
import views.html.helper.form

import scala.util.{Failure, Success, Try}

class Layouts @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def layouts = Action {implicit request =>
		if (isAuthorized(request)) Ok(layoutsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def controlTypes = Action {implicit request => Ok(views.html.control_types(listControlTypes, username(request))) }

	def newLayout = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newLayoutForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(layoutsView(form = formWithErrors)(request)),
				data => try {
					val nl = insertLayout(data)(request)
					Ok(views.html.success(s"Inserted template plate layout ${nl.id} (${nl.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(layoutsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(layoutsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertLayout(data: LayoutData)(implicit request: RequestHeader): TemplatePlatesRow = {
		LayoutInsertion.insert(data)
	}


	/******************************************************
	  * forms
	  ******************************************************/

	private val newLayoutForm = Form(mapping(
		"name" -> nonEmptyText(1, 100),
		"description" -> optional(text(0, 10000)),
		"plate_type" -> byteNumber,
		"fish-range" -> list(text(0, 100)),
		"control" -> list(optional(byteNumber)),
		"nfish" -> list(nonEmptyText(1, 100)),
		"age" -> list(text(0, 100)),
		"variant" -> list(text(0, 250)),
		"group" -> list(text(0, 250)),
		"treatment-range" -> list(text(0, 100)),
		"compound" -> list(text(0, 100)),
		"dose" -> list(text(0, 200)),
		"creator" -> number(1)
	)(LayoutData.apply)(LayoutData.unapply))


	private def layoutsView(form: Form[LayoutData] = newLayoutForm)(implicit request: RequestHeader) = {
		views.html.layouts(listTemplatePlates, listTemplateWells, listPlateTypes, listControlTypes, form, userId(request), username(request))
	}

}
