from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import requests
from app.core.config import NEWS_API_KEY
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device detected: {device}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Use pipeline which handles loading safely
print("Loading FinBERT model...")
finbert_pipeline = pipeline(
    "text-classification",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert",
    device=0 if torch.cuda.is_available() else -1,
    top_k=None
)
print(f"FinBERT loaded on {device} ✅")

def analyze_headline(headline: str):
    results = finbert_pipeline(
        headline[:512],
        truncation=True,
    )[0]
    
    scores = {r['label']: r['score'] for r in results}
    ppos = scores.get('positive', 0)
    pneg = scores.get('negative', 0)
    pneu = scores.get('neutral', 0)
    score = ppos - pneg
    
    return {
        "headline": headline,
        "positive": round(ppos, 4),
        "negative": round(pneg, 4),
        "neutral": round(pneu, 4),
        "score": round(score, 4)
    }

def fetch_headlines(query: str, max_headlines: int = 10):
    if not NEWS_API_KEY:
        # Fallback dummy headlines if no API key
        return [
            f"{query} shows strong market momentum",
            f"Investors cautious about {query} outlook",
            f"{query} trading volume increases significantly"
        ]
    try:
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={query}&language=en&sortBy=publishedAt"
            f"&pageSize={max_headlines}&apiKey={NEWS_API_KEY}"
        )
        r = requests.get(url, timeout=5)
        articles = r.json().get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except Exception as e:
        print(f"News fetch error: {e}")
        return [f"{query} market update today"]

def get_market_sentiment(symbol: str):
    headlines = fetch_headlines(symbol)
    if not headlines:
        return {
            "symbol": symbol,
            "msi": 0.0,
            "signal": "HOLD",
            "headlines": []
        }
    
    results = []
    for h in headlines:
        try:
            result = analyze_headline(h)
            results.append(result)
        except Exception as e:
            print(f"FinBERT error: {e}")
    
    if not results:
        msi = 0.0
    else:
        # Equal weights for now
        msi = round(sum(r["score"] for r in results) / len(results), 4)
    
    # Signal gate — tau = 0.1
    tau = 0.1
    if msi >= tau:
        sentiment_signal = "POSITIVE"
    elif msi < -tau:
        sentiment_signal = "NEGATIVE"
    else:
        sentiment_signal = "NEUTRAL"
    
    return {
        "symbol": symbol,
        "msi": msi,
        "signal": sentiment_signal,
        "headlines": [
            {
                "title": r["headline"],
                "source": "NewsAPI",
                "score": round(r["score"] * 100, 1)
            }
            for r in results
        ]
    } 
