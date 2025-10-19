import json
import io
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from typing import Literal, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from fastmcp import FastMCP, Image

# Matplotlibの日本語設定
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"

mcp = FastMCP("DataAnalysisAssistant")


def load_data(data_source: Literal["sales", "customers"]) -> pd.DataFrame:
    """JSONファイルからデータを読み込み、DataFrameを返す"""
    with open(f"data/{data_source}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


@mcp.tool()
def get_data(
    data_source: Literal["sales", "customers"],
    product_name: Optional[str] = None,
    branch: Optional[str] = None,
    period: Optional[Literal["2025-08", "2025-09"]] = None,
) -> str:
    """
    指定された条件で売上データまたは顧客データをフィルタリングし、JSON文字列として返す。

    Args:
        data_source: データの種類 ('sales' または 'customers')。
        product_name: 製品名（売上データの場合）。
        branch: 支社名。
        period: 期間（'2025-08' または '2025-09'）。

    Returns:
        フィルタリングされたデータのJSON文字列。
    """
    try:
        df = load_data(data_source)

        if branch:
            df = df[df["branch"] == branch]

        if data_source == "sales":
            if product_name:
                df = df[df["product"] == product_name]
            if period:
                if period == "2025-08":
                    df = df[
                        (df["date"] >= datetime(2025, 8, 1))
                        & (df["date"] <= datetime(2025, 8, 31))
                    ]
                elif period == "2025-09":
                    df = df[
                        (df["date"] >= datetime(2025, 9, 1))
                        & (df["date"] <= datetime(2025, 9, 30))
                    ]

        if df.empty:
            return "該当するデータが見つかりませんでした。"

        return df.to_json(orient="records", date_format="iso")
    except Exception as e:
        return f"データ取得中にエラーが発生しました: {e}"


@mcp.tool()
def create_chart_from_json(
    json_data: str,
    chart_type: Literal["line", "bar", "pie", "histogram"],
    x_axis: Optional[str] = None,
    y_axis: Optional[str] = None,
    title: str = "グラフ",
    group_by: Optional[str] = None,
) -> Image | str:
    """
    JSONデータから指定された種類のグラフを生成し、画像として返す。
    ※折れ線グラフにはx_axisとy_axisが必要です。
    ※棒グラフにはx_axisとy_axisが必要です。
    ※円グラフにはgroup_byとy_axisが必要です。
    ※ヒストグラムにはx_axisが必要です。


    Args:
        json_data: グラフ化するデータ（JSON文字列）。
        chart_type: グラフの種類 ('line', 'bar', 'pie', 'histogram')。
        x_axis: X軸に使用する列名。
        y_axis: Y軸に使用する列名。
        title: グラフのタイトル。
        group_by: 集計に使用する列名（円グラフなどで使用）。

    Returns:
        生成されたグラフの画像パス。エラー時はエラーメッセージ。
    """
    try:
        data = json.loads(json_data)
        if not data:
            return "グラフを生成するためのデータがありません。"
        df = pd.DataFrame(data)

        plt.figure(figsize=(10, 6))

        if chart_type == "line":
            if not x_axis or not y_axis:
                return "折れ線グラフにはx_axisとy_axisが必要です。"
            df[x_axis] = pd.to_datetime(df[x_axis])
            df = df.sort_values(by=x_axis)
            plt.plot(df[x_axis], df[y_axis])
            plt.xticks(rotation=45)
        elif chart_type == "bar":
            if not x_axis or not y_axis:
                return "棒グラフにはx_axisとy_axisが必要です。"
            df.groupby(x_axis)[y_axis].sum().plot(kind="bar")
            plt.xticks(rotation=45)
        elif chart_type == "pie":
            if not group_by or not y_axis:
                return "円グラフにはgroup_byとy_axisが必要です。"
            df.groupby(group_by)[y_axis].sum().plot(
                kind="pie", autopct="%1.1f%%", startangle=90
            )
            plt.ylabel("")
        elif chart_type == "histogram":
            if not x_axis:
                return "ヒストグラムにはx_axisが必要です。"
            df[x_axis].plot(kind="hist", bins=10)

        plt.title(title)
        plt.xlabel(x_axis if x_axis else "")
        plt.ylabel(y_axis if y_axis else "")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return Image(data=buf.getvalue(), format="png")
    except Exception as e:
        return f"グラフ生成中にエラーが発生しました: {e}"


@mcp.tool()
def send_notification_email() -> str:
    """
    タスクが完了したときに通知メールを送信する。
    ※ユーザーから明示的にメール送信の指示があった場合のみ実行すること。

    Args:
    Returns:
        メール送信のステータスメッセージ。
    """
    host = "mailhog"
    port = 1025

    msg = MIMEText("完了通知メールのToolが実行された結果、このメールが送信されました。")
    msg["Subject"] = "タスク完了"
    msg["From"] = "from@example.com"
    msg["To"] = "to@example.com"

    with smtplib.SMTP(host, port) as s:
        s.send_message(msg)
    return f"メール送信に成功しました"


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=9000)
