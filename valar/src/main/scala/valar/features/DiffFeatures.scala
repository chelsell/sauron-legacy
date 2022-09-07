package valar.features

import breeze.linalg._
import valar.video.RichMatrices.RichMatrix
import valar.video.{RoiUtils, SimplePlateInfo, VTimeFeature}


class MiFeature extends VTimeFeature[Float] {

    override val name: String = "MI"

    override def apply(input: Iterator[RichMatrix]): Array[Float] = {
        (input sliding 2) map {slid =>
            (slid.head |-| slid.last).sum.toFloat
        }
    }.toArray
}

class CdFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"cd($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      ((slid.last.matrix |-| slid.head.matrix) #> tau).toFloat
    }
  }.toArray
}

class TdFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"td($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      ((slid.last.matrix |-| slid.head.matrix) |> tau).toFloat
    }
  }.toArray
}

class CdplusFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"cd+($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      (slid.last.matrix #> (slid.head.matrix + tau)).toFloat
    }
  }.toArray
}

class CdminusFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"cd-($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      (slid.last.matrix #< (slid.head.matrix - tau)).toFloat
    }
  }.toArray
}

class TdplusFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"td+($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      (slid.last.matrix |> (slid.head.matrix + tau)).toFloat
    }
  }.toArray
}

class TdminusFeature(tau: Int) extends VTimeFeature[Float] {

  override val name: String = s"td-($tau)"

  override def apply(input: Iterator[RichMatrix]): Array[Float] = {
    (input sliding 2) map {slid =>
      (slid.last.matrix |< (slid.head.matrix - tau)).toFloat
    }
  }.toArray
}

class PlusminusFeature extends VTimeFeature[Short] {

  override val name: String = s"plusminus"

  override def apply(input: Iterator[RichMatrix]): Array[Short] = {
    (input sliding 2) map {slid =>
      (slid.last.matrix +<> slid.head.matrix).toShort
    }
  }.toArray
}
