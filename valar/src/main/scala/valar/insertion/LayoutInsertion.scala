package valar.insertion

import com.typesafe.scalalogging.Logger
import valar.core.DateTimeUtils.timestamp
import valar.core.{exec, loadDb}


object LayoutInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: LayoutData): TemplatePlatesRow = attempt { () => {
    validate(data)
    val plate = insertTemplatePlate(data)
    withCleanup { () => {
      insertWells(data, plate)
      insertTreatments(data, plate)
    }}{ () =>
      exec(TemplatePlates filter (_.id === plate.id) delete)
    }
    plate
  }}

  private def validate(data: LayoutData): Unit = {

  }

  private def insertTemplatePlate(data: LayoutData): TemplatePlatesRow = {
    val query = TemplatePlates returning (TemplatePlates map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    exec(query += TemplatePlatesRow(
      id = 0,
      name = data.name,
      description = data.description,
      plateTypeId = data.plateType,
      authorId = data.creator,
      hidden = false,
      specializes = None,
      created = timestamp()
    ))
  }

  private def insertWells(data: LayoutData, plate: TemplatePlatesRow): Seq[TemplateWellsRow] = {
    val query = TemplateWells returning (TemplateWells map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    data.fishRanges.indices flatMap { i =>
      val range = data.fishRanges(i)
      val control = data.controls(i)
      val nFish = data.nFish(i)
      val variant = data.variants(i)
      val age = data.ages(i)
      val group = data.groups(i)
      val exists = range.trim.nonEmpty
      if (!exists) None else Some {
      exec(query += TemplateWellsRow(
        id = 0,
        templatePlateId = plate.id,
        wellRangeExpression = range,
        controlType = control,
        nExpression = nFish,
        ageExpression = age,
        variantExpression = variant,
        groupExpression = group
      ))}
    }
  }

  private def insertTreatments(data: LayoutData, plate: TemplatePlatesRow): Seq[TemplateTreatmentsRow] = {
    val query = TemplateTreatments returning (TemplateTreatments map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    data.treatmentRanges.indices flatMap { i =>
      val range = data.treatmentRanges(i)
      val drug = data.drugs(i)
      val dose = data.doses(i)
      val exists = range.trim.nonEmpty
      if (exists && (drug.trim.isEmpty || dose.trim.isEmpty)) throw new UserContradictionException(s"Non-empty row '$range' has empty drug '$drug' or dose '$dose'")
      if (!exists) None else Some {
      exec(query += TemplateTreatmentsRow(
        id = 0,
        templatePlateId = plate.id,
        wellRangeExpression = range,
        batchExpression = drug,
        doseExpression = dose
      ))}
    }
  }
}
