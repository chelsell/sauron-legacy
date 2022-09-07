package valar.params.layouts

import pippin.grammars.GrammarException
import valar.params.layouts.post.LayoutGrammars
import org.scalatest.{Matchers, PropSpec}

class LayoutGrammarsTest extends PropSpec with Matchers {

  property("n fish") {
    LayoutGrammars.NFishGrammar.apply("5") should equal (Some(5))
    LayoutGrammars.NFishGrammar.apply("0") should equal (Some(0))
    a [ExcessiveValueException] should be thrownBy {
      LayoutGrammars.NFishGrammar.apply("-1")
    }
    a [GrammarException] should be thrownBy {
      LayoutGrammars.NFishGrammar.apply("0.1")
    }
    a [GrammarException] should be thrownBy {
      LayoutGrammars.NFishGrammar.apply("1.0") // don't even allow decimal points
    }
    LayoutGrammars.NFishGrammar.apply("5+5") should equal (Some(10))
    LayoutGrammars.NFishGrammar.apply("if 1=1: 8 else: 0") should equal (Some(8))
    LayoutGrammars.NFishGrammar.apply("") should equal (None)
  }

  property("control type") {
    LayoutGrammars.ControlTypeGrammar.apply("1") map (_.id) should equal (Some(1))
    LayoutGrammars.ControlTypeGrammar.apply("") map (_.id) should equal (None)
    a [LookupFailedException] should be thrownBy {
      LayoutGrammars.ControlTypeGrammar.apply("110")
    }
    a [GrammarException] should be thrownBy {
      LayoutGrammars.ControlTypeGrammar.apply("2")
    }
  }
  property("variant") {
    val id = 17 // TODO make one here
    val name = "cacng3a (homozygous)" // has a space in it
    LayoutGrammars.VariantGrammar.apply('"' + name + '"') map (_.id) should equal (Some(id))
    LayoutGrammars.VariantGrammar.apply(name) map (_.id) should equal (Some(id))
    LayoutGrammars.VariantGrammar.apply('"' + id.toString + '"') map (_.id) should equal (Some(id))
    LayoutGrammars.VariantGrammar.apply("") map (_.id) should equal (None)
    LayoutGrammars.ControlTypeGrammar.apply(name) map (_.id) should equal (Some(id))
    a [LookupFailedException] should be thrownBy {
      LayoutGrammars.VariantGrammar.apply("999999") // TODO terrible
    }
  }

}
