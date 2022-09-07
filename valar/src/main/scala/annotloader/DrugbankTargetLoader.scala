package kokellab.mandos.load

import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.core.{exec, loadDb}

import scala.xml.{Elem, Node, XML}
import collection.JavaConverters._


object DrugbankTargetLoader extends MandosImporter {

	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	protected var version: String = null
	protected var dbref: Int = -1

	def main(args: Array[String]): Unit = {
		version = args(1)
		val xml: Elem = XML.loadFile(args(0))
		println(s"Loaded XML with ${sys.runtime.freeMemory} free")
		load(xml)
		println("Done")
	}

	def load(xml: Elem): Unit = {
		for (drug <- xml \ "drug") {
			val drugbankId: String = ((drug \ "drugbank-id") filter (id => (id \ "@primary").nonEmpty) map (_.text)).head
			// 15 | drugbank:${version}:primary_id
                        dbref = getRef(s"drugbank:${version}:primary_id").id
			val compound: Option[Int] = exec((CompoundLabels filter (_.refId === dbref) filter (_.name === drugbankId) map (_.compoundId)).result).headOption
			if (compound.nonEmpty) {
				procCategories(drug, compound.get)
//				procTargets(drug, compound.get)
			}
		}
	}

	def procCategories(drug: Node, compound: Int): Unit = {
		(drug \ "drugbank-id" filter (node => node.attribute("primary").isDefined) map (_.text)).headOption foreach { id =>
			println("Adding categories")
//			for (category <- drug \ "categories" \ "category") {
//				val mesh = (category \ "mesh-id").text
//				val cat = (category \ "category").text
//			}
			for (atc <- drug \\ "atc-codes" \ "atc-code" \ "level") {
				val code = atc.attribute("code").get.text
				val name = atc.text
				if (code.length > 1 && code.head == 'N') {
					println(code, name)
					val results = link(
						compoundId = compound,
						target = code,
						targetName = Some(name),
						predicate = "has_atc_code",
						ref = s"drugbank:${version}:atc",
						kind = "class",
						externalId = None,
					)
				}
			}
		}
	}

	def procTargets(drug: Node, compound: Int): Unit = {
		for (target <- drug \ "targets" \ "target") {
			val knownAction = (target \ "known-action").text == "yes"
			if (knownAction) {
				procTarget(compound, target)
			}
		}
	}

	def procTarget(compound: Int, target: Node): Unit = {
		val targetId = (target \ "id").text
		val targetName = (target \ "name").text
		val targetOrganism = (target \ "organism").text
		val source = targetOrganism.toLowerCase match {
			case "human" => "drugbank:${version}:targets:human"
			case "mouse" => "drugbank:${version}:targets:mouse"
			case "zebrafish" => "drugbank:${version}:targets:zebrafish"
			case _ => ""  // will fail TODO
		}
		if (source == s"drugbank:${version}:targets:human") {
			val actions = (target \ "actions" \ "action") map (_.text)
			val uniprotId = (
				(target \\ "external-identifiers" \ "external-identifier") filter { e =>
					(e \ "resource").text == "UniProtKB"
				} map (e => (e \ "identifier").text)
				).headOption
			println(s"Adding target $targetId/${uniprotId.getOrElse("-")} ($targetName) in $targetOrganism to c$compound with actions {${actions.mkString(",")}}")
			var targetObj: Option[MandosObjectsRow] = None
			for (action <- actions) {
				// link(compoundId: Int, target: String, targetName: Option[String], predicate: String, ref: String, kind: String, externalId: Option[String], value: Option[String] = None)
				val results = link(
					compoundId = compound,
					target = targetId,
					targetName = Some(targetName),
					predicate = action,
					ref = source,
					kind = "target",
					externalId = None,
				)
				targetObj = Some(results._2)
			}
			if (targetObj.nonEmpty) {
				procTargetIds(target, targetObj.get)
			} else println("OH NO!")
		}
	}

	def procTargetIds(target: Node, targetObj: MandosObjectsRow): Unit = {
		for (externalTargetId <- target \\ "external-identifiers" \ "external-identifier") {
			val resource = (externalTargetId \ "resource").text
			val externalTargetIdText = (externalTargetId \ "identifier").text
			if (Set("UniProtKB", "UniProt Accession") contains resource) {
				val keyTag = exec((MandosObjectTags filter (_.ref === dbref) filter (_.name === resource) filter (_.value === externalTargetIdText)).result).headOption getOrElse {
					exec(MandosObjectTags += MandosObjectTagsRow(
						id = 0,
						`object` = targetObj.id,
						ref = dbref, // TODO
						name = resource,
						value = externalTargetIdText,
						created = timestamp()
					))
				}
			}
		}
	}

}
