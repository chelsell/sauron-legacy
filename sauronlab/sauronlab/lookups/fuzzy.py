from __future__ import annotations

from rapidfuzz.process import extract as fuzz_search

from sauronlab.core.core_imports import *
from sauronlab.lookups import *
from sauronlab.lookups.lookups import *
from sauronlab.lookups.mandos import *
from sauronlab.model.compound_names import TieredCompoundNamer

look = Tools.look
_users = {u.id: u.username for u in Users.select()}
_compound_namer = TieredCompoundNamer(max_length=50)


class Fuzzy:
    """Fuzzy matching of labels for compounds, batches, and mandos objects."""

    @classmethod
    def projects(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching project names for '{s}'...")
        query = Projects.select()
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        projects = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(projects)} projects.")
        df = Lookups.projects(Projects.id << set(projects.keys()))
        df["name"] = df["id"].map(projects.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def experiments(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching experiment names for '{s}'...")
        query = Experiments.select()
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        experiments = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(experiments)} experiments.")
        df = Lookups.experiments(Experiments.id << set(experiments.keys()))
        df["name"] = df["id"].map(experiments.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def batteries(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching batteries for '{s}'...")
        query = Batteries.select()
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        batteries = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(batteries)} rows.")
        df = Lookups.batteries(Batteries.id << set(batteries.keys()))
        df["name"] = df["id"].map(batteries.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def assays(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching assays for '{s}'...")
        query = Assays.select()
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        assays = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(assays)} rows.")
        df = Lookups.assays(Assays.id << set(assays.keys()))
        df["name"] = df["id"].map(assays.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def runs(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching run descriptions for '{s}'...")
        query = Runs.select()
        data = list(query)
        raw = fuzz_search(s, {x.description for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        runs = {x.id: x.description for x in data if x.description in matches.keys()}
        logger.debug(f"Done. Found {len(runs)} rows.")
        df = Lookups.runs(Runs.id << set(runs.keys()))
        df["name"] = df["id"].map(runs.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def variants(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching variant names for '{s}'...")
        query = GeneticVariants.select()
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        variants = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(variants)} rows.")
        df = Lookups.variants(variants.keys())
        df["name"] = df["id"].map(variants.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def compounds(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug(f"Searching compound labels for '{s}'...")
        query = CompoundLabels.select()
        if ref is not None:
            query = query.where(CompoundLabels.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        compounds = {x.compound_id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(compounds)} rows.")
        df = Lookups.compounds(compounds.keys())
        df["name"] = df["id"].map(compounds.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def batches(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 70, limit: int = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 70)
            limit:

        Returns:

        """
        logger.debug(f"Searching batch labels for '{s}'...")
        query = BatchLabels.select()
        if ref is not None:
            query = query.where(BatchLabels.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        batches = {x.batch_id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(batches)} rows.")
        df = Lookups.batches(batches.keys())
        df["name"] = df["id"].map(batches.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def mandos_objects(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: Optional[int] = 100
    ) -> Lookup:
        """


        Args:
            s: str:
            ref:
            min_score: int:  (Default value = 75)
            limit:

        Returns:

        """
        logger.debug("Searching mandos_object_tags for '{s}'...")
        query = MandosObjectTags.select()
        if ref is not None:
            query = query.where(MandosObjectTags.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = fuzz_search(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        objects = {x.object_id: x.name for x in data if x.name in matches.keys()}
        logger.debug(f"Done. Found {len(objects)} rows.")
        df = MandosLookups.objects(objects.keys())
        df["name"] = df["id"].map(objects.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)


__all__ = ["Fuzzy"]
