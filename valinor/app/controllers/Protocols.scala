package controllers

import javax.inject.Inject
import kokellab.valar.core._
import kokellab.utils.core._
import kokellab.valar.core.RowHashes
import kokellab.valar.core.DateTimeUtils._
import kokellab.valar.core.CommonQueries._
import kokellab.valar.params.assays.{AssayParameterizations, StimulusValueException}
import kokellab.valar.params.assays.TemplateProtocol
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import kokellab.utils.grammars._
import kokellab.valar.insertion.{BatteryData, BatteryInsertion, ValarChangeException}
import play.api.data.validation._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}
import play.twirl.api.Html

import scala.util.{Failure, Success, Try}

class Protocols @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	val seed: Int = random.nextInt()


	/******************************************************
	  * views
	  ******************************************************/

	def protocols = Action {implicit request =>
		if (isAuthorized(request)) Ok(protocolsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def _protocols = Action {implicit request =>
		if (isAuthorized(request)) Ok(views.js._protocols(listTemplateAssays))
		else Results.Unauthorized("") // it's better to have an empty JS than to insert HTML into the source
	}

	def newProtocol = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newBatteryForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(protocolsView(form = formWithErrors)(request)),
				data => {
					try {
						val newProtocol = handleBattery(data)
						val text = s"Inserted battery ${newProtocol.id}."
						Ok(views.html.success(text, username, Html(text), None))
					} catch {
						case e: ValarChangeException =>
							val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
							BadRequest(protocolsView(form = madeFormWithErrors)(request))
						case e: Throwable => throw e
					}
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(protocolsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def handleBattery(data: BatteryData) = {
		BatteryInsertion.insert(data)
	}


	/******************************************************
	  * form
	  ******************************************************/

	private val newBatteryForm = Form(mapping(
		"name" -> nonEmptyText(1, 100),
		"description" -> optional(text(0, 10000)),
		"notes" -> optional(text(0, 10000)),
		"assay" -> list(number),
		"params" -> list(text),
		"creator" -> number(1)
	)(BatteryData.apply)(BatteryData.unapply))

	private def protocolsView(form: Form[BatteryData] = newBatteryForm)(implicit request: RequestHeader) = {
		views.html.protocols(CommonQueries.listProtocols filter (!_.hidden), listTemplateAssays, form, userId(request), username(request))
	}


}
