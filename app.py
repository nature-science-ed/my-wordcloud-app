import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

# 1. ページの設定（横幅を広く使い、タイトルにアイコンを追加）
st.set_page_config(page_title="振り返り分析・詳細評価アプリ", layout="wide")
st.title("📊 行事振り返り：多角的分離と目標達成度評価")

# 2. 基本的な除外語（ストップワード）の設定
BASE_STOPWORDS = {
    "こと", "もの", "ところ", "今回", "自分", "です", "ます", 
    "そして", "また", "以上", "たち", "広島大学", "広大", 
    "大学", "見学", "施設", "センター"
}

t = Tokenizer()

# 3. 単語抽出エンジンの定義
def extract_words(text, include_feelings=False):
    words = []
    # 思考・変化を表す動詞
    feeling_verbs = [
        "思う", "感じる", "考える", "知る", "驚く", 
        "わかる", "気づく", "学ぶ", "楽しむ", "納得する"
    ]
    # 感動や評価を表す形容詞
    feeling_adjectives = [
        "面白い", "楽しい", "凄い", "すごい", "嬉しい", 
        "難しい", "珍しい", "不思議", "興味深い", "圧巻"
    ]
    
    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        
        # 名詞の抽出
        if part == "名詞" and base not in BASE_STOPWORDS and len(base) >= 2:
            words.append(base)
        
        # 感情・思考・評価ワードの抽出（スイッチがオンの時のみ）
        if include_feelings:
            if part == "動詞" and base in feeling_verbs:
                words.append(base)
            if part == "形容詞" and base in feeling_adjectives:
                words.append(base)
                
    return " ".join(words)

# 4. 詳細な文章評価を生成するロジック
def generate_detailed_evaluation(goal_text, found_facts, found_feelings):
    # ねらいの中から名詞（キーワード）を自動抽出
    goal_keywords = [tk.base_form for tk in t.tokenize(goal_text) 
                     if tk.part_of_speech.startswith("名詞") and len(tk.base_form) >= 2]
    match_facts = [w for w in goal_keywords if w in found_facts]
    
    # 学びの深さを表すワードを抽出
    matched_feelings = [w for w in ["思う", "考える", "知る", "驚く", "わかる", "面白い", "不思議"] 
                        if w in found_feelings]
    
    # 評価文の構築
    evaluation_text = ""
    
    if len(match_facts) > 0:
        evaluation_text += f"生徒の振り返りにおいて、ねらいに直結するキーワードである「{', '.join(match_facts[:3])}」が有意に出現しています。これは、対象に対する客観的な理解が定着していることを示しています。 "
    else:
        evaluation_text += "ねらいに関する直接的な語彙は少なめですが、全体として具体的な事象への言及は見られます。 "

    if len(matched_feelings) > 0:
        evaluation_text += f"また、「{', '.join(matched_feelings[:2])}」といった動詞や形容詞が併せて見られることから、単なる見学に留まらず、自身の思考や感性を働かせた「深い学び」へと繋がっていると評価できます。 "
    
    if any(w in found_facts for w in ["将来", "進路", "自分", "勉強"]):
        evaluation_text += "特に、学びを自己の進路や将来像に関連付ける記述が見られる点は、キャリア形成への動機付けとして高い教育効果があったと言えます。"

    return evaluation_text

# 5. サイドバー：ねらいの入力
st.sidebar.header("📋 行事のねらい設定")
st.sidebar.info("ここに現在の行事の目標を入力してください。")
goal_1 = st.sidebar.text_area("ねらい1", "最先端の科学研究に触れ、興味・関心を高める。")
goal_2 = st.sidebar.text_area("ねらい2", "大学での学びを知り、将来の進路について考えるきっかけとする。")

# 6. メイン画面：ファイルアップロード
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    # ファイル読み込み
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    target_col = st.selectbox("分析したい列（感想列）を選択してください", df.columns)
    
    if st.button("多角的な分析と詳細評価を実行"):
        # クラウド用フォントパス
        FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        all_text = "\n".join(df[target_col].dropna().astype(str))
        
        # 分かち書きデータの作成
        wakati_facts = extract_words(all_text, include_feelings=False)
        wakati_feelings = extract_words(all_text, include_feelings=True)

        # 左右のワードクラウド表示
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("① 事実・対象（名詞のみ）")
            wc1 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_facts)
            st.image(wc1.to_array(), use_container_width=True)
            
            buf1 = io.BytesIO()
            wc1.to_image().save(buf1, format='PNG')
            st.download_button("①を保存", data=buf1.getvalue(), file_name="facts.png")

        with col2:
            st.subheader("② 感情・学び（動詞・形容詞入り）")
            wc2 = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600).generate(wakati_feelings)
            st.image(wc2.to_array(), use_container_width=True)
            
            buf2 = io.BytesIO()
            wc2.to_image().save(buf2, format='PNG')
            st.download_button("②を保存", data=buf2.getvalue(), file_name="feelings.png")

        # 7. 自動評価セクション
        st.divider()
        st.header("📝 達成度に対する詳細評価")

        e_col1, e_col2 = st.columns(2)
        
        with e_col1:
            st.markdown(f"**【ねらい1】**\n{goal_1}")
            st.info(generate_detailed_evaluation(goal_1, wakati_facts, wakati_feelings))

        with e_col2:
            st.markdown(f"**【ねらい2】**\n{goal_2}")
            st.info(generate_detailed_evaluation(goal_2, wakati_facts, wakati_feelings))

        st.success("分析が完了しました。画像と評価文を校内掲示や報告書にご活用ください。")
