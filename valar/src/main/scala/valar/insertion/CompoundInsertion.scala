package valar.insertion

import java.sql.{Date, Timestamp}
import java.time.{LocalDate, LocalDateTime, ZoneId, ZonedDateTime}

import com.typesafe.scalalogging.Logger
import pippin.misc.Chem
import pippin.core.{bytesToHashHex, intsToBytes}
import pippin.core
import pippin.core.addons.SecureRandom
import valar.core.DateTimeUtils.timestamp
import valar.core.{DateTimeUtils, ValarConfig, exec, loadDb}

import scala.util.{Failure, Success, Try}
import scala.util.control.NonFatal

object CompoundInsertion {

  val logger: Logger = Logger(getClass)
  private implicit val db = loadDb()

  import valar.core.Tables._
  import valar.core.Tables.profile.api._

  def insert(data: CompoundData, refId: Int): (BatchesRow, Option[CompoundsRow]) = attempt { () => {
    validate(data)
    val (compound, compoundIsNew) = if (data.hasInchi) insertCompound(data) else (None, false)
    withCleanup { () => {
      val batch = insertBatch(data, compound, refId)
      withCleanup { () => {
        insertBatchLabels(batch, data, refId)
        // insert compound labels after because if insertBatch or insertBatchLabels fails, we don't have to delete added compound labels
        compound foreach { c => insertCompoundLabels(c, data, refId) }
      }}{ () =>
        exec(Batches filter (_.id === batch.id) delete)
      }
      return (batch, compound)
    }}{ () =>
      // only delete it if it's new!
      if (compoundIsNew && compound.isDefined) {
        exec(Compounds filter (_.id === compound.get.id) delete)
      }
    }
  }}

  private def validate(data: CompoundData): Unit = {
    if (data.hasInchi ^ (data.kind == "compound")) {
      throw new UserContradictionException(s"Compound type (${data.kind}) must be 'compound' if and only if an Inchi is supplied")
    }
  }

  private def insertBatch(data: CompoundData, compound: Option[CompoundsRow], refId: Int): BatchesRow = {
    val query = Batches returning (Batches map (_.id)) into ((newRow, id) => newRow.copy(id = id))
    val prev: Option[BatchesRow] = data.madeFrom map ( m =>
      exec((Batches filter (_.lookupHash === m)).result).headOption getOrElse { exec((Batches filter (_.id === m.toInt)).result).head }
    )
    val batch: BatchesRow = exec(query += BatchesRow(
      id = 0,
      compoundId = compound map (_.id),
      refId = Some(refId),
      dateOrdered = Some(convertDate(data.dateOrdered)),
      locationId = data.location,
      boxNumber = data.boxNumber,
      wellNumber = data.wellNumber,
      madeFromId = prev map (_.id),
      locationNote = data.locationNote,
      amount = Some(data.amount),
      concentrationMillimolar = data.concentrationMillimolar,  // NOTE: calling code in Valinor sets this later
      molecularWeight = data.molecularWeight,
      solventId = Some(data.solvent),
      personOrdered = Some(data.creator),
      notes = data.notes,
      supplierId = Some(data.supplier),
      supplierCatalogNumber = data.catalogNumber,
      legacyInternalId = genLegacyId(data),
      lookupHash = newTmpHash(), // we'll fix in a minute
      created = timestamp()
    ))
    exec(Batches filter (_.id === batch.id) map (_.lookupHash) update  genLookupHash(batch))
    exec((Batches filter (_.id === batch.id)).result).head
  }

  private def insertCompoundLabels(compound: CompoundsRow, data: CompoundData, refId: Int): Set[CompoundLabelsRow] = {
    data.compoundLabels map (line => {
      val name = line.trim
      val result = exec((CompoundLabels filter (_.refId === refId) filter (_.compoundId === compound.id) filter (_.name === name)).result).headOption
      result getOrElse {
        val query = CompoundLabels returning (CompoundLabels map (_.id)) into ((newRow, id) => newRow.copy(id = id))
        exec(query += CompoundLabelsRow(
          id = 0,
          compoundId = compound.id,
          name = line.trim,
          refId = refId,
          created = timestamp()
        ))
      }
    })
  }

  private def insertBatchLabels(oc: BatchesRow, data: CompoundData, refId: Int): Set[BatchLabelsRow] = {
    data.batchLabels map (line => {
      val name = line.trim
      val result = exec((BatchLabels filter (_.refId === refId) filter (_.batchId === oc.id) filter (_.name === name)).result).headOption
      result getOrElse {
        val query = BatchLabels returning (BatchLabels map (_.id)) into ((newRow, id) => newRow.copy(id = id))
        exec(query += BatchLabelsRow(
          id = 0,
          batchId = oc.id,
          name = name,
          refId = refId,
          created = timestamp()
        ))
      }
    })
  }

  private def insertCompound(data: CompoundData): (Option[CompoundsRow], Boolean) = {
    val compound: Option[CompoundsRow] = exec((Compounds filter (_.inchi === data.inchi)).result).headOption
    compound map { c =>
      (Some(c), false)
    } getOrElse {
      val (inchi, inchikey, smiles) = getInchiInchikeyAndSmiles(data.inchi)
      val query = Compounds returning (Compounds map (_.id)) into ((newRow, id) => newRow.copy(id = id))
      val inserted = exec(query += CompoundsRow(
        id = 0,
        inchi = inchi,
        inchikey = inchikey,
        inchikeyConnectivity = Chem.connectivity(inchikey),
        smiles = Some(smiles),
        created = timestamp()
      ))
      (Some(inserted), true)
    }
  }

  private def getInchiInchikeyAndSmiles(string: String): (String, String, String) = Try {
    if (string startsWith "InChI=") {
      (string, Chem.inchiToInchikey(string), Chem.inchiToSmiles(string))
    } else {
      val inchi = Chem.smilesToInchi(string)
      (inchi.inchi, inchi.inchikey, string)
    }
  } match {
    case Success(t) => t
    case Failure(e: Exception) => throw new ValidationException(s"Could not parse Inchi/SMILES $string", e)
    case Failure(e) => throw e
  }

  private def genLookupHash(batch: BatchesRow): String =
    "oc_" + bytesToHashHex(intsToBytes(Seq(batch.id))).substring(0, 11)

  private def genLegacyId(data: CompoundData): Option[String] = if (data.boxNumber.isDefined && data.wellNumber.isDefined) Some {
    "UC" + "%03d".format(data.boxNumber.get) + "%02d".format(data.wellNumber.get) // TODO this depends on the ref ID
  } else None

  private def convertDate(d: LocalDate): Date = Date.valueOf(d)

  private val random = new SecureRandom()
  private def newTmpHash(): String = "%tmp-" + (random.alphanumeric take 14-5).mkString

}
