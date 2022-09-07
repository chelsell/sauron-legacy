package controllers

import java.sql.Timestamp
import java.time.ZoneId

import javax.inject.Inject
import kokellab.valar.core.DateTimeUtils._
import model.SimpleSubmissionInfo
import kokellab.valar.core.{CommonQueries, exec, loadDb}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller, RequestHeader, Result}


// see this nonsense: https://stackoverflow.com/questions/30799988/play-2-4-form-could-not-find-implicit-value-for-parameter-messages-play-api-i

class Index @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()
	import kokellab.valar.core.CommonQueries._
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def index = Action {implicit request => Ok(indexView()(request)) }

	def _index = Action {implicit request => Ok(views.js._index()) }

	def redirectToIndex = Action { Redirect("/") }

	def methodNotAllowed = Action {implicit request => MethodNotAllowed(indexView()(request)) }

	def login = Action { implicit request =>
		attemptLogin(request.remoteAddress) match {
			case None => 
				loginForm.bindFromRequest.fold(
					formWithErrors => BadRequest(indexView(form = formWithErrors)(request)),
					result => {
						resetAttempts(request.remoteAddress)
						Redirect(routes.Index.index()).withSession(sessionKey -> result._1)
					}
				)
			case Some(r) => r
		}
	}

	def logout = Action {
		Redirect(routes.Index.index()).withNewSession.flashing( // TODO flash is unused
			"success" -> "You are now logged out."
		)
	}

	def runSearch = Action { implicit request =>
		plateForm.bindFromRequest.fold(
			formWithErrors => BadRequest(indexView(loginForm, formWithErrors)(request)),
			plate => plate match { // ignore IntelliJ; don't change this to 'plate match'
				case plateRunIdPattern() => Redirect(routes.Plates.plate(plate.toInt))
				case submissionHashPattern() => Redirect(routes.Plates.plateByHash(plate))
			}
		)
	}


	/******************************************************
	  * log in and out
	  ******************************************************/

	private def attemptLogin(key: String)(implicit request: RequestHeader): Option[Result] = {
		// check first, then attempt access; otherwise, it's unfair to a user who might just be checking to see if they can try again yet
		val minsToTimeout = minsToWait(key, timeoutMinutes)
		val minsToLockout = minsToWait(key, lockoutMinutes)
		// println(s"timeout=$minsToTimeout and lockout=$minsToLockout with ${lastAttempt(key)} for $key")
		if (minsToLockout > 0) Some(ErrorRelay.apply(LOCKED, username(request), message = Some(s"You have made too many login attempts and have been locked out from this location for 24 hours."))) // check this first
		else if (minsToTimeout > 0) Some(ErrorRelay.apply(TOO_MANY_REQUESTS, username(request), message = Some(s"You must wait for $minsToTimeout more ${if (minsToTimeout > 1) "minutes" else "minute"} before attempting to log in from this location again.")))
		else { // we're good to try again
			val lastAttempt = attemptAccess(key)
			// println(s"Attempting access: $lastAttempt")
			None
		}
	}


	/******************************************************
	  * utilities
	  ******************************************************/

	implicit val timestampOrdering: Ordering[Timestamp] = Ordering.by(_.toInstant.toEpochMilli)

	private def buildHistory(request: RequestHeader): Seq[SimpleSubmissionInfo] = if (userId(request).isEmpty) Nil else {

		val q = for {
			((history, submission), user) <- SubmissionRecords join Submissions on (_.submissionId === _.id) join Users on (_._2.userId === _.id)
		} yield (history, submission, user)

		val w = exec(q.result) sortBy (_._2.created) reverseMap {case (history, submission, user) => SimpleSubmissionInfo(history, submission, user)}
		w filter (_.user.id == userId(request).get) take 10
	}

	private def buildPending(request: RequestHeader): Seq[(SubmissionsRow, ExperimentsRow)] = {
		val alreadyInserted = exec((
			Runs filter (_.submissionId.nonEmpty) map (_.submissionId)
		).result) map (_.get)
		val q = for {
			(submission, experiment) <- Submissions filter (_.userId === userId(request)) filterNot (_.id inSet alreadyInserted) join Experiments on (_.experimentId === _.id)
			if experiment.active
		} yield (submission, experiment)
		(exec(q.result) sortBy (_._1.created)).reverse take 20
	}

	/******************************************************
	  * forms
	  ******************************************************/

	//noinspection MatchToPartialFunction // don't do this!!
	private val loginForm = Form(
		tuple(
			"user" -> text,
			"password" -> text
		) verifying ("Invalid username or password", result => security.check(result._1, result._2))
	)

	private val plateForm = Form(
		"plate" -> text
	)

	private def indexView(form: Form[(String, String)] = loginForm, plateForm: Form[String] = plateForm)(implicit request: RequestHeader) = {
		views.html.index(stats(), listWriteAuthorizedUsers,
			buildHistory(request), buildPending(request),
			form, plateForm, username(request), fullName(request)
		)
	}

        // TODO move this somewhere
        private def stats() = Map.empty[String, Int]
        /*
	private def stats(): Map[String, Int] = Map(
		"runs" -> exec(Runs.length.result),
		"instruments" -> exec(Saurons.length.result),
		"stimulus batteries" -> exec(Batteries.length.result),
		"submissions" -> exec(Submissions.length.result),
		"runs on SauronX" -> exec((Runs filter (_.submissionId.isDefined)).length.result),
		"physical plates" -> exec(Plates.length.result),
		"genetic variants" -> exec(GeneticVariants.length.result),
		"features defined" -> exec(Features.length.result),
		"sensors defined" -> exec(Sensors.length.result),
		"experiments" -> exec(Experiments.length.result),
		"projects" -> exec(Superprojects.length.result),
		"compounds" -> exec(Runs.length.result),
		"compound batches" -> exec(Batches.length.result),
		"targets and indications" -> exec(MandosObjects.length.result),
		"chemical annotations" -> exec(MandosRules.length.result),
		"million animals" -> exec((Wells map (_.n)).result).sum / 1000/1000,
		"days of video" -> 37 // TODO
	)
        */

	/******************************************************
	  * properties
	  ******************************************************/

	private def timeoutMinutes(n: Int) = if (n < 5) 0 else if (n < 8) n else if (n < 15) Math.pow(n, 2).toInt else Math.pow(n, 3).toInt
	private def lockoutMinutes(n: Int) = if (n > 30) 60*60*24 else 0

	private lazy val security = new kokellab.valar.core.Security()

	private lazy val submissionHashPattern = """[0-9a-f]{12}""".r
	private lazy val plateRunIdPattern = """\d{1,10}""".r

}
