package controllers

import javax.inject.Inject

import kokellab.valar.core.loadDb
import play.api.Logger
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, Results}

class General @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._
	import kokellab.valar.core.CommonQueries._

	def expressions = Action {implicit request =>
		Ok(views.html.expressions(username(request)))
	}

	def extendable(item: String) = Action {implicit request =>
		if (isAuthorized(request)) Ok(views.js.extendable(item))
		else Results.Unauthorized
	}

}
