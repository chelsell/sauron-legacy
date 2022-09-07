package valar.params.assays

import org.scalatest.{Matchers, PropSpec}

class StimulusValueTest extends PropSpec with Matchers {

  property("stimulus value") {
    a [TempRangeException] should be thrownBy {
      StimulusValue.fromUnsignedDouble(false, false, false)(5)
    }
    a [TempRangeException] should be thrownBy {
      StimulusValue.fromUnsignedDouble(false, false, false)(-1)
    }
    a [TempRangeException] should be thrownBy {
      StimulusValue.fromUnsignedDouble(false, false, false)(0.1)
    }
    StimulusValue.fromUnsignedDouble(false, false, false)(0) should equal (BinaryStimulusValue(-128))
    StimulusValue.fromUnsignedDouble(false, false, false)(1) should equal (BinaryStimulusValue(-127))
  }

}
