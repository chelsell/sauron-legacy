package controllers

import javax.inject.Inject
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.core.CommonQueries._
import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.core.Tables.GeneticConstructs
import kokellab.valar.insertion.{ValarChangeException, ConstructData}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}

class Constructs @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def constructs = Action {implicit request =>
		if (isAuthorized(request)) Ok(constructsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

        /*
	def newConstruct = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newConstructForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(constructsView(form = formWithErrors)(request)),
				data => try {
					val construct = insertConstruct(data)
					Ok(views.html.success(s"Inserted construct ${construct.id} (${construct.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(constructsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}
        */

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(constructsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

        /*
	private def insertConstruct(data: ConstructData)(implicit request: RequestHeader): GeneticConstructsRow = {
		ConstructInsertion.insert(data)
	}
        */

	/******************************************************
	  * forms
	  ******************************************************/

	private val newConstructForm: Form[ConstructData] = Form(mapping(
		"name" -> nonEmptyText(1, 250),
		"kind" -> nonEmptyText(1, 30),
		"location" -> number,
                "supplier" -> number,
                "box" -> number,
                "tube" -> number,
                "description" -> optional(text),
                "ref" -> number(0),
                "pubmed_id" -> optional(number),
                "pub_link" -> optional(text),
                "person_made" -> number,
                "date_made" -> optional(localDate),
                "selection_marker" -> optional(text),
                "bacterial_strain" -> optional(text),
                "vector" -> optional(text),
                "rawFile" -> text,
                "notes" -> optional(text),
		"creator" -> number(1)
	)(ConstructData.apply)(ConstructData.unapply))

	private def constructsView(form: Form[ConstructData] = newConstructForm)(implicit request: RequestHeader) = {
		views.html.constructs(exec(GeneticConstructs.result), exec(Suppliers.result), exec(Locations.result), exec(Users.result), form, userId(request), username(request))
	}

}
