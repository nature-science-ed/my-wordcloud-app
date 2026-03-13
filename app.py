import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

# ページの設定
st.set_page_config(page_title="振り返り分析・評価アプリ", layout="wide")
st.title("📊 振り返り分析と目標達成度評価")

# 基本的な除外語
BASE_STOPWORDS = {"こと", "もの", "ところ", "今回", "自分", "です", "ます", "そして", "また", "以上", "たち"}

t = Tokenizer()

def extract_words(text, include_feelings=False):
    words = []
    feeling_verbs = ["思う", "感じる", "考える", "知る", "驚く", "わかる", "気づく", "学ぶ", "楽しむ", "納得する"]
    feeling_adjectives = ["面白い", "楽しい", "凄い", "すごい", "嬉しい", "難しい", "珍しい", "不思議", "興味深い", "圧巻"]
    
    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        if part == "名詞" and base not in BASE_STOPWORDS and len(base) >= 2:
            words.append(base)
        if include_feelings:
            if part in ["動詞", "形容詞"] and (base in feeling_verbs or base in feeling_adjectives):
                words.append(base)
    return " ".join(words)

# --- 入力セクション ---
st.sidebar.header("📋 行事の設定")
goal_1 = st.sidebar.text_area("ねらい1（例：科学への興味）", "最先端の科学研究に触れ、興味・関心を高める。")
goal_2 = st.sidebar.text_area("ねらい2（例：将来の進路）", "大学での学びを知り、将来の進路について考えるきっかけとする。")

uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    target_col = st.selectbox("分析したい列を選択してください", df.columns)
    
    if st.button("分析と評価を実行"):
        FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        all_text = "\n".join(df[target_col].dropna().astype(str))
        
        wakati_facts = extract_words(all_text, include_feelings=False)
        wakati_feelings = extract_words(all_text, include_feelings=True)

        # 画面表示
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("① 事実・対象（名詞のみ）")
            wc1 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_facts)
            st.image(wc1.to_array())
        with col2:
            st.subheader("② 感情・学び（動詞・形容詞入り）")
            wc2 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_feelings)
            st.image(wc2.to_array())

        # --- 自動評価ロジック ---
        st.divider()
        st.header("📝 設定された「ねらい」に対する評価")

        def evaluate_goal(goal_text, found_words, feeling_words):
            # ねらいの中からキーワード（名詞）を抽出
            goal_keywords = [t.base_form for t in t.tokenize(goal_text) if t.part_of_speech.startswith("名詞") and len(t.base_form) >= 2]
            # 感想の中にねらいのキーワードが含まれているか
            match_keywords = [w for w in goal_keywords if w in found_words]
            # 感情語が含まれているか
            has_feelings = any(w in feeling_words for w in ["すごい", "面白い", "驚く", "わかる", "思う"])
            
            if len(match_keywords) > 0 and has_feelings:
                return "🟢 **【達成】** ねらいに関連する言葉と、それに対する主観的な反応の両方が確認できます。学びが深まっています。"
            elif len(match_keywords) > 0:
                return "🟡 **【概ね達成】** 内容の理解は進んでいますが、感情的な反応や自分事としての捉え方がやや不足しています。"
            else:
                return "⚪ **【要フォロー】** 感想の中にねらいに直結するキーワードが少ないようです。事後指導で焦点を絞る必要があります。"

        e_col1, e_col2 = st.columns(2)
        with e_col1:
            st.write(f"**ねらい1:** {goal_1}")
            st.info(evaluate_goal(goal_1, wakati_facts, wakati_feelings))
        with e_col2:
            st.write(f"**ねらい2:** {goal_2}")
            st.info(evaluate_goal(goal_2, wakati_facts, wakati_feelings))
