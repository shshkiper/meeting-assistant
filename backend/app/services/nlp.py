# NLP-анализ текста совещания:
# - ключевые слова через KeyBERT (если не работает — YAKE как запасной вариант)
# - извлечение контактов (имена, email, телефоны) через spaCy
# - анализ тональности для русского текста через Dostoevsky

import re
from typing import Any, Dict, List, Optional

import phonenumbers
from loguru import logger


# ── Keyword Extraction ────────────────────────────────────────────────────────

class KeywordExtractor:
    def __init__(self):
        self._kw_model = None
        self._yake_extractor = None

    def _get_keybert(self):
        if self._kw_model is None:
            try:
                from keybert import KeyBERT
                self._kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
            except Exception as e:
                logger.warning(f"KeyBERT unavailable: {e}")
        return self._kw_model

    def _get_yake(self):
        if self._yake_extractor is None:
            try:
                import yake
                self._yake_extractor = yake.KeywordExtractor(
                    lan="ru", n=2, dedupLim=0.7, top=20
                )
            except Exception as e:
                logger.warning(f"YAKE unavailable: {e}")
        return self._yake_extractor

    def extract(self, text: str, top_n: int = 15) -> List[Dict[str, Any]]:
        # Пробуем KeyBERT, если не работает — используем YAKE
        results = []

        model = self._get_keybert()
        if model:
            try:
                keywords = model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 2),
                    stop_words=None,
                    top_n=top_n,
                    use_mmr=True,
                    diversity=0.5,
                )
                results = [{"word": kw, "score": round(score, 4)} for kw, score in keywords]
                return results
            except Exception as e:
                logger.warning(f"KeyBERT не сработал: {e}")

        # Запасной вариант — YAKE
        extractor = self._get_yake()
        if extractor:
            try:
                keywords = extractor.extract_keywords(text)
                # У YAKE меньше = лучше, инвертируем для единообразия
                results = [
                    {"word": kw, "score": round(1 - min(score, 1), 4)}
                    for kw, score in keywords[:top_n]
                ]
                return results
            except Exception as e:
                logger.warning(f"YAKE не сработал: {e}")

        return results


# ── Contact Extraction ────────────────────────────────────────────────────────

class ContactExtractor:
    def __init__(self):
        self._nlp = None

    def _get_nlp(self):
        if self._nlp is None:
            try:
                import spacy
                try:
                    self._nlp = spacy.load("ru_core_news_lg")
                except OSError:
                    self._nlp = spacy.load("ru_core_news_sm")
                logger.info("spaCy Russian model loaded")
            except Exception as e:
                logger.warning(f"spaCy unavailable: {e}")
        return self._nlp

    # Email regex
    EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")

    def extract(self, text: str) -> List[Dict[str, Any]]:
        # Ищем email-адреса, телефоны и имена людей в тексте
        contacts: Dict[str, Dict] = {}

        # Email-адреса по регулярному выражению
        for email in self.EMAIL_RE.findall(text):
            contacts[email] = {"email": email, "name": None, "phone": None}

        # Номера телефонов через библиотеку phonenumbers
        for match in phonenumbers.PhoneNumberMatcher(text, "RU"):
            formatted = phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.E164
            )
            contacts[formatted] = {"phone": formatted, "name": None, "email": None}

        # Имена людей через NER от spaCy
        nlp = self._get_nlp()
        if nlp:
            try:
                doc = nlp(text[:50000])  # берём первые 50к символов для скорости
                for ent in doc.ents:
                    if ent.label_ == "PER":
                        name = ent.text.strip()
                        if name not in contacts:
                            contacts[name] = {"name": name, "email": None, "phone": None}
                        else:
                            contacts[name]["name"] = name
            except Exception as e:
                logger.warning(f"NER не сработал: {e}")

        return list(contacts.values())


# ── Sentiment Analysis ────────────────────────────────────────────────────────

class SentimentAnalyzer:
    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from dostoevsky.tokenization import RegexTokenizer
                from dostoevsky.models import FastTextSocialNetworkModel
                tokenizer = RegexTokenizer()
                self._model = FastTextSocialNetworkModel(tokenizer=tokenizer)
                logger.info("Dostoevsky sentiment model loaded")
            except Exception as e:
                logger.warning(f"Dostoevsky unavailable: {e}")
        return self._model

    def analyze(self, text: str, segments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Returns overall and per-segment sentiment.
        Sentiment classes: positive, negative, neutral, speech, skip.
        """
        model = self._get_model()
        if not model:
            return {"overall": "neutral", "score": 0.0, "segments": []}

        try:
            # Overall
            results = model.predict([text[:512]], k=5)
            overall_scores = results[0] if results else {}
            dominant = max(overall_scores, key=overall_scores.get, default="neutral")

            # Per-speaker if segments provided
            seg_sentiments = []
            if segments:
                speakers = {}
                for seg in segments:
                    spk = seg.get("speaker", "SPEAKER_00")
                    speakers.setdefault(spk, [])
                    speakers[spk].append(seg.get("text", ""))

                for speaker, texts in speakers.items():
                    combined = " ".join(texts)[:512]
                    res = model.predict([combined], k=5)
                    scores = res[0] if res else {}
                    dominant_spk = max(scores, key=scores.get, default="neutral")
                    seg_sentiments.append({
                        "speaker": speaker,
                        "sentiment": dominant_spk,
                        "scores": {k: round(v, 3) for k, v in scores.items()},
                    })

            return {
                "overall": dominant,
                "scores": {k: round(v, 3) for k, v in overall_scores.items()},
                "segments": seg_sentiments,
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {"overall": "neutral", "score": 0.0, "segments": []}


keyword_extractor = KeywordExtractor()
contact_extractor = ContactExtractor()
sentiment_analyzer = SentimentAnalyzer()
