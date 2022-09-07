package controllers

import javax.inject.Inject
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.core.CommonQueries._
import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.core.Tables.GeneticVariants
import kokellab.valar.insertion.{ValarChangeException, VariantData, VariantInsertion}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Results}

class Variants @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def variants = Action {implicit request =>
		if (isAuthorized(request)) Ok(variantsView()(request))
		else ErrorRelay.apply(401, username(request))(request)
	}

	def newVariant = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newVariantForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(variantsView(form = formWithErrors)(request)),
				data => try {
					val variant = insertVariant(data)
					Ok(views.html.success(s"Inserted variant ${variant.id} (${variant.name})", username))
				} catch {
					case e: ValarChangeException =>
						val madeFormWithErrors = bound.withGlobalError("Insertion failed: " + e.getMessage)
						BadRequest(variantsView(form = madeFormWithErrors)(request))
					case e: Throwable => throw e
				}
			)
		}
	}

	def methodNotAllowed = Action { implicit request =>
		MethodNotAllowed(variantsView()(request))
	}


	/******************************************************
	  * insertion
	  ******************************************************/

	private def insertVariant(data: VariantData)(implicit request: RequestHeader): GeneticVariantsRow = {
		VariantInsertion.insert(data)
	}

	/******************************************************
	  * forms
	  ******************************************************/

	private val newVariantForm: Form[VariantData] = Form(mapping(
		"name" -> nonEmptyText(1, 250),
		"type" -> nonEmptyText(1, 30),
		"mother" -> optional(number),
		"father" -> optional(number),
		"date_created" -> optional(localDate).verifying("Date must not be in the future", d => d.isEmpty || d.get.compareTo(Utils.today) <= 0),
		"notes" -> optional(text(0, 10000)),
		"creator" -> number(1)
	)(VariantData.apply)(VariantData.unapply))

	private def variantsView(form: Form[VariantData] = newVariantForm)(implicit request: RequestHeader) = {
		views.html.variants(listVariants, form, userId(request), username(request))
	}

}
