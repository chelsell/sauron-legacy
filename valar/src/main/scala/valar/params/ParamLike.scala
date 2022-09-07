package valar.params

import pippin.grammars.params.DollarSignParam

sealed trait ParamLike {
  def usage: String
  def isPredefined: Boolean
}

case class PlateParam(param: DollarSignParam, origin: ParamOrigin, length: Int) extends ParamLike {
  def usage: String = {
    param.name + " = " + (if (param.isList) {
      s"[${origin.usage}#1, ..., ${origin.usage}#$length]"
    } else origin.usage)
  }
  def isPredefined: Boolean = param.isPredefined
}

case class AssayParam(param: DollarSignParam, origin: ParamOrigin) {
  def usage: String = {
    param.name + " = " + origin.usage
  }
  def isPredefined: Boolean = param.isPredefined
}

sealed trait ParamOrigin {
  def name: String
  def usage: String
}

object ParamOrigin {
  case object nFish extends ParamOrigin { val name = "n_fish"; val usage = "<n-fish>" }
  case object ageDpf extends ParamOrigin { val name = "age_dpf"; val usage = "<age-dpf>" }
  case object group extends ParamOrigin { val name = "group"; val usage = "<age-group>" }
  case object variant extends ParamOrigin { val name = "variant"; val usage = "\"<variant-name>\"" }
  case object compound extends ParamOrigin { val name = "compound"; val usage = "\"oc_<hash>\"" }
  case object dose extends ParamOrigin { val name = "dose"; val usage = "<µM-dose>" }
  case object pwm extends ParamOrigin { val name = "pwm"; val usage = "<pwm>" }
  case object audio extends ParamOrigin { val name = "audio"; val usage = "<volume>" }
  case object digital extends ParamOrigin { val name = "digital"; val usage = "<digital>" }
  case object conditional extends ParamOrigin { val name = "conditional"; val usage = "<conditional_value>"}
  case object interval extends ParamOrigin { val name = "interval"; val usage = "<evaluation_interval>"}
  case object assayRange extends ParamOrigin { val name = "range"; val usage = "<milliseconds>" }
  case object controlType extends ParamOrigin { val name = "control_type"; val usage = "<control_type ID or name>" } // unused on website for now; only in db
}

