package controllers

import javax.inject.Inject
import kokellab.utils.grammars._
import kokellab.valar.core.CommonQueries._
import kokellab.valar.core.DateTimeUtils._
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.params.assays.AssayParameterizations
import kokellab.valar.insertion.{AssayInsertion, TemplateAssayData, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.data.validation.{Constraint, Invalid, Valid, ValidationError}
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader}
import model.LoadData
import play.twirl.api.Html

class Assays @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	val seed: Int = random.nextInt()


	/******************************************************
	 * views
	 ******************************************************/

	def assays = Action {implicit request =>
		if (isAuthorized(request)) Ok(assaysView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def newAssay = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newAssayForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(assaysView(form = formWithErrors)(request)),
				data => try {
					val newAssay = insertAssay(data)
					Ok(views.html.success(s"Inserted assay ${newAssay.id} (${newAssay.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(assaysView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(assaysView()(request))
	}

	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertAssay(data: TemplateAssayData): TemplateAssaysRow = {
		AssayInsertion.insert(data)
	}


	/******************************************************
	  * form
	  ******************************************************/

	private val loadForm = Form(mapping(
		"template" -> number(0),
		"edit" -> boolean
	)(LoadData.apply)(LoadData.unapply))

	private val newAssayForm = Form(mapping(
		"name" -> nonEmptyText(1, 100).verifying("A template assay with that name already exists", s => exec((TemplateAssays filter (_.name === s) map (_.id)).result).isEmpty),
		"description" -> optional(text(0, 10000)),
		"range" -> list(nonEmptyText),
		"stimulus" -> list(number).verifying("The stimulus doesn't exist!", stimuli => stimuli forall (stim => exec((Stimuli filter (_.id === stim) map (_.id)).result).nonEmpty)),
		"value" -> list(text(0, 250)),
		"creator" -> number
	)(TemplateAssayData.apply)(TemplateAssayData.unapply))

	private def assaysView(form: Form[TemplateAssayData] = newAssayForm)(implicit request: RequestHeader) = {
		views.html.assays(listTemplateAssays, listStimuli, form, userId(request), username(request))
	}

}
