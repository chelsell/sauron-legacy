package valar.plugins

import valar.core.Tables.{Assays, Batteries}
import valar.core.exec

object MaintenanceTasks {

  /**
   * Sets / fixes all of the hashes.
   */
  def setAllAssayHashes(): Unit = {
    exec(Assays.result) forEach fixAssayHash
  }

  /**
   * Sets / fixes all of the hashes.
   */
  def setAllBatteryHashes(): Unit = {
    exec(Batteries.result) forEach fixBatteryHash
  }

}
