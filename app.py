import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from openai import OpenAI
from docx import Document
from docx.shared import Inches

# --- 1. ページ設定 ---
st.set_page_config(page_title="Reflection Analyzer", layout="wide")
st.title("📊 振り返り達成度分析システム")
st.write("アンケート結果を可視化し、設定したねらいに対する達成度を客観的に評価します。")

# --- 2. API設定 ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("システム設定（Secrets）を確認してください。")
    st.stop()

# --- 3. サイドバー設定：行事情報入力 ---
st.sidebar.header("📋 行事・学習の設定")
event_name = st.sidebar.text_input("行事名・授業名", "広島大学校外学習")

st.sidebar.subheader("学習のねらい")
g1 = st.sidebar.text_area("ねらい1", "地域の魅力や課題について理解を深める。")
g2 = st.sidebar.text_area("ねらい2", "将来の進路について考えるきっかけとする。")
g3 = st.sidebar.text_area("ねらい3", "")
g4 = st.sidebar.text_area("ねらい4", "")

# 有効なねらいをリスト化
goals = [g for g in [g1, g2, g3, g4] if g.strip()]

t = Tokenizer()

# --- 4. 単語抽出エンジン ---
def extract_words(text):
    words = []
    target_feelings = ["面白い", "楽しい", "凄い", "すごい", "わかる", "驚く", "難しい", "疲れる", "つまらない", "嫌だ", "迷う"]
    if not text or pd.isna(text): return ""
    tokens = list(t.tokenize(str(text)))
    i = 0
    while i < len(tokens):
        token = tokens[i]
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        surface = token.surface
        if part == "名詞" and len(base) >= 2:
            if base not in ["こと", "もの", "よう", "そう", "これ", "それ"]: words.append(base)
        elif base in target_feelings or part == "形容詞":
            word_to_add = base
            if i + 1 < len(tokens):
                next_t = tokens[i+1]
                if next_t.base_form in ["ない", "ぬ", "ん"] or "助動詞" in next_t.part_of_speech:
                    if next_t.base_form in ["ない", "ぬ", "ん"]:
                        word_to_add = base[:-1] + "くない" if part == "形容詞" else base + "ない"
                        i += 1
            if word_to_add not in ["ある", "する", "いる"]: words.append(word_to_add)
        elif surface == "行き" and i + 1 < len(tokens) and "たい" in tokens[i+1].surface:
            word_to_add = "行きたくない" if i + 2 < len(tokens) and tokens[i+2].base_form == "ない" else "行きたい"
            words.append(word_to_add)
            i += 1
        i += 1
    return " ".join(words)

# --- 5. Word作成用関数 ---
def create_word(evaluation_text, img_bytes, event, goal_list):
    doc = Document()
    doc.add_heading(f'{event} 振り返り分析レポート', 0)
    
    doc.add_heading('【設定されたねらい】', level=1)
    for i, g in enumerate(goal_list):
        doc.add_paragraph(f"ねらい{i+1}: {g}")
    
    doc.add_heading('【可視化分析：ワードクラウド】', level=1)
    img_stream = io.BytesIO(img_bytes)
    doc.add_picture(img_stream, width=Inches(6))
    
    doc.add_heading('【ねらいに対する達成度評価】', level=1)
    doc.add_paragraph(evaluation_text)
    
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# --- 6. メイン処理 ---
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    target_col = st.selectbox("分析対象の列を選択してください", df.columns)
    
    if st.button("分析と達成度評価を実行"):
        with st.spinner("データを分析中..."):
            all_text_list = df[target_col].dropna().astype(str).tolist()
            all_text_full = "\n".join(all_text_list)
            wakati = extract_words(all_text_full)
            
            if not wakati.strip():
                st.warning("有効な単語が抽出できませんでした。")
            else:
                FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                wc = WordCloud(font_path=FONT_PATH, background_color="white", width=1200, height=600).generate(wakati)
                img_buf = io.BytesIO()
                wc.to_image().save(img_buf, format='PNG')
                img_bytes = img_buf.getvalue()
                
                st.subheader("📊 分析結果：ワードクラウド")
                st.image(img_bytes)

                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                context_text = all_text_full[:2000]

                # ねらいをプロンプト用に整形
                goals_str = "\n".join([f"ねらい{i+1}: {g}" for i, g in enumerate(goals)])

                prompt = f"""
                あなたは学校教育の専門家として，提供された「ワードクラウド画像」および「生徒の記述内容」を多角的に分析し，
                以下の【行事名】における【設定されたねらい】への達成度を客観的に評価してください。

                【行事名】: {event_name}
                【設定されたねらい】:
                {goals_str}

                【原文の一部】:
                {context_text}

                ### 評価の指針
                1. 各ねらいに対して，生徒がどのような変容を遂げたか，画像内の語彙を根拠に論述してください。
                2. 単語の出現頻度だけでなく，否定語や困難さを示す表現（難しい、疲れる等）も踏まえ，実態に即した評価を行ってください。
                3. 今後の指導に直結する専門的なアドバイスを添えてください。
                4. 「AI」という言葉は使わず、一貫して教育的な分析レポートとして記述してください。
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}],
                )
                
                evaluation_text = response.choices[0].message.content
                st.divider()
                st.header("📝 ねらいに対する達成度評価")
                st.markdown(evaluation_text)
                
                # Wordファイルの生成
                word_file = create_word(evaluation_text, img_bytes, event_name, goals)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("画像を保存", data=img_bytes, file_name=f"{event_name}_分析.png")
                with col2:
                    st.download_button(
                        label="📄 評価レポート(Word)を保存",
                        data=word_file,
                        file_name=f"{event_name}_評価レポート.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

        st.success("分析レポートの作成が完了しました。")
