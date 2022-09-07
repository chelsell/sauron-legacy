package controllers

import javax.inject.Inject
import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.core.CommonQueries
import model.SubmissionInfo
import kokellab.valar.core.{exec, loadDb}
import kokellab.valar.insertion.{AnnotationData, AnnotationInsertion, SubmissionDeletion, ValarChangeException}
import play.api.Logger
import play.api.data.Form
import play.api.data.Forms._
import play.api.i18n.{I18nSupport, MessagesApi}
import play.api.mvc.{Action, Controller}
import play.twirl.api.Html

import scala.util.Try

class Plates @Inject()(val messagesApi: MessagesApi) extends Controller with I18nSupport with Secured {

	val logger: Logger = Logger(getClass)
	private implicit val db = loadDb()

	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._


	/******************************************************
	  * views
	  ******************************************************/

	def plate(id: Int) = Action { implicit request =>
		if (isAuthorized(request)) {
			val info = getInfo(id)
			// an actual, factual bug in Slick made this hard:
			val concerns = exec(Annotations.result) filter (_.runId contains id)
			val usernames = (CommonQueries.listUsers map (u => u.id -> u.username)).toMap
			if (info.isDefined) {
				Ok(views.html.plate(info.get, newConcernForm, concerns, usernames, userId(request), username(request)))
			} else ErrorRelay.apply(404, username(request), message = Some(s"No plate run with ID $id exists"))(request)
		}
		else ErrorRelay.apply(401, username(request))(request)
	}


	def plateByHash(hash: String) = Action { implicit request =>
		if (isAuthorized(request)) {
			val submission = exec((Submissions filter (_.lookupHash === hash)).result).headOption
			if (submission.isDefined) {
				val plateRunId = exec((Runs filter (_.submissionId === submission.get.id) map (_.id)).result).headOption
				if (plateRunId.isDefined) {
					Redirect(routes.Plates.plate(plateRunId.get))
				} else {
					val history = exec((
						SubmissionRecords filter (_.submissionId === submission.get.id)
					).result)
					val project = exec((Experiments filter (_.id === submission.get.experimentId)).result).head
					val experimentalist = exec((Users filter (_.id === submission.get.userId)).result).head
					val concerns = exec((Annotations filter (_.submissionId === (submission map (_.id)))).result)
					val usernames = (CommonQueries.listUsers map (u => u.id -> u.username)).toMap
					Ok(views.html.submission_only(submission.get, project, experimentalist, history, concerns, usernames, userId(request), username(request)))
				}
			} else ErrorRelay.apply(404, username(request), message = Some(s"No SauronX submission $hash exists"))(request)
		}
		else ErrorRelay.apply(401, username(request))(request)
	}


	def plateConcern = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val bound = newConcernForm.bindFromRequest()
			bound.fold(
				formWithErrors => BadRequest(views.html.failure(Html(formWithErrors.errors.map(err => s"${err.key}: ${err.message}").mkString("<br />")), username(request))), // TODO
				data => try {
					addConcern(data, userId(request).get)
					if (data.run.isDefined && data.submission.isDefined) {
						Ok(views.html.success(s"Inserted concern for run ${data.run.get} and submission ${data.submission.get}", username))
					} else if (data.run.isDefined) {
						Ok(views.html.success(s"Inserted concern for run ${data.run.get}", username))
					} else {
						Ok(views.html.success(s"Inserted concern for submission ${data.submission.get}", username))
					}
				} catch {
					case e: ValarChangeException => BadRequest(views.html.failure(Html(s"${e.getMessage}"), username(request)))
					case e: Throwable => throw e
				}
			)
		}
	}

	def concernKeys = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			val usernames = (CommonQueries.listUsers map (u => u.id -> u.username)).toMap
			val concerns = exec((Annotations filter (_.name.isDefined)).result) map {c =>
				(c.name.get, usernames(c.annotatorId), c.description)
			}
			val x = concerns.groupBy (_._1) map (zz =>
				zz._1 -> (zz._2.size, (zz._2 map (_._2)).toSet, zz._2.flatMap(_._3).headOption.getOrElse("—"))
			)
			Ok(views.html.concern_keys(x, username(request)))
		}
	}

	def deleteSubmission() = Action { implicit request =>
		if (!isAuthorized(request)) ErrorRelay.apply(401, username(request))(request)
		else if (!isWriteAuthorized(request)) ErrorRelay.apply(403, username(request))(request)
		else {
			deleteForm.bindFromRequest().fold(
				formWithErrors => BadRequest(views.html.failure(Html(formWithErrors.errors.map(err => s"${err.key}: ${err.message}").mkString("<br />")), username(request))), // TODO,
				data => try {
					SubmissionDeletion.delete(data.hash, userObject(request).get)
					Ok(views.html.success(s"Deleted SauronX submission ${data.hash}. You should delete the local runs in the SauronX output directory.", username))
				} catch {
					case e: ValarChangeException => BadRequest(views.html.failure(Html(s"${e.getMessage}"), username(request)))
					case e: Throwable => throw e
				}
			)
		}
	}


	/******************************************************
	  * backend
	  ******************************************************/

	private def addConcern(data: AnnotationData, userId: Int): Unit = {
		AnnotationInsertion.insert(data)
	}


	private def getInfo(plateRunId: Int): Option[SubmissionInfo] = {
		val q = for {
			(p, s) <- Runs joinLeft Submissions on (_.submissionId === _.id)
			if p.id === plateRunId
		} yield (p, s)
		val plateRuns = exec(q.result).headOption
		val histories: Seq[SubmissionRecordsRow] = if (plateRuns.isDefined && plateRuns.get._2.isDefined) {
			exec((SubmissionRecords filter (_.submissionId === plateRuns.get._2.get.id)).result)
		} else Seq.empty
		plateRuns map {inf =>
			SubmissionInfo(inf._1, inf._2, histories)
		}
	}


	/******************************************************
	  * forms
	  ******************************************************/

	private val deleteForm: Form[X] = Form(mapping(
		"submission" -> number,
		"hash" -> text
	)(X.apply)(X.unapply))

	private val newConcernForm: Form[AnnotationData] = Form(mapping(
		"plate_run" -> optional(number),
		"submission" -> optional(number),
		"name" -> optional(text(0, 255)),
		"description" -> optional(text(0, 10000)),
		"level" -> text,
		"creator" -> number(1)
	)(AnnotationData.apply)(AnnotationData.unapply))


	case class X(submission: Int, hash: String)

}
