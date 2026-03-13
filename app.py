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
st.title("📊 AIリフレクション・アナライザー")
st.write("アンケート結果を可視化し、AIがねらいに対する達成度を評価します。")

# --- 2. API設定 (Secretsから自動読み込み) ---
try:
    # Streamlit CloudのSecretsに登録したキーを呼び出します
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("APIキーが設定されていません。Streamlit CloudのSettings > Secretsを確認してください。")
    st.stop()

# --- 3. サイドバー設定 ---
st.sidebar.header("📋 行事のねらい設定")
goal_1 = st.sidebar.text_area("ねらい1", "地域（邑南町）の魅力や課題について理解を深める。")
goal_2 = st.sidebar.text_area("ねらい2", "農業や特産品（柚子胡椒等）を通じた地域活性化について考える。")

t = Tokenizer()

# --- 4. 単語抽出エンジンの定義 ---
def extract_words(text):
    words = []
    # 思考力や感情を捉えるための単語リスト
    feeling_words = ["思う", "感じる", "考える", "知る", "驚く", "わかる", "面白い", "楽しい", "凄い", "すごい", "不思議", "納得"]
    
    if not text or pd.isna(text):
        return ""

    for token in t.tokenize(str(text)):
        part = token.part_of_speech.split(",")[0]
        base = token.base_form
        # 名詞（2文字以上）または指定した感情語を抽出
        if (part == "名詞" and len(base) >= 2) or (base in feeling_words):
            # 一般的な言葉を除外
            if base not in ["こと", "もの", "よう", "そう", "これ", "それ"]:
                words.append(base)
    return " ".join(words)

# --- 5. メイン処理：ファイルアップロード ---
uploaded_file = st.file_uploader("エクセルまたはCSVファイルをアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    # データの読み込み
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    target_col = st.selectbox("分析したい感想の列を選択してください", df.columns)
    
    if st.button("AIによる分析と詳細評価を実行"):
        with st.spinner("ワードクラウドを生成し、AIが画像を分析しています..."):
            # 5-1. テキスト処理
            all_text = "\n".join(df[target_col].dropna().astype(str))
            wakati = extract_words(all_text)
            
            if not wakati.strip():
                st.warning("単語が抽出できませんでした。列の選択が正しいか確認してください。")
            else:
                # ワードクラウド作成（日本語フォントを指定）
                FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                wc = WordCloud(font_path=FONT_PATH, background_color="white", width=1200, height=600).generate(wakati)
                
                # 画像をバイトデータに変換（AI送信用）
                img_buf = io.BytesIO()
                wc.to_image().save(img_buf, format='PNG')
                img_bytes = img_buf.getvalue()
                
                # 結果の表示
                st.subheader("📊 分析結果：ワードクラウド")
                st.image(img_bytes, use_container_width=True)

                # 5-2. OpenAI (GPT-4o) による画像分析評価
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                
                prompt = f"""
あなたは中学校の理科・総合的な学習の時間の教師として，提供された「ワードクラウド画像」を分析し，以下の2つの「ねらい」に対する達成度を詳細に評価・論述してください。

【ねらい1】
{goal_1}

【ねらい2】
{goal_2}

### 出力ルール
1. 各ねらいに対して，達成度を S, A, B, C の4段階で判定する。
2. 判定の根拠を，画像内で大きく表示されている語彙（事実）や，その周囲にある語彙（感情・思考・驚き）を具体的に引用しながら説明する。
3. 今後の事後指導や，生徒へのフィードバックに活かせるアドバイスを添える。
4. 文章はすべて日本語で，教師が報告書や所見にそのまま活用できるような，専門的かつ温かみのある表現にする。
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
                    max_tokens=1500,
                )
                
                # AI評価の表示
                st.divider()
                st.header("📝 AIによる達成度評価レポート")
                st.markdown(response.choices[0].message.content)
                
                # 保存ボタン
                st.download_button("分析画像を保存", data=img_bytes, file_name="analysis_cloud.png")

        st.success("分析が完了しました。")
