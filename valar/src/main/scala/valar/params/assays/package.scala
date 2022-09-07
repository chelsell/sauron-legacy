package valar.params

import pippin.grammars.GrammarException

package object assays {

  class AssayException(message: String, cause: Exception = null) extends Exception(message) with ValarParamsException

  class AssayValueGrammarException(cause: GrammarException) extends AssayException(cause.message)

  class AssayRangeGrammarException(cause: GrammarException) extends AssayException(cause.message)

  class StimulusValueException(value: Double, templateStimulusFrameId: Short, stimulus: Short)
    extends AssayException(s"Value $value is out of range for template_stimulus_frame $templateStimulusFrameId on stimulus $stimulus")

  class BlockOverlapException()
    extends AssayException(s"There are overlapping assay blocks") // TODO make more useful
}
