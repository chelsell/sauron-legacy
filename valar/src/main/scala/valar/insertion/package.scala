package valar

import java.sql.{SQLException, SQLIntegrityConstraintViolationException}

import pippin.grammars.GrammarException
import valar.core.ValarException
import valar.params.ValarParamsException

package object insertion {

  /**
    * A user-level expected exception thrown from the insertion subproject.
    */
  trait ValarChangeException extends ValarException

  /**
    * A generic validation exception for user-level errors.
    * Here to provided a concrete class of the ValarChangeException trait.
    */
  class ValidationException(message: String, cause: Exception = null) extends Exception(message, cause) with ValarChangeException

  /**
    * A lookup in Valar failed in a way that's more complex than a key constraint violation.
    */
  class LookupFailedException(message: String) extends ValidationException(message)

  /**
    * The request included a combination that doesn't make sense.
    */
  class UserContradictionException(message: String) extends ValidationException(message)

  /**
    * The service is intentionally refusing the request to avoid a probable issue.
    * This indicates that the operation requested, if truly intended, must be performed through a different service or directly in SQL.
    */
  class RefusalException(message: String) extends ValidationException(message)

  /**
    * An issue from the params package.
    */
  class ValarChangeParamsException(message: String, cause: Exception) extends ValidationException(message, cause) with ValarParamsException

  /**
    * Intended to wrap GrammarExceptions to make things easier for calling code.
    */
  class GrammarValidationException(message: String, verboseMessage: Option[String] = None, underlying: Option[Exception] = None)
    extends GrammarException(message, verboseMessage, underlying) with ValarChangeException

  /**
    * Usually means that a unique or foreign key constraint failed.
    * @param message Should be more useful than the message from the cause
    */
  class ConstraintViolationException(message: String, cause: SQLIntegrityConstraintViolationException) extends ValidationException(message, cause)

  def withCleanup[A](call: () => A)(cleanup: () => Any): A = try {
    call()
  } catch {
    case e: Throwable => try {
      cleanup()
      throw e
    } finally throw e // it might not be critical to have this in a finally block, but don't change it
  }

  def attempt[A](call: () => A): A = try {
    call()
  } catch {
    // we know the first few user exceptions are safe
    case e: SQLIntegrityConstraintViolationException =>
      throw new ConstraintViolationException(s"A database constraint violation occurred (ex: a unique or foreign key). Probably something should exist but doesn’t, or vice versa.", e)
    case e: GrammarException =>
      throw new GrammarValidationException(e.message, e.verboseMessage, e.underlying)
    case e: ValarParamsException =>
      // unfortunately we're stuck with e.getCause, which is a Throwable; we need an Exception
      if (e.getCause != null && e.isInstanceOf[Exception])
        throw new ValarChangeParamsException(e.getMessage, e.getCause.asInstanceOf[Exception])
      else throw e
    case e: Throwable => try {
      throw e
    } finally throw e // it might not be critical to have this in a finally block, but don't change it
  }

}
