from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.model.treatments import Treatment


class UnknownVariableError(UnrecognizedKeyError):
    """ """

    pass


class TreatmentNamer:
    """
    A way to format a Treatment.
    """

    @abcd.abstractmethod
    def display(self, treatment: Treatment, name: Union[None, str, Mapping[int, str]]) -> str:
        """
        Returns a dict mapping treatments to their display strings

        Args:
            treatment: A Treatment instance
            name: None, a name, or a map from compound IDs to compound names.
                  Does not need to include every compound ID, and may even be empty.

        Returns:
            The display name of the Treatment

        """
        raise NotImplementedError()

    def __call__(self, treatment: Treatment, name: Union[None, str, Mapping[int, str]]) -> str:
        """

        Args:
            treatment:
            name:

        Returns:

        """
        return self.display(treatment, name)

    def _convert(self, t: Treatment, names: Union[None, str, Mapping[int, str]]) -> Optional[str]:
        if names is None:
            return None
        elif isinstance(names, str):
            return names
        elif hasattr(names, "__getitem__"):
            return names[t.cid] if t.cid is not None and t.cid in names else None
        else:
            raise TypeError(f"Type {type(names)} for name not recognized")


rtreatment = regex.compile(r"\${treatment\}", flags=regex.V1)
rid = regex.compile(r"\${?id\}", flags=regex.V1)
rcid = regex.compile(r"\${?cid\}", flags=regex.V1)
rbid = regex.compile(r"\${?bid\}", flags=regex.V1)
rinchikey = regex.compile(r"\${?([cd]?id\|)?inchikey(?:\?([^\}]+))?\}", flags=regex.V1)
rchembl = regex.compile(r"\${?([cd]?id\|)?chembl(?:\?([^\}]+))?\}", flags=regex.V1)
rtag = regex.compile(
    r"\${?([cd]?id\|)?tag(?:[:.]([0-9]+))?(?:/([a-z_]+))?(?:\?([^\}]+))?\}", flags=regex.V1
)
rname = regex.compile(
    r"\${?([cd]?id\|)?name(?:[:.]([0-9]+))?(?:/([a-z_]+))?(?:\?([^\}]+))?\}", flags=regex.V1
)
rumdose = regex.compile(r"\${um(?:([:.])([0-9]+))?\}", flags=regex.V1)
rdose = regex.compile(r"\${?dose(?:([:.])([0-9]+))?\}", flags=regex.V1)
rwrong = regex.compile(r"\${[^\}]*\}", flags=regex.V1)


