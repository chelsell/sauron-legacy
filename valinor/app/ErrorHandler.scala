import javax.inject._

import controllers.ErrorRelay
import play.api.http.DefaultHttpErrorHandler
import play.api._
import play.api.mvc._
import play.api.mvc.Results._
import play.api.routing.Router

import scala.concurrent._

@Singleton
class ErrorHandler @Inject() (
		env: Environment,
		config: Configuration,
		sourceMapper: OptionalSourceMapper,
		router: Provider[Router]
	) extends DefaultHttpErrorHandler(env, config, sourceMapper, router) {

	override def onProdServerError(request: RequestHeader, exception: UsefulException): Future[Result] = {
		Future.successful(
			InternalServerError("A server error occurred: " + exception.getMessage)
		)
	}

	override def onClientError(request: RequestHeader, statusCode: Int, message: String): Future[Result] = Future.successful (
		ErrorRelay(statusCode, username(request), None)(request) // message seems useless and always empty
	)

  private def username(implicit request: RequestHeader) = request.session.get("myuser")

}
