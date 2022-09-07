package kokellab.mandos.load

import com.github.tototoshi.csv.CSVReader

import scala.xml.XML
import collection.JavaConverters._
import kokellab.valar.core.CommonQueries
import kokellab.valar.core.Tables._
import kokellab.valar.core.{loadDb, exec}
import kokellab.valar.core.DateTimeUtils.timestamp


object DrugbankStructureLoader extends MandosImporter {

	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	protected var version: String = null
	private var priorNames = (exec(CompoundLabels.result) map (n => (n.compoundId, n.refId))).toSet
	private var priorChemInfo = (exec(MandosInfo.result) map (c => (c.compoundId, c.name))).toSet

	def main(args: Array[String]): Unit = {
		val reader = CSVReader.open(args(0), "UTF-8")
		version = args(1)
		try {
			reader.iteratorWithHeaders foreach readLine
		} finally {
			reader.close()
		}
	}

	def readLine(line: Map[String, String]): Unit = {
		/*
		DrugBank ID	Name	CAS Number	Drug Groups	InChIKey	InChI	SMILES	Formula	KEGG Compound ID	KEGG Drug ID	PubChem Compound ID	PubChem Substance ID	ChEBI ID	ChEMBL ID	HET ID	ChemSpider ID	BindingDB ID
	DB00006	Bivalirudin	128270-60-0	approved; investigational	OIRCOABEOLEUMC-GEJPAHFPSA-N	InChI=1S/...	C98H138N24O33		D03136	16129704	46507415	59173	CHEMBL2103749		10482069
	*/
		exec((Compounds filter (_.inchikey === line("InChIKey"))).result).headOption foreach { compound =>
			println(compound.id)
			insertName(compound.id, line("DrugBank ID"), s"drugbank:${version}:primary_id")
			insertName(compound.id, line("Name"), s"drugbank:${version}:secondary_id")
			insertName(compound.id, line("CAS Number"), "cas_number")
			insertName(compound.id, line("KEGG Compound ID"), "kegg:compound_id")
			insertName(compound.id, line("KEGG Drug ID"), "kegg:drug_id")
			insertName(compound.id, line("ChEBI ID"), "chebi:id")
			insertName(compound.id, line("ChEMBL ID"), "chembl:id")
			insertName(compound.id, line("ChemSpider ID"), "chemspider:id")
			insertName(compound.id, line("PubChem Compound ID"), "pubchem:compound_id")
			insertName(compound.id, line("PubChem Substance ID"), "pubchem:substance_id")
			insertName(compound.id, line("HET ID"), "het:id")
			insertName(compound.id, line("BindingDB ID"), "bindingdb:id")
			val groups = line("Drug Groups") split ";" map (_.trim)
			for (group <- Seq("approved", "investigational", "withdrawn", "nutraceutical", "vet_approved", "illicit")) {
//				add(compound.id, "is_" + group, (groups contains group).toString)
				link(compound.id, "is_" + group, None, "part_of", s"drugbank:${version}:links", "class", None)
			}
			if (line("ChemSpider ID").nonEmpty && compound.chemspiderId.isEmpty) {
				exec(Compounds filter (_.id === compound.id) map (_.chemspiderId) update Some(line("ChemSpider ID").toInt))
			}
			if (line("ChEMBL ID").nonEmpty && compound.chemspiderId.isEmpty) {
				exec(Compounds filter (_.id === compound.id) map (_.chemblId) update Some(line("ChEMBL ID")))
			}
		}
	}

	private def add(compoundId: Int, key: String, value: String): Unit =
		if (value.trim.nonEmpty && !(priorChemInfo contains (compoundId, key))) {
//			println(s"Adding $compoundId: $key=$value")
		exec(MandosInfo += MandosInfoRow(
			id = 0,
			compoundId = compoundId,
			refId = getRef(s"drugbank:${version}:chem_info").id,
			name = key,
			value = value,
			created = timestamp()
		), waitSeconds = 60*5)
//			priorChemInfo = (exec(MandosInfo.result) map (c => (c.compoundId, c.name))).toSet
	}

	private def insertName(compoundId: Int, name: String, source: String): Unit =
		if (name.trim.nonEmpty && !(priorNames contains (compoundId, getRef(source).id))) {
//			println(s"Naming $compoundId: $name ($source)")
		exec(CompoundLabels += CompoundLabelsRow(
			id = 0,
			refId = getRef(source).id,
			name = name,
			compoundId = compoundId,
			created = timestamp()
		), waitSeconds = 60*5)
//			priorNames =  (exec(CompoundLabels.result) map (n => (n.compoundId, n.refId))).toSet
	}
}
