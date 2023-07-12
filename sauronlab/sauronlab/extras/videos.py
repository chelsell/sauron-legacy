from __future__ import annotations

from matplotlib.colors import to_rgb

from sauronlab.core.core_imports import *
from sauronlab.extras.video_core import VideoCore
from sauronlab.model.cache_interfaces import ASauronxVideo
from sauronlab.model.roi_tools import *
from sauronlab.model.wf_builders import *
from sauronlab.viz.kvrc import *

stim_colors = {s.name: "#" + s.default_color for s in Stimuli.select()}


def _draw_rectangle(frame, x0, y0, x1, y1, thickness: int, color):
    """
    Draw a rectangle in the frame

    Args:
        frame:
        x0:
        y0:
        x1:
        y1:
        thickness: int:
        color:

    Returns:

    """
    frame = np.copy(frame)
    frame.setflags(write=1)  # unfortunate result of some update to numpy or moviepy
    top, bottom, left, right = y0, y1, x0, x1
    frame[top : top + thickness, left:right] = color
    frame[bottom - thickness : bottom, left:right] = color
    frame[top:bottom, left : left + thickness] = color
    frame[top:bottom, right - thickness : right] = color
    return frame


def _concat_audio(clips):
    """


    Args:
        clips:

    Returns:

    """
    from moviepy.audio.AudioClip import CompositeAudioClip

    if len(clips) == 0:
        return None
    newclips = []
    for start_ms, end_ms, clip in clips:
        clip = clip.set_start(start_ms / 1000)
        newclips.append(clip)
    duration = max([e for s, e, c in clips]) / 1000 - min([s for s, e, c in clips]) / 1000
    concat = CompositeAudioClip(newclips).set_duration(duration)
    concat.fps = 44100
    return concat


