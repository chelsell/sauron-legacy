from typing import List

from terminaltables import AsciiTable

from valarpy import Valar
from .utils import notify_user_light, warn_thin, show_table

from .configuration import config

max_rows = 20  # type: int


def show(headers: List[str], rows: List[list], title=None) -> None:
    data = [headers]
    data.extend(rows)
    print(AsciiTable(data, title=title).table)


def show_limited(headers: List[str], rows: List[list]) -> None:
    print("Showing only the {} most recently inserted rows:".format(max_rows))
    show(headers, rows[0:max_rows])


# TODO because of the init from main, self isn't passed
# TODO this also makes queries for large tables inefficient
class LookupTools:

    def users(self) -> None:
        import valarpy.model as model
        show(
            headers=['id', 'username', 'first name', 'last name'],
            rows=[[u.id, u.username, u.first_name, u.last_name] for u in model.Users.select()]
        )

    def experiments(self) -> None:
        import valarpy.model as model
        show(
            headers=['id', 'name', 'battery', 'description', 'datetime created'],
            rows=[
                [e.id, e.name, e.battery.name, e.description, e.created]
                for e in model.Experiments
                .select(model.Experiments, model.Batteries)
                .join(model.Batteries)
            ]
        )

    def submissions(self) -> None:
        import valarpy.model as model
        show_limited(
            ['id', 'submission hash', 'description', 'experiment', 'battery', 'template', 'author',
             'previous submission of plate', 'notes', 'created'],
            [
                [s.id, s.lookup_hash, s.description, s.experiment.name, s.experiment.battery.name,
                 s.experiment.template_plate.name, s.user_id, s.continuing_id, s.notes, s.created]
                for s in
                model.Submissions.select(model.Submissions, model.Experiments, model.Batteries, model.TemplatePlates) \
                    .join(model.Experiments).join(model.Batteries) \
                    .switch(model.Experiments).join(model.TemplatePlates) \
                    .order_by(model.Submissions.created.desc()).limit(max_rows)
            ]
        )

    def history(self) -> None:
        return self._history(None)

    def log(self) -> None:
        import valarpy.model as model
        return self._history(model.SubmissionRecords.sauron == config.sauron_name)

    def _history(self, where) -> None:
        import valarpy.model as model
        query = model.SubmissionRecords.select(model.SubmissionRecords, model.Submissions, model.Users,
                                               model.Experiments, model.Saurons) \
            .join(model.Submissions).join(model.Experiments) \
            .switch(model.Submissions).join(model.Users, on=model.Submissions.user_id == model.Users.id) \
            .switch(model.SubmissionRecords).join(model.Saurons) \
            .where(model.SubmissionRecords.sauron == config.sauron_id)
        if where is not None: query = query.where(where)
        query = query.order_by(model.SubmissionRecords.datetime_modified.desc()).limit(max_rows)
        show(
            ['submission hash', 'description', 'user', 'experiment', 'status', 'updated', 'started'],
            [
                [s.submission.lookup_hash, s.submission.description, s.submission.user.username,
                 s.submission.experiment.name, s.status, s.datetime_modified, s.created]
                for s in query
            ]
        )

    def templates(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name', 'description', 'author', 'created'],
            [[t.id, t.name, t.description, t.author_id, t.created] for t in model.TemplatePlates.select()]
        )

    def batteries(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name', 'description', 'length', 'datetime created'],
            [
                [c.id, c.name, c.description, c.length, c.created]
                for c in model.Batteries.select().where(~model.Batteries.name.startswith('legacy-'))
            ]
        )

    def assays(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name', 'description', 'datetime created'],
            [
                [c.id, c.name, c.description, c.created]
                for c in model.Assays.select().where(~model.Assays.name.startswith('legacy-'))
            ]
        )

    def plates(self) -> None:
        import valarpy.model as model
        show_limited(
            ['id', 'experiment', 'plated by', 'datetime plated'],
            [
                [p.id, p.experiment_id, p.person_plated.username, p.datetime_fish_plated]
                for p in model.Plates.select(model.Plates, model.Users).join(model.Users).order_by(
                model.Plates.created.desc()).limit(max_rows)
            ]
        )

    def plate_types(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'n_rows', 'n_columns', 'name', 'opacity'],
            [
                [p.id, p.n_rows, p.n_columns, p.name, p.opacity]
                for p in model.PlateTypes.select()
            ]
        )

    def saurons(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name'],
            [
                [s.id, s.name]
                for s in model.Saurons.select()
            ]
        )

    def locations(self) -> None:
        import valarpy.model as model
        PartOf = model.Locations.alias()
        show(
            ['id', 'name', 'purpose', 'part_of', 'description', 'active', 'temporary'],
            [
                [p.id, p.name, p.purpose, p.part_of.name, p.description, p.active, p.temporary]
                for p in model.Locations.select(model.Locations, PartOf).join(PartOf)
            ]
        )

    def runs(self) -> None:
        import valarpy.model as model
        show_limited(
            ['id', 'plate', 'experimentalist', 'datetime run', 'notes'],
            [
                [r.id, r.plate_id, r.experimentalist_id, r.datetime_run, r.notes]
                for r in model.Runs.select().order_by(model.Runs.created.desc()).limit(max_rows)
            ]
        )

    def configs(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'sauron', 'description', 'datetime modified', 'datetime inserted'],
            [
                [c.id, c.sauron.id, c.description, c.datetime_changed, c.created]
                for c in model.SauronConfigs.select(model.SauronConfigs, model.Saurons).join(model.Saurons)
            ]
        )

    def stimuli(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name', 'description', 'is analog', 'audio file'],
            [[s.id, s.name, s.description, bool(s.analog), s.audio_file_id] for s in model.Stimuli.select()]
        )

    def sensors(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'name', 'description'],
            [[s.id, s.name, s.description] for s in model.Sensors.select()]
        )

    def audio_files(self) -> None:
        import valarpy.model as model
        show(
            ['id', 'filename', 'seconds', 'stimulus', 'created'],
            [
                [c.audio_file.id, c.audio_file.filename, c.audio_file.n_seconds, c.name, c.audio_file.created]
                for c in model.Stimuli.select(model.Stimuli, model.AudioFiles)
            .join(model.AudioFiles)
            ]
        )


