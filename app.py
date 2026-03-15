import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from openai import OpenAI
from docx import Document
from docx.shared import Inches  # ← ここを確実にインポートするように修正しました

# --- 1. ページ設定 ---
st.set_page_config(page_title="AI Reflection Analyzer", layout="wide")
st.title("📊 AIリフレクション・アナライザー (Word出力対応)")

# --- 2. API設定 ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("APIキーが設定されていません。Settings > Secretsを確認してください。")
    st.stop()

# --- 3. サイドバー設定 ---
st.sidebar.header("📋 行事のねらい設定")
goal_1 = st.sidebar.text_area("ねらい1", "地域の魅力や課題について理解を深める。")
goal_2 = st.sidebar.text_area("ねらい2", "地域活性化について考える。")

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

# --- 5. Word作成用関数 (エラー修正済み) ---
def create_word(evaluation_text, img_bytes, g1, g2):
    doc = Document()
    doc.add_heading('AIリフレクション評価レポート', 0)
    
    doc.add_heading('【設定されたねらい】', level=1)
    doc.add_paragraph(f"ねらい1: {g1}")
    doc.add_paragraph(f"ねらい2: {g2}")
    
    doc.add_heading('【分析結果：ワードクラウド】', level=1)
    img_stream = io.BytesIO(img_bytes)
    # 修正箇所: st.docx.shared ではなく Inches を直接使う
    doc.add_picture(img_stream, width=Inches(6))
    
    doc.add_heading('【AI評価詳細】', level=1)
    doc.add_paragraph(evaluation_text)
    
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# --- 6. メイン処理 ---
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    target_col = st.selectbox("分析したい感想の列を選択してください", df.columns)
    
    if st.button("AIによる分析と詳細評価を実行"):
        with st.spinner("分析中..."):
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

                prompt = f"""
                あなたは中学校教師として，提供された「ワードクラウド画像」を分析し，以下の「ねらい」に対する達成度を評価してください。
                【ねらい1】: {goal_1}
                【ねらい2】: {goal_2}
                原文の一部: {context_text}
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}],
                )
                
                evaluation_text = response.choices[0].message.content
                st.divider()
                st.header("📝 AIによる達成度評価レポート")
                st.markdown(evaluation_text)
                
                # Wordファイルの生成
                word_file = create_word(evaluation_text, img_bytes, goal_1, goal_2)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("画像を保存", data=img_bytes, file_name="analysis.png")
                with col2:
                    st.download_button(
                        label="📄 Wordレポートをダウンロード",
                        data=word_file,
                        file_name="AI評価レポート.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