@abcd.auto_info()
@abcd.auto_eq(exclude=lambda a: a != "video")
class SauronxVideo(ASauronxVideo):
    """
    A video from a SauronX or legacy Sauron run.
    This is a wrapper around a MoviePy VideoClip.
    It implements some nice functions for Sauron data, such as cropping by well label (ex SauronxVideo.well('A01')).
    It also remembers exactly where it's cropped and time-sliced with respect to the original video.

    ========
    Coordinates and times are always with respect to the original!

    Example:
        Cropping::

            cropped = video.crop_coords(100, 100, 200, 200)
            print(cropped.x0, cropped.y0)  # 100, 100
            cropped = cropped.crop_coords(100, 100, 200, 200)
            print(cropped.x0, cropped.y0)  # 200, 200

    ========

    WARNING:
        These videos are stored in memory, and will remain unless explicitly closed.
        You should call either:
            - SauronxVideo.close(), or
            - del sauronx_video (preferred)

    You should build these using a VideoCache (see sauronlab.caches.video_cache),
    or, if necessary, with SauronxVideos.of.

    Here are the features...

    1) Cropping
        - video.crop_to_well:     Crop by a single well label such as 'A01', or a well ID
        - video.crop_to_bound:    Crop a rectangle around two wells (ex 'A01' to 'D11')
        - video.crop_to_roid:     Crop by an Rois instance in Valar
        - video.crop_to_coords:   Crop to specific coordinates

    2) Time-slicing
        - video.slice_ms:           Slice to start and end milliseconds
        - video.slice_by_assay:     Slice to a AssayPositions instance.
                                    You can't use an assay name because the assay can occur multiple times.
        - video.speedx:             Speed up (>1) or slow down (<1) the video

    3) Remembering history:
        - video.x0, video.x1, video.y0, video.y1:   The current coordinates with respect to the original frame
        - video.starts_at_ms, video.starts_at_ms:   When the current video starts and ends with respect to the original
        - video.crop_history:                       A list of exact coordinates cropped with, in order
        - video.clip_histroy:                       A list of exact start and stop times, in order

    4) Previewing and saving:
        - video.ipython_display:    Show in IPython
        - video.save_mkv:           Save as the Shire-native H265 MKV
        - video.save_avi:           Save a much-less compressed AVI file

    5) Higlighting and drawing:
        - video.higlight:                       Highlight a specific well (by label or ID)
        - video.highlight_bound:                Highlight a rectangle surrounding two wells
        - video.highlight_controls:             Highlight (with a border) controls red for positive and blue for negative
        - video.highlight_controls_matching:    Highlight colors matching conditions with a specific color
        - video.highlight_with_all_compounds:   Highlight wells containing (all of) a list of compounds
        - video.highlight_by:                   Highlight by an arbitrary function of WellFrame meta column series objects
        - video.draw_roi_grid:                  Show the well ROIs as a grid
        - video.draw_rectangle:                 Draw an arbitrary rectangle

    """

    def __init__(
        self,
        path: PathLike,
        run: RunLike,
        video,
        roi_ref: RefLike,
        starts_at_ms: int,
        ends_at_ms: int,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        clip_history: Sequence[Tup[int, int]],
        crop_history: Sequence[Tup[int, int, int, int]],
        rate: float = 1,
        wf: Optional[WellFrame] = None,
        meta: Optional[Mapping[str, Any]] = None,
    ):
        from moviepy.video.io.VideoFileClip import VideoFileClip

        self.path = Path(path)
        self.run = Tools.run(run, join=True)
        self.generation = ValarTools.generation_of(self.run)
        self.wb1 = Tools.wb1_from_run(self.run)
        if not self.generation.is_sauronx():
            logger.warning(
                f"Run r{self.run.id} is generation {self.generation.name}; the ROIs might be wrong."
            )
        self.video: VideoFileClip = video
        self.roi_ref = Refs.fetch(roi_ref)
        self.rois: Mapping[str, Rois] = {
            self.wb1.index_to_label(roi.well.well_index): roi
            for roi in Rois.select(Rois, Wells, Runs, Plates, PlateTypes)
            .join(Wells)
            .join(Runs)
            .join(Plates)
            .join(PlateTypes)
            .switch(Rois)
            .join(Refs)
            .where(Refs.id == self.roi_ref.id)
            .where(Runs.id == self.run.id)
        }
        self.clip_history, self.crop_history = list(clip_history), list(crop_history)
        self.starts_at_ms, self.ends_at_ms, self.n_ms = (
            starts_at_ms,
            ends_at_ms,
            int(video.duration * 1000),
        )
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.rate, self.meta = rate, deepcopy(meta)
        if isinstance(wf, pd.DataFrame):
            self.wf = WellFrame.of(wf).slice_ms(self.starts_at_ms, self.ends_at_ms)
        else:
            self.wf = WellFrameBuilder.runs(run).build()

    def highlight_by(self, well_frame_fn: Callable[[WellFrame], WellFrame]) -> SauronxVideo:
        """


        Args:
            well_frame_fn:

        Returns:

        """
        wells = WellFrame.of(well_frame_fn(self.wf))["well_label"].unique().tolist()
        return self.highlight_wells(wells, color=sauronlab_rc.video_plain_color)

    def highlight_controls_matching(self, **kwargs) -> SauronxVideo:
        """


        Args:
            **kwargs:

        Returns:

        """
        wells = self.wf.with_controls(**kwargs)["well_label"].unique().tolist()
        return self.highlight_wells(wells, color=sauronlab_rc.video_negative_control_color)

    def highlight_controls(self) -> SauronxVideo:
        """"""
        wells = self.wf.with_controls(positive=True)["well_label"].unique().tolist()
        cp = self.highlight_wells(wells, color=sauronlab_rc.video_positive_control_color)
        wells = self.wf.with_controls(positive=False)["well_label"].unique().tolist()
        return cp.highlight_wells(wells, color=sauronlab_rc.video_negative_control_color)

    def highlight_with_all_compounds(self, compounds) -> SauronxVideo:
        """


        Args:
            compounds:

        Returns:

        """
        wells = self.wf.with_compounds_all(compounds)["well_label"].unique().tolist()
        return self.highlight_wells(wells, color=sauronlab_rc.video_plain_color)

    def highlight_bound(
        self,
        well1: str,
        well2: str,
        start_ms: int = 0,
        end_ms: Optional[int] = None,
        color=sauronlab_rc.video_plain_color,
    ) -> SauronxVideo:
        """


        Args:
            well1: str:
            well2: str:
            start_ms:
            end_ms:
            color:

        Returns:

        """
        a = self.roi_from_label(well1)
        b = self.roi_from_label(well2)
        return self.highlight_coords(
            a.x0, a.y0, b.x1, b.y1, start_ms=start_ms, end_ms=end_ms, color=color
        )

    def highlight_wells(
        self,
        labels: Union[str, Iterable[str]],
        start_ms: int = None,
        end_ms: Optional[int] = None,
        color=sauronlab_rc.video_plain_color,
    ) -> SauronxVideo:
        """


        Args:
            labels:
            start_ms:
            end_ms:
            color:

        Returns:

        """
        if not Tools.is_true_iterable(labels):
            labels = [labels]
        cp = self
        # fails early
        for roi in [self._verify_crop(label, self.roi_from_label(label)) for label in labels]:
            cp = cp.highlight_coords(
                roi.x0, roi.y0, roi.x1, roi.y1, start_ms=start_ms, end_ms=end_ms, color=color
            )
        return cp

    def highlight_coords(
        self,
        x0: int = None,
        y0: int = None,
        x1: int = None,
        y1: int = None,
        color=sauronlab_rc.video_plain_color,
        start_ms=None,
        end_ms=None,
    ) -> SauronxVideo:
        """


        Args:
            x0: int:
            y0: int:
            x1: int:
            y1: int:
            color:
            start_ms:
            end_ms:

        Returns:

        """
        try:
            r, g, b = to_rgb(color)
            color = (r * 255, g * 255, b * 255)
        except ValueError:
            raise XValueError(f"Color {color} is invalid")
        if x0 is None:
            x0 = 0
        if y0 is None:
            y0 = 0
        if x1 is None:
            x1 = self.width - 1
        if y1 is None:
            y1 = self.height - 1
        coords = dict(x0=x0 - self.x0, y0=y0 - self.y0, x1=x1 - self.x0, y1=y1 - self.y0)
        if start_ms is None and end_ms is None:
            clip = self.video.copy().fl_image(
                partial(
                    _draw_rectangle,
                    **coords,
                    color=color,
                    thickness=sauronlab_rc.video_roi_line_width,
                )
            )
        else:
            start_ms, end_ms = (
                0 if start_ms is None else start_ms / 1000,
                None if end_ms is None else end_ms / 1000,
            )
            clip = self.video.copy().subfx(
                lambda v: v.fl_image(
                    partial(
                        _draw_rectangle,
                        **coords,
                        color=color,
                        thickness=sauronlab_rc.video_roi_line_width,
                    )
                ),
                start_ms,
                end_ms,
            )
        return self.copy(clip)

    def draw_roi_grid(
        self, start_ms: Optional[int] = None, end_ms: Optional[int] = None
    ) -> SauronxVideo:
        """
        Draws an ROI grid using the specified ROI ref.
        If no ref is supplied, will draw an ROI for every ref.
        This will be moderately slow.

        Args:
            start_ms:
            end_ms:

        Returns:

        """
        v = self
        for roi in self.rois.values():
            v = v.rectangle(
                roi.x0,
                roi.y0,
                roi.x1,
                roi.y1,
                sauronlab_rc.video_roi_color,
                sauronlab_rc.video_roi_line_width,
                start_ms,
                end_ms,
            )
        return v

    def crop_to_well(self, wb1: str) -> SauronxVideo:
        """
        Crops to a single well.

        Args:
            wb1: str:

        Returns:

        """
        roi = self.roi_from_label(wb1)
        return self.crop_to_roi(wb1)

    def crop_to_bound(self, label_1: str, label_2: str) -> SauronxVideo:
        """
        Crop between two wells.

        Example:
            Cropping::

                video.bound('A01', 'C04')

        Args:
            label_1: str:
            label_2: str:

        Returns:

        """
        a, b = self.roi_from_label(label_1), self.roi_from_label(label_2)
        return self.crop_to_coords(a.x0, a.y0, b.x1, b.y1)

    def crop_to_roi(self, label: str) -> SauronxVideo:
        """


        Args:
            label: str:

        Returns:

        """
        roi = self.roi_from_label(label)
        return self.crop_to_coords(roi.x0, roi.y0, roi.x1, roi.y1)

    def crop_to_coords(self, x0: int, y0: int, x1: int, y1: int) -> SauronxVideo:
        import moviepy.video.fx.crop as crop_fx
        coords = x0 - self.x0, y0 - self.y0, x1 - self.x0, y1 - self.y0
        RoiTools.verify_coords(*coords, self.width, self.height)
        clip = crop_fx.crop(self.video, *coords)
        crop_hist = self.crop_history + [(x0, y0, x1, y1)]
        return SauronxVideo(
            self.path,
            self.run,
            clip,
            self.roi_ref,
            self.starts_at_ms,
            self.ends_at_ms,
            x0,
            x1,
            y0,
            y1,
            self.clip_history,
            crop_hist,
            self.rate,
            self.wf,
            self.meta,
        )

    def speedx(self, factor: float) -> SauronxVideo:
        """


        Args:
            factor: float:

        Returns:

        """
        clip = self.copy(self.video.speedx(factor))
        clip.rate *= factor
        return clip

    def slice_to_assay(self, assay: AssayPositions) -> SauronxVideo:
        """


        Args:
            assay: AssayPositions:

        Returns:

        """
        conv = ValarTools.assay_ms_per_stimframe(assay.assay)
        start_ms, end_ms = assay.start / conv, (assay.start + assay.length) / conv
        return self._verify_slice(start_ms, end_ms, assay)

    def slice_ms(self, start_ms: int, end_ms: int) -> SauronxVideo:
        """


        Args:
            start_ms: int:
            end_ms: int:

        Returns:

        """
        return self._verify_slice(start_ms, end_ms, None)

    def roi_from_index(self, wb1: int) -> Rois:
        """


        Args:
            wb1: int:

        Returns:

        """
        return self._verify_crop(wb1, self.rois[self.wb1.index_to_label(wb1)])

    def roi_from_label(self, wb1: str) -> Rois:
        """


        Args:
            wb1: str:

        Returns:

        """
        return self._verify_crop(wb1, self.rois[wb1])

    def roi_from_well_obj(self, well: Union[int, Wells]) -> Rois:
        """


        Args:
            well:

        Returns:

        """
        well = Wells.fetch(well)
        roi = Tools.only(
            Rois.select(Rois).where(Rois.ref_id == self.roi_ref.id).where(Wells.id == well.id)
        )
        return self._verify_crop(well, roi, well.run_id)

    def roi_from_roi(self, roi: Rois) -> Rois:
        """


        Args:
            roi: Rois:

        Returns:

        """
        return self._verify_crop(roi, roi)

    def copy(self, video: SauronxVideo) -> SauronxVideo:
        """


        Args:
            video: SauronxVideo:

        Returns:

        """
        video = self.video if video is not None else video
        return SauronxVideo(
            self.path,
            self.run,
            video,
            self.roi_ref,
            self.starts_at_ms,
            self.ends_at_ms,
            self.x0,
            self.x1,
            self.y0,
            self.y1,
            self.clip_history.copy(),
            self.crop_history.copy(),
            self.rate,
            self.wf,
            self.meta,
        )

    def ipython_display(self, suppress: bool = True):
        """


        Args:
            suppress:

        Returns:

        """
        from moviepy.video.io.html_tools import ipython_display

        logger.info(f"Displaying {self}")
        with logger.suppressed(suppress, universe=True):
            with Tools.silenced(suppress, suppress):
                return ipython_display(self.video)

    def save_mkv(self, path: PathLike) -> None:
        """


        Args:
            path: PathLike:

        """
        path = str(Tools.prepped_file(path).with_suffix(".mkv"))
        self.video.write_videofile(
            path, codec=VideoCore.codec, ffmpeg_params=VideoCore.hevc_params.split(" ")
        )

    def save_mp4(self, path: PathLike) -> None:
        """


        Args:
            path: PathLike:

        """
        path = str(Tools.prepped_file(path).with_suffix(".mp4"))
        self.video.write_videofile(path, ffmpeg_params=VideoCore.mp4_params)

    def close(self) -> None:
        """"""
        self.video.close()

    def _verify_slice(self, start_ms: int, end_ms: int, assay: Optional[AssayPositions]):
        """


        Args:
            start_ms: int:
            end_ms: int:
            assay: Optional[AssayPositions]:

        Returns:

        """
        if start_ms < 0 or end_ms <= start_ms or end_ms > self.n_ms:
            raise OutOfRangeError(f"{start_ms}–{end_ms}")
        if assay is not None and (
            assay.start < self.starts_at_ms or assay.start + assay.assay.length > self.ends_at_ms
        ):
            raise RefusingRequestError(
                "Can't trim to assay; not in bounds {self.starts_at_ms}–{self.ends_at_ms}"
            )
        clip = self.video.subclip(start_ms / 1000, end_ms / 1000)
        clip_hist = self.clip_history + [(start_ms, end_ms)]
        return SauronxVideo(
            self.path,
            self.run,
            clip,
            self.roi_ref,
            self.starts_at_ms + start_ms,
            start_ms + (end_ms - start_ms),
            self.x0,
            self.y0,
            self.x1,
            self.y1,
            clip_hist,
            self.crop_history,
            self.rate,
            self.wf,
            self.meta,
        )

    def _verify_crop(
        self, lookup: Any, roi: Rois, ref: Optional[int] = None, run: Optional[int] = None
    ) -> Rois:
        """


        Args:
            lookup: Any:
            roi: Rois:
            ref:
            run:

        Returns:

        """
        if len(self.crop_history) > 0:
            raise RefusingRequestError(f"Can't get ROI {lookup} for a cropped video")
        if ref is not None and ref != self.roi_ref.id:
            raise RefusingRequestError(f"ROI {lookup} uses ref {ref}, not {self.roi_ref.id}")
        if run is not None and run != self.run.id:
            raise RefusingRequestError(f"{lookup} belongs to run r{run}, not r{self.run.id}")
        RoiTools.verify_roi(roi, self.width, self.height, lookup)
        return roi

    def __del__(self):
        # del can be called even if __init__ failed
        if hasattr(self, "video") and self.video is not None:
            self.close()

    @property
    def n_rows(self) -> int:
        """ """
        return self.wb1.n_rows

    @property
    def n_columns(self) -> int:
        """ """
        return self.wb1.n_rows

    @property
    def width(self) -> int:
        """ """
        return self.video.w

    @property
    def height(self) -> int:
        """ """
        return self.video.h

    def __repr__(self):
        return "SauronxVideo(run={}, path='{}', {}, {}x{}, section={}–{}, bounds={}, rate={}x @ {})".format(
            self.run.id,
            self.path,
            Tools.ms_to_minsec(self.n_ms),
            self.width,
            self.height,
            self.starts_at_ms,
            self.ends_at_ms,
            (self.x0, self.y0, self.x1, self.y1),
            self.rate,
            hex(id(self)),
        )

    def __str__(self):
        return repr(self)


class SauronxVideos:
    """"""

    @classmethod
    def of(cls, path: PathLike, run: Runs) -> SauronxVideo:
        """


        Args:
            path: PathLike:
            run: Runs:

        Returns:

        """
        from moviepy.video.io.VideoFileClip import VideoFileClip

        run = Tools.run(run, join=True)
        generation = ValarTools.generation_of(run)
        roi_ref = "hardware:sauronx" if generation.is_sauronx() else "hardware:legacy"
        clip = VideoFileClip(str(path))
        clip = SauronxVideo(
            path, run, clip, roi_ref, 0, clip.duration * 1000, 0, 0, clip.w, clip.h, [], []
        )
        return clip


__all__ = ["SauronxVideo", "SauronxVideos"]
