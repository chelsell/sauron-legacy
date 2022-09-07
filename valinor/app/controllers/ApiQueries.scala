package controllers

import javax.inject.Inject

//import kokellab.utils.grammars._
import kokellab.valar.core.{ValarConfig, loadDb}
import kokellab.valar.core.CommonQueries._
import play.api.Logger
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, Results}
import kokellab.valar.core.ValarConfig

class ApiQueries @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val api_key: String = ValarConfig.instance.config.getString("valar_api_key")
	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	def grammar(key: String, grammarType: String, expression: String, start: Int, end: Int) = Action {implicit request =>
		if (key == api_key) {
//			grammarType match {
//				case "stimulus" => {
//					val randBasis = GrammarUtils.randBasis(random.nextInt)
//					TimeSeriesGrammar.build(expression, start, end)
//				}
//				case _ => ErrorRelay.apply(404, username(request))(request)
//			}
			Results.Ok("")
		} else Results.NoContent
		Results.NotImplemented
	}

}
