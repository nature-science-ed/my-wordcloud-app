import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

# ページの設定
st.set_page_config(page_title="感想比較分析アプリ", layout="wide")
st.title("振り返り分析：事実と感情の比較")

# 基本的な除外語（分析のノイズになる言葉）
BASE_STOPWORDS = {
    "こと", "もの", "ところ", "今回", "自分", "です", "ます", 
    "そして", "また", "広島大学", "広大", "大学", "見学", "以上", "たち"
}

t = Tokenizer()

def extract_words(text, include_feelings=False):
    words = []
    
    # 思考・変化を表す動詞のリスト
    feeling_verbs = [
        "思う", "感じる", "考える", "知る", "驚く", 
        "わかる", "気づく", "学ぶ", "楽しむ", "納得する"
    ]
    
    # 感動や評価を表す形容詞のリスト
    feeling_adjectives = [
        "面白い", "楽しい", "凄い", "すごい", "嬉しい", 
        "難しい", "珍しい", "不思議", "興味深い", "圧巻"
    ]
    
    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form # 「驚きました」なども「驚く」に変換されます
        
        # 1. 名詞の抽出（常に実行）
        if part == "名詞" and base not in BASE_STOPWORDS and len(base) >= 2:
            words.append(base)
        
        # 2. 感情・思考ワードの抽出（スイッチがオンの時のみ）
        if include_feelings:
            if part == "動詞" and base in feeling_verbs:
                words.append(base)
            if part == "形容詞" and base in feeling_adjectives:
                words.append(base)
                
    return " ".join(words)

# ファイルアップローダー
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    target_col = st.selectbox("分析したい列（感想が書かれた列）を選択してください", df.columns)
    
    if st.button("2種類の分析を実行する"):
        # フォントパス（Streamlit Cloud環境用）
        FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        
        # テキストの結合
        all_text = "\n".join(df[target_col].dropna().astype(str))
        
        # データの生成
        wakati_facts = extract_words(all_text, include_feelings=False)
        wakati_feelings = extract_words(all_text, include_feelings=True)

        # 画面を2分割して表示
        col1, col2 = st.columns(2)

        with col1:
            st.header("① 事実・対象（名詞のみ）")
            st.write("何が印象に残ったか（対象物）を可視化します。")
            wc1 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_facts)
            fig1, ax1 = plt.subplots()
            ax1.imshow(wc1)
            ax1.axis("off")
            st.pyplot(fig1)
            
            buf1 = io.BytesIO()
            wc1.to_image().save(buf1, format='PNG')
            st.download_button("①を画像として保存", data=buf1.getvalue(), file_name="facts_only.png")

        with col2:
            st.header("② 感情・学び（動詞・形容詞入り）")
            st.write("生徒がどう感じ、どう考えたかを可視化します。")
            wc2 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_feelings)
            fig2, ax2 = plt.subplots()
            ax2.imshow(wc2)
            ax2.axis("off")
            st.pyplot(fig2)
            
            buf2 = io.BytesIO()
            wc2.to_image().save(buf2, format='PNG')
            st.download_button("②を画像として保存", data=buf2.getvalue(), file_name="with_feelings.png")

        st.success("分析が完了しました。左右の単語の違いに注目して評価を行ってください。")