class IdentificationTools:

    def identify(self, submission_hash: str) -> None:

        with Valar():
            import valarpy.model as model
            submission = model.Submissions \
                .select(model.Submissions, model.Experiments) \
                .join(model.Experiments) \
                .where(model.Submissions.lookup_hash == submission_hash) \
                .first()
            history = list(
                model.SubmissionRecords
                .select(model.SubmissionRecords, model.Submissions, model.Saurons)
                .join(model.Submissions)
                .switch(model.SubmissionRecords).join(model.Saurons)
                .where(model.Submissions.lookup_hash == submission_hash)
                .order_by(model.SubmissionRecords.created.desc())
            )
            run = model.Runs.select(model.Runs, model.Submissions) \
                .join(model.Submissions) \
                .where(model.Submissions.lookup_hash == submission_hash) \
                .first()
            if run is not None:
                notify_user_light(
                    "Submission {} (\"{}\")".format(submission_hash, submission.description),
                    "in experiment \"{}\" was run {} times".format(submission.experiment.name, len(history)),
                    "It’s associated with plate run {}.".format(run.id)
                )
                if len(history) == 0:
                    warn_thin(
                        "WARNING: Submission {} has run {} but no history!".format(submission_hash, run.id),
                        "This shouldn't be possible."
                    )
            elif submission is None:
                notify_user_light("No submission with hash {} exists.".format(submission_hash))
            elif len(history) == 0:
                notify_user_light(
                    "Submission {} (\"{}\")".format(submission_hash, submission.description),
                    "in experiment \"{}\" was never run".format(submission.experiment.name)
                )
            else:
                notify_user_light(
                    "Submission {} ({})".format(submission_hash, submission.description),
                    "in experiment \"{}\" was run {} times".format(submission.experiment.name, len(history)),
                    "The most recent run was on Sauron {} and has status \"{}\".".format(history[0].sauron.id,
                                                                                         history[0].status)
                )

        if len(history) > 0:
            print('')
            print(show_table(
                headers=['status', 'sauron', 'run datetime'],
                rows=[[z.status, z.sauron.id, z.created] for z in history],
                title='full run history'
            ))


__all__ = ['LookupTools', 'IdentificationTools']