class StringTreatmentNamer(TreatmentNamer):
    """
    A displayer built from a formatting expression with variables ${um}, ${bid}, etc.
    The result of display() will be the literal expression, but with certain fields substituted.

    Example:
    >>> # example 1
        >>> displayer = StringTreatmentNamer('${id} (${dose.2})') # '.2'  means 2 decimal places
        >>> displayer(Treatment.from_info(4, 5048.6))  # returns 'c13 (5.05mM)'
        >>> # example 2
        >>> displayer = StringTreatmentNamer('${name} (${id} @ ${dose:1})')  # ':1' means 1 sigfig
        >>> displayer(Treatment.from_info(4, 5048.6), 'ethanol')  # returns 'ethanol (c4 @ 5mM)'
        >>> # example 3
        >>> displayer = StringTreatmentNamer('compound ID = ${cid} @ ${um} [µM'])  # 'um' means micromolar
        >>> displayer(Treatment.from_info(4, 5048.6), 'ethanol')  # returns 'compound ID = 4 @ 5048.6 [µM]'

    The recognized placeholders are:
        - ${treatment}        The value of str(treatment)
        - ${bid}              The batch ID
        - ${cid}              The compound ID, or '' if it doesn't exist
        - ${id}               The compound ID with a prefix of 'c' if it exists, otherwise the batch ID with a prefix of 'b'
        - ${inchikey}         The inchikey
        - ${connectivity}     The inchikey connectivity
        - ${chembl}           The CheEMBL ID, if it exists
        - ${connectivity}     The inchikey connectivity
        - ${name}             The exact compound name passed
        - ${name:10}          The compound name, truncated to 10 characters with a trailing … if needed (note: strips out any trailing ... in the name before truncating)
        - ${name/lower}       The compound name, forced into lowercase
        - ${name?-}           The compound name with - if not found ('?' by default)
        - ${id|name}          Same as the above, but filling in the ID only if the name is missing
        - any combo           Any combination of truncateion, capitalization, and if-null rules, in order
        - ${tag}              The value of batches.tag
        - ${tag?-}            The tag with - if missing ('?' by default)
        - any combo           Any combination of truncateion, capitalization, and if-null rules, in order
        - ${dose}             The dose with infinite significant figures and µM, nM, pM, or mM as needed
        - ${dose:3}           The dose with 3 (or other value passed) significant figures and µM, nM, pM, or mM as needed
        - ${dose.3}           The dose with 3 (or other value passed) _decimal places_ and µM, nM, pM, or mM as needed
        - ${um}               The dose in micromolar with a suffix of µM, with infinite significant figures
        - ${um:3}             The dose in micromolar with a suffix of µM, with 3 (or other value passed) significant figures
        - ${um.3}             The dose in micromolar with a suffix of µM, with 3 (or other value passed) decimal places

    The capitalizers are:
        - 'lower' for all lowercase
        - 'upper' for all uppercase
        - 'first' for the first letter capitalized
        - 'title' for title case
        - 'auto' for smart capitalization
        - 'auto_first' for auto but always capitalizing the first letter
        - 'auto_title' for auto but title case
    """

    def __init__(self, expression: str):
        """
        Builds using a formatting expression. See the docs for StringTreatmentDisplayer.

        Args:
            expression: A formatting expression
        """
        self.expression = expression
        # it's just annoyingly easy to make this mistake
        n_dollar, n_left, n_right = (
            expression.count("$"),
            expression.count("{"),
            expression.count("}"),
        )
        if n_dollar > n_left or n_dollar > n_right or n_left != n_right:
            logger.warning(
                f"Expression contains {n_dollar} $ signs but {n_left} left braces and {n_right} right braces. Intended?"
            )

        # just test first
        e = self._format("", 0, 0, None, 0, "", "", 0)
        bad = []
        for match in rwrong.finditer(e):
            bad.append(match.group(0))
        if len(bad) > 0:
            raise UnknownVariableError(f"The expressions {bad} were not recognized")

    def display(self, t: Treatment, name: Union[None, str, Mapping[int, str]]) -> str:
        name = self._convert(t, name)
        return self._format(str(t), t.bid, t.cid, t.btag, t.dose, name, t.inchikey, t.chembl)

    def _format(
        self,
        t_str: str,
        bid: int,
        cid: int,
        tag: Optional[str],
        dose: float,
        name: Optional[str],
        inchikey,
        chembl,
    ) -> str:
        """


        Args:
          t_str: str:
          bid: int:
          cid: int:
          tag: Optional[str]:
          dose: float:
          name: Optional[str]:
          inchikey:
          chembl:

        Returns:

        """

        def inchikeyit(gs):
            return self._fall(gs[0], cid, bid) if inchikey is None else inchikey

        def chemblit(gs):
            return self._fall(gs[0], cid, bid) if chembl is None else chembl

        def nameit(gs):
            return self._parse(cid, bid, name, gs[0], gs[1], gs[2], gs[3])

        def tagit(gs):
            return self._parse(cid, bid, tag, gs[0], gs[1], gs[2], gs[3])

        def idit(gs):
            return "b" + str(bid) if cid is None else ("c" + str(cid))

        def get_dose_kwargs(gs) -> Tup[Optional[int], Optional[bool]]:
            use_sigfigs = gs[0] == ":"
            round_figs = None if gs[1] is None else int(gs[1])
            return use_sigfigs, round_figs

        def doseit(gs):
            return self._dosify(dose, True, *get_dose_kwargs(gs))

        def rumit(gs):
            return self._dosify(dose, False, *get_dose_kwargs(gs))

        e = self.expression
        e = self._replace(e, rtreatment, lambda g: t_str)
        e = self._replace(e, rid, idit)
        e = self._replace(e, rbid, lambda gs: bid)
        e = self._replace(e, rcid, lambda gs: cid)
        e = self._replace(e, rinchikey, inchikeyit)
        e = self._replace(e, rchembl, chemblit)
        e = self._replace(e, rname, nameit)
        e = self._replace(e, rtag, tagit)
        e = self._replace(e, rdose, doseit)
        e = self._replace(e, rumdose, rumit)
        return e

    def _dosify(self, dose, adjust, use_sigfigs, round_figs) -> Optional[str]:
        """"""
        if round_figs is None:
            round_figs = 5
        elif round_figs == "*":
            round_figs = 100  # reserved
        round_figs = int(round_figs)
        #return Tools.nice_dose(dose, round_figs, adjust_units=adjust, use_sigfigs=use_sigfigs) #Tools.nice_dose can't be found -CH
        return dose

    def _fall(self, allowed, cid, bid) -> Optional[str]:
        """"""
        if allowed is None:
            return
        fallback = None if allowed is None else allowed.rstrip("|")
        if cid is not None and fallback in ["cid", "id"]:
            return "c" + str(cid)
        elif fallback in ["id", "bid"]:
            return "b" + str(bid)

    def _replace(self, e0, reg, rep) -> Optional[str]:
        """"""
        for match in reg.finditer(e0):
            rep1 = rep(match.groups())
            e0 = e0.replace(match[0], "" if rep1 is None else str(rep1))
        return e0

    def _parse(
        self,
        cid,
        bid,
        name: Optional[str],
        fallback_rule: str,
        truncate_rule: Optional[str],
        cap_rule: Optional[str],
        if_null_rule: Optional[str],
    ) -> str:
        """"""
        if_null_rule = "" if if_null_rule is None else if_null_rule
        if name is None:
            name = self._fall(fallback_rule, cid, bid)
            if name is None:
                name = if_null_rule
        else:
            # check cap_rule first so we can auto-capitalize with the whole string
            name = self._capitalize(name, cap_rule)
            if truncate_rule is not None:
                name = Tools.truncate(name, int(truncate_rule))
        return name

    def _capitalize(self, name: str, rule: Optional[str]) -> str:
        """"""
        if rule is None:
            return name
        if rule == "lower":
            return name.lower()
        elif rule == "upper":
            return name.upper()
        elif rule == "auto":
            return name.upper() if name.isupper() and len(name) < 6 else name.lower()
        elif rule == "first":
            return name.upper() if len(name) < 2 else name[0].upper() + name[1:]
        elif rule == "title":
            return name.title()
        elif rule == "auto_title":
            return name.upper() if name.isupper() and len(name) < 6 else name.title()
        elif rule == "auto_first":
            return (
                name.upper()
                if name.isupper() and len(name) < 6 or len(name) < 2
                else name[0].upper() + name.lower()[1:]
            )
        else:
            raise UnknownVariableError(f"Unknown capitalization scheme {rule}")

    def __repr__(self):
        return "display(" + self.expression + ")"

    def __str__(self):
        return repr(self)


class TreatmentNamers:
    """"""

    @classmethod
    def of(cls, s: str) -> StringTreatmentNamer:
        """


        Args:
            s: str:

        """
        return StringTreatmentNamer(s)

    @classmethod
    def id(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${id}")

    @classmethod
    def id_with_dose(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${id} (${dose})")

    @classmethod
    def name_with_dose(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${id|name} (${dose})")

    @classmethod
    def name(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${id|name}")

    @classmethod
    def name_with_id(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${name} [${id}]")

    @classmethod
    def name_with_id_with_dose(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${name} [${id}] (${dose})")

    @classmethod
    def chembl(cls) -> StringTreatmentNamer:
        """"""
        return StringTreatmentNamer("${id|chembl}")


__all__ = ["TreatmentNamer", "TreatmentNamers", "StringTreatmentNamer"]
