package valar.params.layouts.post

import pippin.core.trimWhitespaceAndQuotes
import pippin.grammars._
import pippin.grammars.squints.{SiPrefix, Squinter}
import valar.core.{CommonQueries, loadDb}
import valar.core.Tables.{BatchesRow, ControlTypesRow, GeneticVariantsRow}
import valar.params.ParamOrigin
import valar.core.{exec, loadDb}
import valar.params.layouts.{ExcessiveValueException, LookupFailedException}
import squants.mass.SubstanceConcentration

import scala.util.Try

/**
  * Provides converters from expressions to Valar-compatible types.
  * Each parameter type has a single corresponding trait here.
  * This does not handle parameterizations: LayoutParameterization does and wraps around LayoutGrammars.
  * Where applicable, each of these fetches rows:
  *   - fetches from Valar
  *   - parses pippin grammars
  *   - handles surrounding quotes
  *   - verifies that values are reasonable.
  */
object LayoutGrammars {

  implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  trait LayoutGrammar[A] {
    def apply(expression: String): Option[A] = {
      val a = parse(expression)
      a foreach check
      a
    }
    protected def parse(expression: String): Option[A]
    protected def check(a: A): Unit = {}
    protected def origin: ParamOrigin
  }

  trait LookupGrammar[A] extends LayoutGrammar[A] {
    override protected def parse(e: String) = {
      preprocess(e) map { trimmed =>
        lookup(trimmed) getOrElse {
          throw new LookupFailedException(origin, trimmed)
        }
      }
    }
    protected def preprocess(e: String) = {
      val v = trimWhitespaceAndQuotes(e)
      if (v.isEmpty) None else Some(v)
    }
    protected def lookup(e: String): Option[A]
  }

  object ControlTypeGrammar extends LookupGrammar[ControlTypesRow] {
    override protected def lookup(e: String): Option[ControlTypesRow] = {
      Try(e.toByte).toOption flatMap { v =>
        exec((ControlTypes filter (_.id === v)).result).headOption
      }
    }
    override protected def origin: ParamOrigin = ParamOrigin.controlType
    override protected def preprocess(e: String): Option[String] = {
      if (e.trim.isEmpty) None else {
        Try(e.toInt.toString).toOption orElse {
          throw new GrammarException(s"Control type '$e' is not a number (must be an ID)")
        }
      }
    }
  }

  object VariantGrammar extends LookupGrammar[GeneticVariantsRow] {
    override protected def lookup(e: String) = {
      val trimmed = trimWhitespaceAndQuotes(e)
      CommonQueries.listVariants find (v => v.name == trimmed || v.id.toString == trimmed)
    }
    override protected def origin: ParamOrigin = ParamOrigin.variant
  }

  object CompoundGrammar extends LookupGrammar[BatchesRow] {
    override protected def lookup(e: String) = CommonQueries.batchByHash(e)
    override protected def origin: ParamOrigin = ParamOrigin.compound
  }

  object DoseGrammar extends LayoutGrammar[Double] {
    protected val prefixes = SiPrefix.between("pico", "milli").toSet
    override protected def parse(expression: String) = {
      // units are allowed only at the end of the whole expression
      val prefix = prefixes find (p => expression endsWith (p.symbol + "M")) getOrElse SiPrefix.micro
      val stripped = expression.stripSuffix(prefix.symbol+"M")
      // deterministic by not adding randBasis
      IfElseRealNumberGrammar.eval(stripped, BooleanRealNumberGrammar.DEFAULT_TOLERANCE) map { dose =>
        dose * (prefix.factor / SiPrefix.micro.factor) // make sure not to introduce rounding error
      }
    }
    override protected def check(ans: Double): Unit = {
      if (ans < 0) throw new ExcessiveValueException(origin, ans)
      if (ans > 1E9) throw new ExcessiveValueException(origin, ans) // something like 7x the "molarity" of pure liquid bromine.
    }
    override protected def origin: ParamOrigin = ParamOrigin.dose
  }


  trait IntGrammar extends LayoutGrammar[Int] {
    override protected def parse(expression: String): Option[Int] = {
      if (expression.trim.isEmpty) None else IfElseIntegerGrammar.eval(expression)
    }
    override protected def check(n: Int): Unit = {
      if (n < bounds._1) throw new ExcessiveValueException(origin, n)
      if (n > bounds._2) throw new ExcessiveValueException(origin, n)
    }
    protected def bounds: (Int, Int)
  }

  trait StringGrammar extends LayoutGrammar[String] {
    override protected def parse(expression: String): Option[String] = {
      if (expression.trim.isEmpty) None else Some(expression)
    }
    override protected def check(s: String): Unit = {
      if (s.length > maxLength) throw new ExcessiveValueException(origin, s)
    }
    protected def maxLength: Int
  }

  object AgeGrammar extends IntGrammar {
    override protected def bounds = (0, 3650)
    override protected def origin: ParamOrigin = ParamOrigin.ageDpf
  }

  object NFishGrammar extends IntGrammar {
    override protected def bounds = (0, 1000)
    override protected def origin: ParamOrigin = ParamOrigin.nFish
  }

  object WellGroupGrammar extends StringGrammar {
    override protected def maxLength: Int = 30
    override protected def origin: ParamOrigin = ParamOrigin.group
  }

}
