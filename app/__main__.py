import argparse
import json
from pathlib import Path

from . import Utils
from .Conversions import Formatter
from .Stats import Plots
from .Val import EvalJob


def main():
    parser = argparse.ArgumentParser(
        prog="Object Detection Tools"
    )
    subparsers = parser.add_subparsers(dest="command", help="Jobs")

    # DATASET FORMATTING AND SPLITTING
    form_parser = subparsers.add_parser("form")
    form_parser.add_argument("output", help="Transformed dataset destination.")
    form_parser.add_argument("images_path", help="Path to images.")
    form_parser.add_argument("annot_path", help="Path to annotations.")

    form_parser.add_argument("-i", "--input_format", default="mung", choices=["mung", "coco", "yolod", "yolos"])
    form_parser.add_argument("-o", "--output_format", default="coco", choices=["mung", "coco", "yolod", "yolos"])
    form_parser.add_argument("--image_format", default="jpg", help="Input image format.")

    form_parser.add_argument("-s", "--split", type=float, default=1.0, help="Train/test split ratio.")

    form_parser.add_argument("--seed", type=int, default=42, help="Seed for dataset shuffling.")
    form_parser.add_argument("--resize", type=int, default=None,
                             help="Resizes images so that the longer side is this many pixels long.")
    form_parser.add_argument("--image_splitting", action="store_true", help="Split images into smaller ones.")

    # global arguments
    form_parser.add_argument("-v", "--verbose", action="store_true", help="Make script verbose")
    form_parser.add_argument("--config", default=None,
                             help="Path to config, see \"default.config\" for example.")

    # DATASET STATISTICS
    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("images_path", help="Path to images.")
    stats_parser.add_argument("annot_path", help="Path to annotations.")

    stats_parser.add_argument("-o", "--output_dir", type=str, default=None, help="If used, plots will be saved here.")
    stats_parser.add_argument("-i", "--input_format", default="mung", choices=["mung", "coco", "yolod", "yolos"])
    stats_parser.add_argument('-j', '--jobs', nargs='+', help="Specify jobs to run, if None, all jobs will be run.",
                              choices=["stddev", "xybin", "whbin", "rect"])

    # global arguments
    stats_parser.add_argument("-v", "--verbose", action="store_true", help="Make script verbose")
    stats_parser.add_argument("--config", default=None,
                              help="Path to config, see \"default.config\" for example.")
    stats_parser.add_argument("--sum", action="store_true", help="Adds \"All\" category to stats.")

    # MODEL VALIDATION
    val_parser = subparsers.add_parser("val")

    val_parser.add_argument("model_path", type=str, help="Path to model.")
    val_parser.add_argument("images_path", help="Path to images.")
    val_parser.add_argument("annot_path", help="Path to annotations.")

    val_parser.add_argument("-i", "--input_format", default="yolod", choices=["mung", "coco", "yolod", "yolos"],
                            help="Validation dataset annotation format.")
    val_parser.add_argument("-m", "--model_type", default="yolod", choices=["yolod", "yolos"],
                            help="Type of model.")

    val_parser.add_argument("-o", "--output_dir", type=str, default=None,
                            help="Path to output directory, if not specified, plot will be shown.")

    val_parser.add_argument("--image_format", default="jpg", help="Input image format.")

    val_parser.add_argument("--overlap", type=float, default=0.25, help="Overlap ratio for image splits.")
    val_parser.add_argument("-c", "--count", type=int, help="How many images the model will be tested on.")
    val_parser.add_argument("-s", "--seed", type=int, default=42, help="Seed for dataset shuffling.")
    val_parser.add_argument("--sum", action="store_true", help="Adds \"All\" category to evaluation.")
    val_parser.add_argument("--iou", type=float, default=0.25,
                            help="Threshold to consider two annotations overlapping while resolving predictions.")

    # global arguments
    val_parser.add_argument("-v", "--verbose", action="store_true", help="Make script verbose")
    val_parser.add_argument("--config", default=None,
                            help="Path to config, see \"default.config\" for example.")

    # CONFIG CHECK
    conf_parser = subparsers.add_parser("confcheck")
    conf_parser.add_argument("config_path", help="Path to config.")

    args = parser.parse_args()

    if args.command == "confcheck":
        with open(args.config_path, "r", encoding="utf8") as f:
            loaded_config = json.load(f)

        Utils.get_mapping_and_names_from_config(loaded_config, verbose=True)
        return 0

    # load config
    if args.config is None:
        with open("configs/default.json", "rt") as f:
            loaded_config = json.load(f)
    else:
        with open(args.config, "r", encoding="utf8") as f:
            loaded_config = json.load(f)

    class_id_mapping, class_output_names = Utils.get_mapping_and_names_from_config(loaded_config)

    if args.command == "form":
        input_f = Formatter.InputFormat.from_string(args.input_format)
        output_f = Formatter.OutputFormat.from_string(args.output_format)

        Formatter.format_dataset(
            # directories
            Path(args.images_path),
            Path(args.annot_path),
            Path(args.output),
            # class ids etc.
            class_reference_table=class_id_mapping,
            class_output_names=class_output_names,
            # formatting
            input_format=input_f,
            output_format=output_f,
            split_ratio=args.split,
            resize=args.resize,
            image_format=args.image_format,
            # image splitting settings
            window_size=tuple(loaded_config["window_size"]),
            overlap_ratio=loaded_config["overlap_ratio"],
            image_splitting=args.image_splitting,
            # others
            seed=args.seed,
            verbose=args.verbose
        )
    elif args.command == "stats":
        Plots.load_and_plot_stats(
            # directories
            Path(args.images_path),
            Path(args.annot_path),
            Formatter.InputFormat.from_string(args.input_format),
            # class ids etc.
            class_reference_table=class_id_mapping,
            class_output_names=class_output_names,
            image_format="jpg",
            jobs=args.jobs,
            # others
            output_dir=Path(args.output_dir) if args.output_dir is not None else None,
            summarize=args.sum,
            verbose=args.verbose
        )

    elif args.command == "val":
        EvalJob.run_f1_scores_vs_iou(
            # input paths
            Path(args.model_path),
            Path(args.images_path),
            Path(args.annot_path),
            # formatting
            Formatter.InputFormat.from_string(args.input_format),
            EvalJob.ModelType.from_string(args.model_type),
            class_output_names,
            iou_threshold=args.iou,
            overlap=args.overlap,
            # optional graph saving
            output_dir=Path(args.output_path) if args.output_path is not None else None,
            summarize=args.sum,
            count=args.count,
            verbose=args.verbose
        )


if __name__ == "__main__":
    main()
