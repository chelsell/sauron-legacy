package model

sealed trait GrammarType {
	val name: String = getClass.getSimpleName.toLowerCase
}

case class Stimulus() extends GrammarType
case class Compound() extends GrammarType
case class Dose() extends GrammarType
case class nFish() extends GrammarType
case class variant() extends GrammarType
