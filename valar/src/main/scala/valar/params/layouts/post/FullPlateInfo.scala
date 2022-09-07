package valar.params.layouts.post

import valar.core.Tables._
import valar.core.Tables.profile.api._

/**
  * A full description of a plate layout as a set of mappings from 1-based well indices to final values.
  * This is trivial to insert into Valar as WellsRow and WellTreatments instances under a RunsRow.
  */
case class FullPlateInfo(
  controls: Map[Int, Option[ControlTypesRow]],
  nFish: Map[Int, Int],
  ages: Map[Int, Option[Int]],
  variants: Map[Int, Option[GeneticVariantsRow]],
  groups: Map[Int, Option[String]],
  compounds: Map[Int, List[BatchesRow]],
  doses: Map[Int, List[Double]]
)
