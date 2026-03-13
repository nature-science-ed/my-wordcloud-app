import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

# ページの設定
st.set_page_config(page_title="感想ワードクラウド作成")
st.title("📝 感想ワードクラウド作成")

# ストップワードの設定
STOPWORDS = {
    "こと","もの","ところ","今回","自分",
    "思う","感じる","する","いる","なる",
    "です","ます","そして","また"
}

t = Tokenizer()

def extract_words(text):
    words = []
    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        if part == "名詞" and base not in STOPWORDS and len(base) >= 2:
            words.append(base)
    return " ".join(words)

# ファイルアップローダー
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    # ファイルの読み込み
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # 列の選択（"text"列を探す）
    target_col = st.selectbox("分析したい列を選択してください", df.columns)
    
    if st.button("ワードクラウドを生成"):
        all_text = "\n".join(df[target_col].dropna().astype(str))
        wakati = extract_words(all_text)

        # ここを以下のように修正します
        # Linux環境での日本語フォントの標準的なパスを指定します
        FONT_PATH_JP = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

        wc = WordCloud(
            font_path=FONT_PATH_JP, # ここでフォントを指定！
            background_color="white",
            width=1600,
            height=1000,
            collocations=False
        ).generate(wakati)

        # 表示
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.imshow(wc)
        ax.axis("off")
        st.pyplot(fig)
        
        # 保存用
        img_buf = io.BytesIO()
        wc.to_image().save(img_buf, format='PNG')
        st.download_button("画像を保存", data=img_buf.getvalue(), file_name="wordcloud.png")
