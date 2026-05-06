import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


INPUT_MD = "data.md"
OUTPUT_DIR = "figures"
OUTPUT_PNG = os.path.join(OUTPUT_DIR, "new_accounts.png")
OUTPUT_SVG = os.path.join(OUTPUT_DIR, "new_accounts.svg")


def extract_first_markdown_table(md_path: str) -> pd.DataFrame:
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    table_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            in_table = True
        elif in_table:
            break

    if len(table_lines) < 3:
        raise ValueError("未找到有效的 Markdown 表格。")

    header_line = table_lines[0]
    data_lines = table_lines[2:]

    columns = [x.strip() for x in header_line.strip("|").split("|")]

    rows = []
    for line in data_lines:
        parts = [x.strip() for x in line.strip("|").split("|")]
        if len(parts) == len(columns):
            rows.append(parts)

    return pd.DataFrame(rows, columns=columns)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    date_col = df.columns[0]
    value_col = df.columns[1]

    df = df.copy()

    df[value_col] = (
        df[value_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"([-+]?\d*\.?\d+)")[0]
        .astype(float)
    )

    df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m", errors="coerce")
    df = df.dropna(subset=[date_col, value_col])
    df = df.sort_values(date_col)

    return df.rename(columns={date_col: "date", value_col: "new_accounts"})


def configure_chinese_font():
    candidate_fonts = [
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
    ]

    available_fonts = {f.name for f in mpl.font_manager.fontManager.ttflist}

    for font in candidate_fonts:
        if font in available_fonts:
            plt.rcParams["font.sans-serif"] = [font]
            break

    plt.rcParams["axes.unicode_minus"] = False


def plot_chart(df: pd.DataFrame):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    configure_chinese_font()

    latest_date = df["date"].max().strftime("%Y-%m")
    latest_value = df.loc[df["date"].idxmax(), "new_accounts"]

    plt.figure(figsize=(12, 6.5))

    plt.plot(
        df["date"],
        df["new_accounts"],
        marker="o",
        linewidth=2,
        markersize=5,
        label="月度新开户数量",
    )

    if len(df) >= 3:
        df["ma3"] = df["new_accounts"].rolling(3).mean()
        plt.plot(
            df["date"],
            df["ma3"],
            linewidth=2,
            linestyle="--",
            label="3个月移动平均",
        )

    plt.annotate(
        f"{latest_date}\n{latest_value:.2f}",
        xy=(df["date"].max(), latest_value),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=10,
        arrowprops=dict(arrowstyle="->", linewidth=1),
    )

    plt.title("账户新开户数量月度趋势", fontsize=16, pad=16)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("账户新开户数量，万户", fontsize=12)
    plt.legend(frameon=False)
    plt.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    plt.savefig(OUTPUT_SVG, bbox_inches="tight")
    plt.close()


def main():
    raw_df = extract_first_markdown_table(INPUT_MD)
    df = clean_data(raw_df)
    plot_chart(df)

    print(f"已生成图表：{OUTPUT_PNG}")
    print(f"已生成图表：{OUTPUT_SVG}")


if __name__ == "__main__":
    main()
