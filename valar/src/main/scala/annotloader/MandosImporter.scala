package kokellab.mandos.load

import kokellab.valar.core.DateTimeUtils.timestamp
import kokellab.valar.core.Tables.MandosRules
import kokellab.valar.core.{exec, loadDb}


class MandosImporter {

	private implicit val db = loadDb()
	import kokellab.valar.core.Tables._
	import kokellab.valar.core.Tables.profile.api._

	protected var sources: Map[String, RefsRow] = (exec(Refs.result) map (s => s.name -> s)).toMap

	protected def getRef(name: String): RefsRow = {
		if (!(sources contains name)) {
			exec(Refs += RefsRow(
				id = 0,
				name = name,
				externalVersion = Some("5.0.10"),
				created = timestamp()
			), waitSeconds = 60*5)
			sources = (exec(Refs.result) map (s => s.name -> s)).toMap
		}
		sources(name)
	}

	protected def link(
				compoundId: Int,
				target: String, targetName: Option[String],
				predicate: String, ref: String, kind: String,
				externalId: Option[String]
	): (MandosRulesRow, MandosObjectsRow, MandosPredicatesRow) = {
		val sourceId = getRef(ref).id
		val predicateObj: MandosPredicatesRow =
			exec((MandosPredicates filter (_.name === predicate)).result, waitSeconds = 60*5).headOption getOrElse {
				val insertQuery = MandosPredicates returning (MandosPredicates map (_.id)) into ((newRow, id) => newRow.copy(id = id))
				exec(insertQuery += MandosPredicatesRow(
					id = 0,
					name = predicate,
					refId = sourceId,
					kind = kind,
					created = timestamp()
				), waitSeconds = 60*5)
			}
		val objectObj: MandosObjectsRow =
			exec((MandosObjects filter (_.refId === sourceId) filter (_.externalId === target)).result, waitSeconds = 60*5).headOption getOrElse {
				val insertQuery = MandosObjects returning (MandosObjects map (_.id)) into ((newRow, id) => newRow.copy(id = id))
				exec(insertQuery += MandosObjectsRow(
					id = 0,
					name = targetName,
					externalId = target,
					refId = sourceId,
					created = timestamp()
				), waitSeconds = 60*5)
			}
		val linkObj: MandosRulesRow =
			exec((MandosRules filter (_.compoundId === compoundId) filter (_.refId === sourceId) filter (_.predicateId === predicateObj.id) filter (_.objectId === objectObj.id)).result, waitSeconds = 60*5).headOption getOrElse {
				val insertQuery = MandosRules returning (MandosRules map (_.id)) into ((newRow, id) => newRow.copy(id = id))
				exec(insertQuery += MandosRulesRow(
					id = 0,
					compoundId = compoundId,
					objectId = objectObj.id,
					refId = sourceId,
					externalId = externalId,
					predicateId = predicateObj.id,
				), waitSeconds = 60*5)
			}
		(linkObj, objectObj, predicateObj)
	}

}
