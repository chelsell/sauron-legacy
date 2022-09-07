package controllers

import java.sql.{Date, Timestamp}
import java.time.temporal.ChronoUnit
import java.time.{LocalDate, LocalDateTime, ZoneId, ZonedDateTime}

import kokellab.valar.core.DateTimeUtils

object Utils {

	def convertDate(d: LocalDate): Date = Date.valueOf(d)

	def convertDatetime(dt: LocalDateTime): Timestamp =
		DateTimeUtils.toSqlTimestamp(ZonedDateTime.of(dt, ZoneId.systemDefault()))

	lazy val now: LocalDateTime = LocalDateTime.now()
	lazy val today: LocalDate = LocalDate.now()
	lazy val midnight: LocalDateTime = ZonedDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0).truncatedTo(ChronoUnit.SECONDS).toLocalDateTime

}