import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import rasterio


"""Compare flow-status parameter runs and create summary charts."""


def find_project_root(start_path):
    for path in [start_path, *start_path.parents]:
        if (path / "Data").exists() and (path / "Output").exists():
            return path
    raise FileNotFoundError("Could not find project root containing Data and Output directories.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
NODATA = 255

PARAMETERS = (
    "water_ratio_threshold",
    "use_connectivity",
    "min_connected_water_cells",
    "perennial_month_threshold",
    "perennial_ratio_threshold",
)

VARY_ALIASES = {
    "water_ratio": "water_ratio_threshold",
    "water_ratio_threshold": "water_ratio_threshold",
    "WATER_RATIO_THRESHOLD": "water_ratio_threshold",
    "connectivity": "use_connectivity",
    "use_connectivity": "use_connectivity",
    "USE_CONNECTIVITY": "use_connectivity",
    "min_conn": "min_connected_water_cells",
    "min_connected_water_cells": "min_connected_water_cells",
    "MIN_CONNECTED_WATER_CELLS": "min_connected_water_cells",
    "perennial": "perennial_month_threshold",
    "perennial_month_threshold": "perennial_month_threshold",
    "PERENNIAL_MONTH_THRESHOLD": "perennial_month_threshold",
    "perennial_ratio": "perennial_ratio_threshold",
    "perennial_ratio_threshold": "perennial_ratio_threshold",
    "PERENNIAL_RATIO_THRESHOLD": "perennial_ratio_threshold",
}

RUN_LABEL_RE = re.compile(
    r"^water_ratio_(?P<water_ratio>\d+(?:\.\d+)?)_"
    r"min_conn_(?P<min_conn>na|\d+)_"
    r"perennial_(?P<perennial>\d+)_"
    r"perennial_ratio_(?P<perennial_ratio>\d+(?:\.\d+)?)$"
)

CLASS_NAMES = {
    0: "non_water",
    1: "intermittent",
    2: "perennial",
    NODATA: "nodata",
}

PLOT_METRICS = {
    "water_ratio_threshold": (
        ("non_water_cells", "0 non-water", "#b8b8b8"),
        ("water_cells", "1+2 water", "#2f80ed"),
    ),
    "perennial_month_threshold": (
        ("intermittent_cells", "1 intermittent", "#f2994a"),
        ("perennial_cells", "2 perennial", "#2f80ed"),
    ),
    "perennial_ratio_threshold": (
        ("intermittent_cells", "1 intermittent", "#f2994a"),
        ("perennial_cells", "2 perennial", "#2f80ed"),
    ),
    "use_connectivity": (
        ("non_water_cells", "0 non-water", "#b8b8b8"),
        ("water_cells", "1+2 water", "#2f80ed"),
    ),
    "min_connected_water_cells": (
        ("water_cells", "1+2 water", "#2f80ed"),
        ("intermittent_cells", "1 intermittent", "#f2994a"),
        ("perennial_cells", "2 perennial", "#1f5fbf"),
    ),
}

WATER_ONLY_METRICS = (
    ("water_cells", "1+2 water", "#2f80ed"),
    ("intermittent_cells", "1 intermittent", "#f2994a"),
    ("perennial_cells", "2 perennial", "#1f5fbf"),
)

PARAMETER_LABELS = {
    "water_ratio_threshold": "WATER_RATIO_THRESHOLD",
    "use_connectivity": "USE_CONNECTIVITY",
    "min_connected_water_cells": "MIN_CONNECTED_WATER_CELLS",
    "perennial_month_threshold": "PERENNIAL_MONTH_THRESHOLD",
    "perennial_ratio_threshold": "PERENNIAL_RATIO_THRESHOLD",
}


def parse_run_label(label):
    match = RUN_LABEL_RE.match(label)
    if not match:
        return None

    params = match.groupdict()
    min_connected_water_cells = None if params["min_conn"] == "na" else int(params["min_conn"])
    return {
        "water_ratio_threshold": float(params["water_ratio"]),
        "use_connectivity": min_connected_water_cells is not None,
        "min_connected_water_cells": min_connected_water_cells,
        "perennial_month_threshold": int(params["perennial"]),
        "perennial_ratio_threshold": float(params["perennial_ratio"]),
    }


def parameter_sort_value(value):
    if value is None:
        return (-1, "na")
    return (0, value)


def format_parameter_value(value):
    if value is None:
        return "na"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def default_mosaic_root(region):
    if region == "china":
        return PROJECT_ROOT / "Output" / "ChinaFlowStatusMosaic"
    if region == "global":
        return PROJECT_ROOT / "Output" / "GlobalFlowStatusMosaic"
    raise ValueError(f"Unsupported region: {region}")


def default_runs_root(region):
    if region == "china":
        return PROJECT_ROOT / "Output" / "ChinaFlowStatusRuns"
    if region == "global":
        return PROJECT_ROOT / "Output" / "GlobalFlowStatusRuns"
    raise ValueError(f"Unsupported region: {region}")


def discover_mosaic_runs(mosaic_root):
    runs = []
    if not mosaic_root.exists():
        return runs

    for run_dir in sorted(path for path in mosaic_root.iterdir() if path.is_dir()):
        params = parse_run_label(run_dir.name)
        if params is None:
            continue

        tif_paths = sorted(run_dir.glob("*.tif"))
        if not tif_paths:
            continue

        runs.append(
            {
                "name": run_dir.name,
                "params": params,
                "kind": "mosaic",
                "path": tif_paths[0],
            }
        )
    return runs


def discover_tile_runs(runs_root):
    runs = []
    if not runs_root.exists():
        return runs

    for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        params = parse_run_label(run_dir.name)
        if params is None:
            continue

        tile_dir = run_dir / "tiles"
        tile_paths = sorted(tile_dir.glob("flow_status_*.tif"))
        if not tile_paths:
            continue

        runs.append(
            {
                "name": run_dir.name,
                "params": params,
                "kind": "tiles",
                "path": tile_dir,
                "tile_paths": tile_paths,
            }
        )
    return runs


def discover_runs(region, mosaic_root=None, runs_root=None, prefer="mosaic"):
    mosaic_root = Path(mosaic_root) if mosaic_root else default_mosaic_root(region)
    runs_root = Path(runs_root) if runs_root else default_runs_root(region)

    mosaic_runs = discover_mosaic_runs(mosaic_root)
    tile_runs = discover_tile_runs(runs_root)

    by_name = {}
    ordered_sources = (mosaic_runs, tile_runs) if prefer == "mosaic" else (tile_runs, mosaic_runs)
    for source_runs in ordered_sources:
        for run in source_runs:
            by_name.setdefault(run["name"], run)
    return sorted(by_name.values(), key=lambda run: run["name"])


def raster_paths_for_run(run):
    if run["kind"] == "mosaic":
        return [run["path"]]
    return run["tile_paths"]


def load_raster(path):
    with rasterio.open(path) as src:
        return src.read(1)


def summarize_array(data):
    counts = Counter(data.reshape(-1).tolist())
    non_water = int(counts.get(0, 0))
    intermittent = int(counts.get(1, 0))
    perennial = int(counts.get(2, 0))
    nodata = int(counts.get(NODATA, 0))
    total = int(data.size)
    valid = total - nodata
    water = intermittent + perennial

    def ratio(count, denominator):
        return float(count / denominator) if denominator else 0.0

    return {
        "total_cells": total,
        "valid_cells": valid,
        "nodata_cells": nodata,
        "non_water_cells": non_water,
        "water_cells": water,
        "intermittent_cells": intermittent,
        "perennial_cells": perennial,
        "water_ratio_valid": ratio(water, valid),
        "intermittent_ratio_water": ratio(intermittent, water),
        "perennial_ratio_water": ratio(perennial, water),
        "perennial_ratio_valid": ratio(perennial, valid),
    }


def add_summary_totals(total, summary):
    for key, value in summary.items():
        total[key] += value


def summarize_run(run):
    total = defaultdict(float)
    for path in raster_paths_for_run(run):
        add_summary_totals(total, summarize_array(load_raster(path)))

    total["water_ratio_valid"] = safe_divide(total["water_cells"], total["valid_cells"])
    total["intermittent_ratio_water"] = safe_divide(total["intermittent_cells"], total["water_cells"])
    total["perennial_ratio_water"] = safe_divide(total["perennial_cells"], total["water_cells"])
    total["perennial_ratio_valid"] = safe_divide(total["perennial_cells"], total["valid_cells"])

    result = dict(total)
    for key, value in result.items():
        if key.endswith("_cells") or key == "total_cells":
            result[key] = int(value)
    return result


def safe_divide(numerator, denominator):
    return float(numerator / denominator) if denominator else 0.0


def compare_arrays(base, other):
    if base.shape != other.shape:
        raise ValueError(f"Raster shapes differ: {base.shape} vs {other.shape}")

    valid = (base != NODATA) & (other != NODATA)
    base_water = (base == 1) | (base == 2)
    other_water = (other == 1) | (other == 2)
    base_perennial = base == 2
    other_perennial = other == 2

    changed = valid & (base != other)
    added_water = valid & (~base_water) & other_water
    lost_water = valid & base_water & (~other_water)
    common_water = valid & base_water & other_water
    intermittent_to_perennial = valid & (base == 1) & (other == 2)
    perennial_to_intermittent = valid & (base == 2) & (other == 1)

    transition_counts = {}
    for from_value in (0, 1, 2):
        for to_value in (0, 1, 2):
            key = f"{CLASS_NAMES[from_value]}_to_{CLASS_NAMES[to_value]}"
            transition_counts[key] = int(np.sum(valid & (base == from_value) & (other == to_value)))

    valid_count = int(np.sum(valid))
    base_water_count = int(np.sum(valid & base_water))
    other_water_count = int(np.sum(valid & other_water))
    base_perennial_count = int(np.sum(valid & base_perennial))
    other_perennial_count = int(np.sum(valid & other_perennial))

    return {
        "compared_valid_cells": valid_count,
        "changed_cells": int(np.sum(changed)),
        "changed_ratio_valid": safe_divide(int(np.sum(changed)), valid_count),
        "base_water_cells": base_water_count,
        "other_water_cells": other_water_count,
        "water_delta_cells": other_water_count - base_water_count,
        "water_delta_pct_of_base": safe_divide(other_water_count - base_water_count, base_water_count),
        "added_water_cells": int(np.sum(added_water)),
        "lost_water_cells": int(np.sum(lost_water)),
        "common_water_cells": int(np.sum(common_water)),
        "base_perennial_cells": base_perennial_count,
        "other_perennial_cells": other_perennial_count,
        "perennial_delta_cells": other_perennial_count - base_perennial_count,
        "perennial_delta_pct_of_base": safe_divide(other_perennial_count - base_perennial_count, base_perennial_count),
        "intermittent_to_perennial_cells": int(np.sum(intermittent_to_perennial)),
        "perennial_to_intermittent_cells": int(np.sum(perennial_to_intermittent)),
        **transition_counts,
    }


def compare_runs(base, other):
    base_paths = raster_paths_for_run(base)
    other_paths = raster_paths_for_run(other)

    if base["kind"] == "tiles" or other["kind"] == "tiles":
        base_by_name = {path.name: path for path in base_paths}
        other_by_name = {path.name: path for path in other_paths}
        common_names = sorted(base_by_name.keys() & other_by_name.keys())
        if not common_names:
            raise ValueError(f"No common tile names for {base['name']} and {other['name']}")

        total = defaultdict(float)
        for name in common_names:
            metrics = compare_arrays(load_raster(base_by_name[name]), load_raster(other_by_name[name]))
            for key, value in metrics.items():
                total[key] += value

        result = dict(total)
        result["changed_ratio_valid"] = safe_divide(result["changed_cells"], result["compared_valid_cells"])
        result["water_delta_pct_of_base"] = safe_divide(result["water_delta_cells"], result["base_water_cells"])
        result["perennial_delta_pct_of_base"] = safe_divide(result["perennial_delta_cells"], result["base_perennial_cells"])
        result["common_tile_count"] = len(common_names)
    else:
        result = compare_arrays(load_raster(base_paths[0]), load_raster(other_paths[0]))
        result["common_tile_count"] = None

    for key, value in list(result.items()):
        if key.endswith("_cells") or key == "common_tile_count":
            result[key] = None if value is None else int(value)
    return result


def group_runs_for_parameter(runs, parameter):
    groups = defaultdict(list)
    for run in runs:
        if parameter == "min_connected_water_cells" and not run["params"]["use_connectivity"]:
            continue

        excluded = {parameter}
        if parameter == "use_connectivity":
            excluded.add("min_connected_water_cells")

        key = tuple((name, run["params"][name]) for name in PARAMETERS if name not in excluded)
        groups[key].append(run)
    return {
        key: sorted(group, key=lambda run: parameter_sort_value(run["params"][parameter]))
        for key, group in groups.items()
        if len(group) >= 2
    }


def row_with_params(prefix, params):
    return {
        f"{prefix}_{name}": format_parameter_value(params[name])
        for name in PARAMETERS
        if name in params
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    for row in rows[1:]:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(runs, parameter):
    summaries = []
    summary_by_name = {}
    for run in runs:
        summary = summarize_run(run)
        summary_by_name[run["name"]] = summary
        summaries.append(
            {
                "run": run["name"],
                "source_kind": run["kind"],
                "source_path": str(run["path"]),
                **row_with_params("param", run["params"]),
                **summary,
            }
        )

    comparison_rows = []
    groups = group_runs_for_parameter(runs, parameter)
    for group_key, group in groups.items():
        fixed_params = {name: value for name, value in group_key}
        if parameter == "use_connectivity":
            false_runs = [run for run in group if not run["params"]["use_connectivity"]]
            true_runs = [run for run in group if run["params"]["use_connectivity"]]
            pairs = [(false_run, true_run) for false_run in false_runs for true_run in true_runs]
        else:
            pairs = [(group[index], group[index + 1]) for index in range(len(group) - 1)]

        for base, other in pairs:
            metrics = compare_runs(base, other)
            comparison_rows.append(
                {
                    "vary_parameter": parameter,
                    **row_with_params("fixed", fixed_params),
                    "base_run": base["name"],
                    "other_run": other["name"],
                    "base_value": format_parameter_value(base["params"][parameter]),
                    "other_value": format_parameter_value(other["params"][parameter]),
                    **row_with_params("base_param", base["params"]),
                    **row_with_params("other_param", other["params"]),
                    **metrics,
                }
            )

    return {
        "parameter": parameter,
        "run_count": len(runs),
        "comparison_count": len(comparison_rows),
        "summaries": summaries,
        "comparisons": comparison_rows,
    }


def run_axis_label(run, parameter):
    value = format_parameter_value(run["params"][parameter])
    if parameter == "use_connectivity" and run["params"]["use_connectivity"]:
        return f"{value}\nmin={format_parameter_value(run['params']['min_connected_water_cells'])}"
    return value


def fixed_group_label(fixed_params):
    return "\n".join(
        f"{PARAMETER_LABELS[name]} = {format_parameter_value(value)}"
        for name, value in fixed_params.items()
    )


def plot_grouped_bars(path, title, condition_text, x_labels, metric_specs, values_by_metric, ylabel):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.arange(len(x_labels), dtype=float)
    width = min(0.8 / max(len(metric_specs), 1), 0.32)

    fig_width = max(10.5, len(x_labels) * 1.35 + 3.2)
    fig, (ax, info_ax) = plt.subplots(
        1,
        2,
        figsize=(fig_width, 5.2),
        dpi=180,
        gridspec_kw={"width_ratios": [4.4, 1.6]},
    )
    for metric_index, (metric_name, label, color) in enumerate(metric_specs):
        offset = (metric_index - (len(metric_specs) - 1) / 2) * width
        ax.bar(x + offset, values_by_metric[metric_name], width=width, label=label, color=color)

    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=0)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)

    info_ax.axis("off")
    info_ax.set_title("Conditions", fontsize=11, loc="left", pad=10)
    info_ax.text(
        0.0,
        0.96,
        condition_text,
        transform=info_ax.transAxes,
        va="top",
        ha="left",
        fontsize=9.5,
        linespacing=1.55,
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#f7f7f7",
            "edgecolor": "#d0d0d0",
            "linewidth": 0.8,
        },
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def generate_visualizations(runs, report, parameter, output_dir):
    summary_by_run = {row["run"]: row for row in report["summaries"]}
    groups = group_runs_for_parameter(runs, parameter)
    metric_specs = PLOT_METRICS[parameter]
    chart_paths = []
    plot_dir = output_dir / "plots"

    for group_index, (group_key, group) in enumerate(groups.items(), start=1):
        fixed_params = {name: value for name, value in group_key}
        x_labels = [run_axis_label(run, parameter) for run in group]
        group_summaries = [summary_by_run[run["name"]] for run in group]

        counts_by_metric = {
            metric_name: [summary[metric_name] for summary in group_summaries]
            for metric_name, _, _ in metric_specs
        }
        ratios_by_metric = {
            metric_name: [
                safe_divide(summary[metric_name], summary["valid_cells"])
                for summary in group_summaries
            ]
            for metric_name, _, _ in metric_specs
        }

        fixed_label = fixed_group_label(fixed_params)
        title = PARAMETER_LABELS[parameter]
        count_path = plot_dir / f"group_{group_index:02d}_{parameter}_counts.png"
        ratio_path = plot_dir / f"group_{group_index:02d}_{parameter}_ratios.png"

        plot_grouped_bars(
            count_path,
            title,
            fixed_label,
            x_labels,
            metric_specs,
            counts_by_metric,
            "cells",
        )
        plot_grouped_bars(
            ratio_path,
            title,
            fixed_label,
            x_labels,
            metric_specs,
            ratios_by_metric,
            "ratio of valid cells",
        )
        chart_paths.extend([str(count_path), str(ratio_path)])

        water_counts_by_metric = {
            metric_name: [summary[metric_name] for summary in group_summaries]
            for metric_name, _, _ in WATER_ONLY_METRICS
        }
        water_ratios_by_metric = {
            metric_name: [
                safe_divide(summary[metric_name], summary["water_cells"])
                for summary in group_summaries
            ]
            for metric_name, _, _ in WATER_ONLY_METRICS
        }
        water_count_path = plot_dir / f"group_{group_index:02d}_{parameter}_water_only_counts.png"
        water_ratio_path = plot_dir / f"group_{group_index:02d}_{parameter}_water_only_ratios.png"

        plot_grouped_bars(
            water_count_path,
            f"{title} water only",
            fixed_label,
            x_labels,
            WATER_ONLY_METRICS,
            water_counts_by_metric,
            "water cells",
        )
        plot_grouped_bars(
            water_ratio_path,
            f"{title} water only",
            fixed_label,
            x_labels,
            WATER_ONLY_METRICS,
            water_ratios_by_metric,
            "ratio of water cells",
        )
        chart_paths.extend([str(water_count_path), str(water_ratio_path)])

    return chart_paths


