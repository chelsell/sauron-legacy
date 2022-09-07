package controllers

import play.api.mvc.{RequestHeader, Result}
import play.api.mvc.Results._

object ErrorRelay {

	def apply(statusCode: Int, username: Option[String], message: Option[String] = None)(implicit request: RequestHeader): Result = {

		def view(errorName: String, defaultMessage: String) = views.html.error(statusCode, errorName, if (message.isDefined) message.get else defaultMessage, username)

		statusCode match {
			case 400 => BadRequest(view("Bad request", "The client made an error."))
			case 401 => Unauthorized(view("Unauthorized", "You must log in to access this page."))
			case 403 => Forbidden(view("Forbidden", "Although your credientials are recognized, you are not permitted to access this resource."))
			case 404 => NotFound(view("Not found", "The page was not found."))
			case 405 => MethodNotAllowed(view("Method not allowed", "The correct type of request (GET, POST, UPDATE, ...) was not used."))
			case 406 => NotAcceptable(view("Not acceptable", "Content for the requested resources is not available according to the Accept headers sent."))
			case 408 => RequestTimeout(view("Request timed out", "The client took more time than the server was willing to wait."))
			case 409 => Conflict(view("Conflict", "There was a conflict, such as a simultaneous read and write."))
			case 410 => Gone(view("Gone", "The requested resource is no longer available because it has been permanently removed."))
			case 411 => Status(411)(view("Length required", "The length of the content is required but was not given."))
			case 412 => Status(412)(view("Precondition failed", "A required precondition was not satisfied."))
			case 413 => EntityTooLarge(view("Payload too large", "The request payload was too long."))
			case 414 => UriTooLong(view("URI too long", "The URI was too long."))
			case 415 => UnsupportedMediaType(view("Unsupported media type", "The client requested a media type that is not supported."))
			case 421 => Status(421)(view("Misdirected request", "The request was misdirected. Was an old connection reused?"))
			case 423 => Locked(view("Locked", "This resource has been locked."))
			case 429 => TooManyRequests(view("Too many requests", "You have made too many requests in too short of a time period."))
			case _ => Status(statusCode)
		}
	}

}
