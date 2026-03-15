import streamlit as st
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from openai import OpenAI

# --- 1. ページ設定 ---
st.set_page_config(page_title="AI Reflection Analyzer", layout="wide")
st.title("📊 AIリフレクション・アナライザー (否定語対応版)")

# --- 2. OpenAI API設定 ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("APIキーが設定されていません。Settings > Secretsを確認してください。")
    st.stop()

# --- 3. サイドバー設定 ---
st.sidebar.header("📋 行事のねらい設定")
goal_1 = st.sidebar.text_area("ねらい1", "地域（邑南町）の魅力や課題について理解を深める。")
goal_2 = st.sidebar.text_area("ねらい2", "農業や特産品（柚子胡椒等）を通じた地域活性化について考える。")

t = Tokenizer()

# --- 4. 改良版：単語抽出エンジン (否定語・ネガティブ語対応) ---
def extract_words(text):
    words = []
    # 判定したい感情・状態ワード（基本形で指定）
    target_feelings = [
        "面白い", "楽しい", "凄い", "すごい", "わかる", "驚く", 
        "難しい", "疲れる", "つまらない", "嫌だ", "迷う"
    ]
    
    if not text or pd.isna(text):
        return ""

    tokens = list(t.tokenize(str(text)))
    i = 0
    while i < len(tokens):
        token = tokens[i]
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        surface = token.surface
        
        # 1. 名詞の抽出
        if part == "名詞" and len(base) >= 2:
            if base not in ["こと", "もの", "よう", "そう", "これ", "それ"]:
                words.append(base)
        
        # 2. 感情語（形容詞・動詞）の判定と否定の結合
        elif base in target_feelings or part == "形容詞":
            word_to_add = base
            
            # 次のトークンを確認して否定（ない、ん、ぬ）を探す
            if i + 1 < len(tokens):
                next_t = tokens[i+1]
                if next_t.base_form in ["ない", "ぬ", "ん"] or "助動詞" in next_t.part_of_speech:
                    if next_t.base_form in ["ない", "ぬ", "ん"]:
                        # 形容詞の場合は「語幹 + く」にしてから「ない」を繋ぐ
                        if part == "形容詞":
                            # 「面白い」の語幹「面白」に「くない」を付ける
                            word_to_add = base[:-1] + "くない"
                        else:
                            # 動詞などはそのまま「ない」を付ける
                            word_to_add = base + "ない"
                        i += 1 # 「ない」を消費
            
            # 除外リストになければ追加
            if word_to_add not in ["ある", "する", "いる"]:
                words.append(word_to_add)
                
        # 3. 「行きたくない」などの特殊な助動詞結合
        elif surface == "行き" and i + 1 < len(tokens) and "たい" in tokens[i+1].surface:
            word_to_add = "行きたい"
            if i + 2 < len(tokens) and tokens[i+2].base_form == "ない":
                word_to_add = "行きたくない"
                i += 1
            words.append(word_to_add)
            i += 1

        i += 1
    return " ".join(words)

# --- 5. メイン処理 ---
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    target_col = st.selectbox("分析したい感想の列を選択してください", df.columns)
    
    if st.button("AIによる分析と詳細評価を実行"):
        with st.spinner("AIが文脈を読み取っています..."):
            # テキスト統合
            all_text_list = df[target_col].dropna().astype(str).tolist()
            all_text_full = "\n".join(all_text_list)
            wakati = extract_words(all_text_full)
            
            if not wakati.strip():
                st.warning("有効な単語が抽出できませんでした。")
            else:
                # ワードクラウド作成
                FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                wc = WordCloud(font_path=FONT_PATH, background_color="white", width=1200, height=600).generate(wakati)
                
                img_buf = io.BytesIO()
                wc.to_image().save(img_buf, format='PNG')
                img_bytes = img_buf.getvalue()
                
                st.subheader("📊 分析結果：ワードクラウド")
                st.image(img_bytes, use_container_width=True)

                # OpenAI (GPT-4o) へのプロンプト設定
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                
                # 生のテキストも一部（最大2000文字）渡して、文脈の誤解を防ぐ
                context_text = all_text_full[:2000]

                prompt = f"""
あなたは中学校教師として，提供された「ワードクラウド画像」を分析し，以下の「ねらい」に対する達成度を評価してください。

【ねらい1】: {goal_1}
【ねらい2】: {goal_2}

### 重要な注意点
画像内に「面白い」等の言葉があっても、元の文脈が「面白くない」等の否定である場合があります。
以下の【原文の一部】も参考にし、生徒の真の反応（肯定的か、批判的か、困難を感じているか）を正確に判定してください。

【原文の一部】:
{context_text}

### 出力ルール
1. 達成度を S, A, B, C で判定する。
2. 画像内の語彙を引用しながら根拠を説明する。
3. 今後の指導へのアドバイスを添える。
"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ],
                        }
                    ],
                )
                
                st.divider()
                st.header("📝 AIによる達成度評価レポート")
                st.markdown(response.choices[0].message.content)
                st.download_button("画像を保存", data=img_bytes, file_name="analysis.png")

        st.success("完了しました。")
