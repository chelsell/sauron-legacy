package controllers

import java.time.{Duration, LocalDateTime}
import java.util.concurrent.ConcurrentMap

import kokellab.utils.core._
import kokellab.valar.core._
import play.api.mvc._
import slick.jdbc.JdbcBackend

trait Secured extends ValarAccess {

	protected val sessionKey = "myuser"

	protected implicit val securityDb: JdbcBackend.DatabaseDef = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	// override this if needed
	protected val accessAttempts: ConcurrentMap[String, AccessAttempt] = buildCache[String, AccessAttempt](expireAfterWriteSeconds = 60 * 60 * 24)

	def attemptAccess(key: String): AccessAttempt = {
		if (accessAttempts containsKey key) accessAttempts.put(key, accessAttempts.get(key).incremented)
		else accessAttempts.put(key, AccessAttempt())
		accessAttempts.get(key)
	}

	def minsToWait(key: String, waitMinutes: Int => Long): Long = {
		if (accessAttempts containsKey key) {
			val last = accessAttempts.get(key)
			val delta = Duration.between(last.last, LocalDateTime.now())
			waitMinutes(last.n) - delta.toMinutes
		} else 0
	}

	def lastAttempt(key: String): Option[AccessAttempt] = if (accessAttempts containsKey key) Some(accessAttempts.get(key)) else None

	def resetAttempts(key: String): AccessAttempt = accessAttempts.put(key, AccessAttempt(n = 0))

	def username(implicit request: RequestHeader): Option[String] = request.session.get(sessionKey)

	def userId(implicit request: RequestHeader): Option[Int] = userObject(request) map (_.id)

	def userObject(implicit request: RequestHeader): Option[UsersRow] = if (username(request).isDefined) {
		CommonQueries.listLoginUsers find (_.username == username(request).get)
	} else None

	def fullName(implicit request: RequestHeader): Option[String] = userObject map (u => s"${u.firstName} ${u.lastName}")

	def isAuthorized(implicit request: Request[AnyContent]): Boolean = username(request).isDefined

	def isWriteAuthorized(implicit request: Request[AnyContent]): Boolean = username(request).isDefined && (CommonQueries.listWriteAuthorizedUsers map (_.id) contains userId(request).get)

	protected case class AccessAttempt(n: Int = 1, last: LocalDateTime = LocalDateTime.now) {
		def incremented: AccessAttempt = AccessAttempt(n + 1, LocalDateTime.now)
	}

}
