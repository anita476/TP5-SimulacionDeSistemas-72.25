import matplotlib

FONT_SIZE = 20
SAVE_DPI = 300

BLUE = "#0072B2"
VERMILLION = "#FF7003"
GREEN = "#009E73"
PURPLE = "#CC79A7"
RED = "#DB2B2B"
VIOLET = "#6E00B7"


def apply_academic_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": FONT_SIZE,
            "axes.labelsize": FONT_SIZE,
            "axes.titlesize": FONT_SIZE,
            "axes.linewidth": 1.15,
            "axes.formatter.use_mathtext": True,
            "axes.formatter.limits": (-2, 4),
            "xtick.labelsize": FONT_SIZE,
            "ytick.labelsize": FONT_SIZE,
            "xtick.major.size": 6,
            "ytick.major.size": 6,
            "xtick.major.width": 1.1,
            "ytick.major.width": 1.1,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.fontsize": FONT_SIZE,
            "legend.frameon": True,
            "legend.fancybox": False,
            "legend.edgecolor": "0.35",
            "legend.framealpha": 1.0,
            "legend.borderpad": 0.4,
            "legend.handlelength": 1.6,
            "mathtext.fontset": "stix",
            "lines.linewidth": 1.8,
            "lines.markersize": 8.5,
            "errorbar.capsize": 4.5,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.dpi": SAVE_DPI,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_axes(ax, xlabel: str, ylabel: str) -> None:
    ax.set_xlabel(xlabel, labelpad=10)
    ax.set_ylabel(ylabel, labelpad=10)
    ax.xaxis.label.set_clip_on(False)
    ax.yaxis.label.set_clip_on(False)
    ax.grid(False)
    ax.tick_params(axis="both", which="major", direction="out", top=False, right=False)
    ax.minorticks_off()
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(matplotlib.rcParams["axes.linewidth"])
