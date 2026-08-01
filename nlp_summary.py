# -*- coding: utf-8 -*-
"""伯乐职南 · 本地智能总结引擎（纯 Python，无需外部 API）
实现：TextRank 摘要、TF-IDF 关键词、智能分类、趋势提取
"""
import re
import math
from collections import Counter, defaultdict

# ─── 工具函数 ───

def split_sentences(text):
    """将文本切分为句子"""
    text = re.sub(r'\s+', '', text)
    parts = re.split(r'[。！？!?.…\n]+', text)
    result = []
    for p in parts:
        p = p.strip()
        if len(p) >= 6:
            if p.endswith('，') or p.endswith(','):
                result.append(p)
            else:
                result.append(p)
    return result

def char_ngrams(text, n=2):
    """提取字符 n-gram 特征"""
    return [text[i:i+n] for i in range(len(text)-n+1)]

def jaccard_sim(a, b):
    """Jaccard 字符级相似度"""
    if not a or not b:
        return 0
    set_a, set_b = set(a), set(b)
    inter = set_a & set_b
    union = set_a | set_b
    return len(inter) / len(union) if union else 0


# ─── TF-IDF 关键词提取 ───

def compute_tfidf(documents, top_k=10):
    """简单 TF-IDF 提取关键词"""
    if not documents:
        return []
    N = len(documents)
    word_docs = defaultdict(int)
    doc_words = []
    for doc in documents:
        words = re.findall(r'[一-鿿]{2,4}', doc)
        doc_words.append(words)
        for w in set(words):
            word_docs[w] += 1
    tfidf_scores = defaultdict(float)
    for words in doc_words:
        tf = Counter(words)
        max_tf = max(tf.values()) if tf else 1
        for w, cnt in tf.items():
            idf = math.log((N + 1) / (word_docs[w] + 1)) + 1
            tfidf_scores[w] += (cnt / max_tf) * idf
    keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, score in keywords[:top_k]]


# ─── TextRank 摘录 ───

def textrank_summarize(sentences, top_k=3, damping=0.85, max_iter=100):
    """TextRank 算法提取关键句"""
    if len(sentences) <= top_k:
        return sentences
    n = len(sentences)
    graph = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                sim = jaccard_sim(sentences[i], sentences[j])
                graph[i][j] = sim
    scores = [1.0] * n
    for _ in range(max_iter):
        prev = scores[:]
        for i in range(n):
            total = sum(graph[i][j] for j in range(n) if j != i)
            if total == 0:
                continue
            score = (1 - damping)
            for j in range(n):
                if j != i and sum(graph[j][k] for k in range(n) if k != j) > 0:
                    score += damping * graph[i][j] * prev[j] / max(sum(graph[j][k] for k in range(n) if k != j), 1e-8)
            scores[i] = score
        diff = sum(abs(scores[i] - prev[i]) for i in range(n))
        if diff < 1e-6:
            break
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    indices = sorted([i for i, _ in ranked[:top_k]])
    return [sentences[i] for i in indices]


# ─── 情感分类 ───

def classify_feedback(text):
    """根据关键词判断反馈类别：positive / negative / suggestion"""
    if not text:
        return 'other'
    pos_words = ['好', '棒', '赞', '喜欢', '优秀', '专业', '收获', '干货', '实用',
                 '精彩', '不错', '满意', '推荐', '值得', '有趣', '生动', '热情', '周到']
    neg_words = ['差', '烂', '无聊', '失望', '不好', '浪费时间', '太贵', '混乱',
                 '不满', '尴尬', '冷场', '听不懂', '太快', '太慢', '一般般']
    suggest_words = ['建议', '希望', '可以', '如果', '改进', '下次', '期待',
                     '优化', '增加', '减少']
    text_lower = text.lower()
    pos_count = sum(1 for w in pos_words if w in text)
    neg_count = sum(1 for w in neg_words if w in text)
    sug_count = sum(1 for w in suggest_words if w in text or w in text_lower)
    if max(pos_count, neg_count, sug_count) == 0:
        return 'neutral'
    if sug_count >= max(pos_count, neg_count):
        return 'suggestion'
    return 'positive' if pos_count >= neg_count else 'negative'


# ─── 趋势提取 ───

def extract_trends(all_feedback_texts):
    """从多期反馈中提取趋势变化"""
    if len(all_feedback_texts) < 2:
        return []
    trends = []
    for i in range(1, len(all_feedback_texts)):
        prev_words = set(re.findall(r'[一-鿿]{2,4}', all_feedback_texts[i-1]))
        curr_words = set(re.findall(r'[一-鿿]{2,4}', all_feedback_texts[i]))
        new_topics = curr_words - prev_words
        if new_topics:
            trends.append(f'第{i+1}期新增关注：{"、".join(list(new_topics)[:3])}')
    return trends[:5]


# ─── 主汇总函数 ───

def generate_summary(feedback_list):
    """对反馈列表做综合 NLP 分析，返回结构化结果"""
    if not feedback_list:
        return {
            'pros': [], 'cons': [], 'wants': [],
            'pros_text': '', 'cons_text': '', 'wants_text': '',
            'pros_summary': '', 'cons_summary': '', 'wants_summary': '',
            'ai_summary': '', 'keywords': [], 'trends': []
        }

    # 分类
    pros, cons, suggestions = [], [], []
    for fb in feedback_list:
        text = fb if isinstance(fb, str) else fb.get('raw_text', '')
        if not text:
            continue
        cat = classify_feedback(text)
        if cat == 'positive':
            pros.append(text)
        elif cat == 'negative':
            cons.append(text)
        elif cat == 'suggestion':
            suggestions.append(text)

    # TextRank 摘要
    pro_sents = [s for t in pros for s in split_sentences(t)]
    con_sents = [s for t in cons for s in split_sentences(t)]
    sug_sents = [s for t in suggestions for s in split_sentences(t)]

    pros_summary = '；'.join(textrank_summarize(pro_sents, top_k=2)) if pro_sents else ''
    cons_summary = '；'.join(textrank_summarize(con_sents, top_k=2)) if con_sents else ''
    wants_summary = '；'.join(textrank_summarize(sug_sents, top_k=2)) if sug_sents else ''

    # 关键词
    all_texts = [t if isinstance(t, str) else t.get('raw_text', '') for t in feedback_list]
    all_texts = [t for t in all_texts if t]
    keywords = compute_tfidf(all_texts, top_k=10)

    # 综合摘要
    parts = []
    if pros_summary:
        parts.append(f"亮点：{pros_summary}")
    if cons_summary:
        parts.append(f"待改进：{cons_summary}")
    if wants_summary:
        parts.append(f"期待：{wants_summary}")
    ai_summary = '。'.join(parts) if parts else '暂无数据'

    # 趋势
    trends = extract_trends(all_texts)

    return {
        'pros': pros[-5:] if pros else [],
        'cons': cons[-5:] if cons else [],
        'wants': suggestions[-5:] if suggestions else [],
        'pros_text': '\n'.join(pros),
        'cons_text': '\n'.join(cons),
        'wants_text': '\n'.join(suggestions),
        'pros_summary': pros_summary,
        'cons_summary': cons_summary,
        'wants_summary': wants_summary,
        'ai_summary': ai_summary,
        'keywords': keywords,
        'trends': trends,
    }
