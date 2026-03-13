import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

# ページの設定
st.set_page_config(page_title="感想比較ワードクラウド", layout="wide")
st.title("📊 振り返り分析：事実と感想の比較")

# 基本的な除外語（助詞や名詞のノイズ）
BASE_STOPWORDS = {
    "こと", "もの", "ところ", "今回", "自分", "です", "ます", 
    "そして", "また", "広島大学", "広大", "大学", "見学", "以上"
}

t = Tokenizer()

def extract_words(text, include_feelings=False):
    words = []
    # 「思う」「感じる」などの感情語リスト
    feeling_verbs = ["思う", "感じる", "考える", "知る", "驚く"]
    
    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        
        # 1. 基本的な名詞の抽出
        if part == "名詞" and base not in BASE_STOPWORDS and len(base) >= 2:
            words.append(base)
        
        # 2. 感情語を含める設定の場合、動詞もチェックして追加
        if include_feelings:
            if part == "動詞" and base in feeling_verbs:
                words.append(base)
                
    return " ".join(words)

# ファイルアップローダー
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    target_col = st.selectbox("分析したい列を選択してください", df.columns)
    
    if st.button("2種類のワードクラウドを生成して比較する"):
        # フォントパス（Streamlit Cloud環境用）
        FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        
        # データ準備
        all_text = "\n".join(df[target_col].dropna().astype(str))
        
        # 左側：事実・キーワード中心（感情語なし）
        wakati_standard = extract_words(all_text, include_feelings=False)
        # 右側：心理・学びのプロセス（感情語あり）
        wakati_with_feelings = extract_words(all_text, include_feelings=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("① 事実・知識（名詞のみ）")
            wc1 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_standard)
            fig1, ax1 = plt.subplots()
            ax1.imshow(wc1)
            ax1.axis("off")
            st.pyplot(fig1)
            
            # 保存ボタン
            buf1 = io.BytesIO()
            wc1.to_image().save(buf1, format='PNG')
            st.download_button("①を保存", data=buf1.getvalue(), file_name="facts_only.png")

        with col2:
            st.subheader("② 学びのプロセス（感情語あり）")
            wc2 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_with_feelings)
            fig2, ax2 = plt.subplots()
            ax2.imshow(wc2)
            ax2.axis("off")
            st.pyplot(fig2)
            
            # 保存ボタン
            buf2 = io.BytesIO()
            wc2.to_image().save(buf2, format='PNG')
            st.download_button("②を保存", data=buf2.getvalue(), file_name="with_feelings.png")

        st.info("左側は「何について学んだか」を、右側は「どう考え・感じたか」を分析するのに適しています。")
