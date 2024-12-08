import random
import statistics
from pathlib import Path

from tqdm import tqdm

from . import StdDevs, Bins
from ..Conversions.Annotations import FullPage
from ..Conversions.Formats import InputFormat


def load_and_plot_stats(
        images_path: Path,
        annotations_path: Path,
        input_format: InputFormat,
        class_reference_table: dict[str, int],
        class_output_names: list[str],
        jobs: list[str] = None,
        summarize: bool = False,
        image_format: str = "jpg",
        output_dir: Path = None,
        seed: int = 42,
        verbose: bool = False,
):
    """
    Load dataset annotations, plot means wíth standard deviations, optionally save to file.

    :param images_path: path to directory with images
    :param annotations_path: path to directory with labels
    :param input_format: input format

    :param class_reference_table: dictionary, a function that assigns class id by class name
    :param class_output_names: list of class names

    :param jobs: list of jobs to perform on data
    :param summarize: whether to add "all" category to statistics

    :param image_format: annot_format in which the images are saved
    :param output_dir: output path, if not None, graph will be saved here

    :param seed: seed for reproducibility
    :param verbose: make script verbose
    """
    # set up params
    if jobs is None:
        jobs = ["stddev", "xybin", "whbin", "rect"]
    if output_dir is not None:
        output_dir.mkdir(exist_ok=True, parents=True)

    # load data from given paths
    images = sorted(list(images_path.rglob(f"*.{image_format}")))
    annotations = sorted(list(annotations_path.rglob(f"*.{input_format.to_annotation_extension()}")))
    data = list(zip(images, annotations))

    # setup variables for stats
    counts = [[] for _ in range(len(class_output_names))]
    all_counts = []

    wh_relative_coords = []
    xy_center_relative_coords = []
    class_ids_in_order = []

    # retrieve data for every page in data
    for path_to_image, path_to_annotations in tqdm(data, disable=not verbose, desc="Loading annotations"):
        page = FullPage.load_from_file(
            path_to_annotations,
            path_to_image,
            class_reference_table,
            class_output_names,
            input_format
        )

        # STDDEV job
        if "stddev" in jobs:
            for i in range(len(counts)):
                counts[i].append(len(page.annotations[i]))

            if summarize:
                all_counts.append(page.annotation_count())

        # WHBIN, RECT and XYBIN job
        for annot in page.all_annotations():
            if "whbin" in jobs or "rect" in jobs:
                wh_relative_coords.append((annot.bbox.width / page.size[0], annot.bbox.height / page.size[1]))
            if "xybin" in jobs:
                xy_center_relative_coords.append(
                    ((annot.bbox.left - annot.bbox.width / 2) / page.size[0],
                     (annot.bbox.top - annot.bbox.height / 2) / page.size[1])
                )
            if "rect" in jobs:
                class_ids_in_order.append(annot.class_id)

    if "stddev" in jobs:
        _process_stddev(
            counts,
            all_counts,
            class_output_names,
            summarize=summarize,
            verbose=verbose,
            output_path=output_dir / "annot_counts.png" if output_dir is not None else None,
        )

    if "xybin" in jobs:
        Bins.plot_2d_heatmap(
            xy_center_relative_coords,
            num_bins=50,
            xlabel="x",
            ylabel="y",
            output_path=output_dir / "xy_heatmap.png" if output_dir is not None else None,
        )
    if "whbin" in jobs:
        Bins.plot_2d_heatmap(
            wh_relative_coords,
            num_bins=50,
            xlabel="width",
            ylabel="height",
            output_path=output_dir / "wh_heatmap.png" if output_dir is not None else None,
        )

    if "rect" in jobs:
        data = list(zip(class_ids_in_order, wh_relative_coords))
        random.Random(seed).shuffle(data)
        Bins.plot_rectangles(
            data[:500],
            output_path=output_dir / "rectangles.png" if output_dir is not None else None,
        )


def _process_stddev(
        counts: list[list[int]],
        all_counts: list[int],
        class_output_names: list[str],
        summarize: bool = False,
        output_path: Path | str = None,
        verbose: bool = False,
):
    means = []
    stdevs = []
    for i, count in enumerate(counts):
        means.append(statistics.mean(count))
        stdevs.append(statistics.stdev(count))
        if verbose:
            print(f"class: {i}, {class_output_names[i]}")
            print(f"mean: {means[-1]}")
            print(f"stdev: {stdevs[-1]}")

    if summarize:
        means.append(statistics.mean(all_counts))
        stdevs.append(statistics.stdev(all_counts))
        if verbose:
            print("class: All")
            print(f"mean: {means[-1]}")
            print(f"stdev: {stdevs[-1]}")

    StdDevs.plot_stddev(
        means,
        stdevs,
        names=class_output_names + ["ALL"] if summarize else class_output_names,
        output_path=output_path
    )
