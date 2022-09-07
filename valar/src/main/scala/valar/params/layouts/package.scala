package valar.params

import pippin.grammars.GrammarException

package object layouts {

  class LayoutException(message: String, cause: Exception = null) extends Exception(message) with ValarParamsException

  class ExcessiveValueException(field: ParamOrigin, actual: Any) extends LayoutException(s"Excessive value '$actual' for ${field.name}")

  class LookupFailedException(field: ParamOrigin, actual: String) extends LayoutException(s"Lookup of '$actual' for ${field.name} failed")

  class TooManyException(field: ParamOrigin, maxAllowed: Int, actual: Int) extends LayoutException(s"At most $maxAllowed items required for ${field.name}, but $actual were given")

  class TooFewException(field: ParamOrigin, minAllowed: Int, actual: Int) extends LayoutException(s"At least $minAllowed items required for ${field.name}, but $actual were given")

}