def main():
    parser = argparse.ArgumentParser(
        description="Compare flow-status outputs while varying one parameter and keeping the others fixed."
    )
    parser.add_argument("--region", choices=("china", "global"), default="china")
    parser.add_argument(
        "--vary",
        choices=tuple(VARY_ALIASES),
        default="MIN_CONNECTED_WATER_CELLS",
        help="Parameter to compare. Accepts the original constant names or short aliases.",
    )
    parser.add_argument("--mosaic-root", type=Path, default=None)
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--prefer", choices=("mosaic", "tiles"), default="mosaic")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_ROOT / "Output" / "FlowStatusComparisons",
    )
    args = parser.parse_args()

    vary_parameter = VARY_ALIASES[args.vary]

    runs = discover_runs(args.region, args.mosaic_root, args.runs_root, args.prefer)
    if not runs:
        raise FileNotFoundError("No comparable run directories found.")

    report = build_report(runs, vary_parameter)
    label = f"{args.region}_compare_{vary_parameter}"
    output_dir = args.out_dir / label
    summary_csv = output_dir / "run_summaries.csv"
    comparison_csv = output_dir / "comparisons.csv"
    report_json = output_dir / "report.json"

    write_csv(summary_csv, report["summaries"])
    write_csv(comparison_csv, report["comparisons"])
    output_dir.mkdir(parents=True, exist_ok=True)
    report["plots"] = generate_visualizations(runs, report, vary_parameter, output_dir)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Runs found: {report['run_count']}")
    print(f"Pair comparisons: {report['comparison_count']}")
    print(f"Saved run summaries: {summary_csv}")
    print(f"Saved comparisons: {comparison_csv}")
    print(f"Saved plots: {output_dir / 'plots'}")
    print(f"Saved JSON report: {report_json}")


if __name__ == "__main__":
    main()
