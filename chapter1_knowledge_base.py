"""
BALANCE Chemistry — Oxford MYP Chemistry Years 4 & 5
Chapter 1: Balance (Gary Horner) — Clean Academic Knowledge Base & High-Speed Retriever
Strict Zero-Paid-Services Policy Enforced
"""

import os
import re
import math
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_TXT_PATH = os.path.join(BASE_DIR, 'knowledge', 'BALANCE_Chapter1_Knowledge_CLEAN.txt')

class Chapter1KnowledgeBase:
    def __init__(self, txt_path=CLEAN_TXT_PATH):
        self.txt_path = txt_path
        self.pages = []
        self.doc_freqs = Counter()
        self.total_docs = 0
        self.avg_doc_len = 0.0
        self.load_and_index()

    def tokenize(self, text):
        return re.findall(r'\b[a-zA-Z0-9_\-\+]+|\b[A-Z][a-z]?\b', text.lower())

    def load_and_index(self):
        if not os.path.exists(self.txt_path):
            print(f"[KNOWLEDGE BASE ERROR] File not found: {self.txt_path}")
            return

        with open(self.txt_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        split_tokens = re.split(r'={5,}\s*BOOK PAGE (\d+)\s*—\s*PDF PAGE (\d+)\s*={5,}', raw_text)
        
        self.pages = []
        total_tokens = 0

        for i in range(1, len(split_tokens), 3):
            book_page = int(split_tokens[i])
            pdf_page = int(split_tokens[i+1])
            content = split_tokens[i+2].strip()

            # Identify major topic/headings
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            heading = lines[0] if lines else f"Page {book_page}"
            if heading.isdigit() or len(heading) < 3:
                heading = lines[1] if len(lines) > 1 else f"Page {book_page}"

            tokens = self.tokenize(content)
            word_counts = Counter(tokens)
            total_tokens += len(tokens)

            for w in set(tokens):
                self.doc_freqs[w] += 1

            self.pages.append({
                "book_page": book_page,
                "pdf_page": pdf_page,
                "heading": heading,
                "content": content,
                "tokens": tokens,
                "word_counts": word_counts,
                "length": len(tokens)
            })

        self.total_docs = len(self.pages)
        self.avg_doc_len = total_tokens / max(1, self.total_docs)
        print(f"[KNOWLEDGE BASE] Successfully indexed {self.total_docs} pages of Oxford MYP Chemistry Chapter 1 (Book Pages 2–25).")

    def search(self, query: str, top_k=2) -> list:
        """
        Fast in-memory BM25 retrieval across Chapter 1 textbook pages (<0.5ms).
        """
        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        k1 = 1.5
        b = 0.75
        scores = []

        for page in self.pages:
            score = 0.0
            doc_len = page["length"]
            word_counts = page["word_counts"]

            for q in q_tokens:
                if q in word_counts:
                    df = self.doc_freqs.get(q, 0)
                    idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                    tf = word_counts[q]
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)

            # Boost exact key chemistry phrase matches
            content_lower = page["content"].lower()
            if "le chatelier" in query.lower() and "le chatelier" in content_lower:
                score += 8.0
            if "haber" in query.lower() and "haber" in content_lower:
                score += 8.0
            if "cobalt" in query.lower() and "cobalt" in content_lower:
                score += 8.0
            if "entropy" in query.lower() and "entropy" in content_lower:
                score += 8.0
            if "ammonium chloride" in query.lower() and "ammonium chloride" in content_lower:
                score += 8.0
            if "sodium chloride" in query.lower() and "sodium chloride" in content_lower:
                score += 8.0

            scores.append((score, page))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, p in scores[:top_k]:
            is_covered = (s > 2.5)
            content = p["content"]
            
            # Paragraph-level relevance extraction for pinpoint accuracy
            paragraphs = [p_text.strip() for p_text in re.split(r'\n\s*\n', content) if len(p_text.strip()) > 20]
            best_para = content[:500]
            best_p_score = -1
            
            for para in paragraphs:
                p_tokens = set(self.tokenize(para))
                match_count = len(p_tokens.intersection(set(q_tokens)))
                p_lower = para.lower()
                for q in q_tokens:
                    if len(q) > 3 and q in p_lower:
                        match_count += 2
                
                # Weight by substantive paragraph length to prefer full definitions over short subheaders
                para_len = len(para)
                if para_len < 40:
                    weight = 0.3
                elif para_len > 100:
                    weight = 1.0 + min(1.0, para_len / 400.0)
                else:
                    weight = 1.0

                p_score = match_count * weight
                if p_score > best_p_score:
                    best_p_score = p_score
                    best_para = para

            # Limit excerpt length cleanly around the best paragraph
            excerpt = best_para
            if len(excerpt) > 650:
                excerpt = excerpt[:650] + "..."

            results.append({
                "book_page": p["book_page"],
                "pdf_page": p["pdf_page"],
                "heading": p["heading"],
                "score": round(s, 2),
                "is_covered": is_covered,
                "excerpt": excerpt,
                "full_page": content
            })
        return results

    def format_context_prompt(self, query: str) -> str:
        """
        Formats academic textbook context for injection into Gemini Live & Flash prompts.
        """
        matches = self.search(query, top_k=2)
        if not matches or not matches[0]["is_covered"]:
            return """[ACADEMIC KNOWLEDGE BASE: Oxford MYP Chemistry Chapter 1 - Balance]
- Status: Query topic is NOT explicitly covered in Chapter 1: Balance (Pages 2–25).
- Instruction: Clearly state that this topic is not covered in Chapter 1: Balance. If general chemistry knowledge permits answering, distinguish it as general knowledge rather than attributing it to the textbook."""

        best = matches[0]
        context_parts = [
            f"[OXFORD MYP CHEMISTRY YEARS 4 & 5 — CHAPTER 1: BALANCE]",
            f"Author: Gary Horner | Publisher: Oxford University Press",
            f"Primary Reference: Chapter 1, Book Page {best['book_page']} (PDF Page {best['pdf_page']})",
            f"Topic/Heading: {best['heading']}",
            f"Verified Textbook Excerpt:\n\"\"\"{best['excerpt']}\"\"\"",
            f"Guidelines for AI Teacher:",
            f"1. Ground your explanation primarily in this textbook reference.",
            f"2. Cite the exact textbook page naturally in your speech: (e.g., 'In Oxford MYP Chemistry Chapter 1, page {best['book_page']}...').",
            f"3. For sodium chloride dissolving, distinguish dissolving from melting, and express dissociation as NaCl(s) -> Na+(aq) + Cl-(aq).",
            f"4. Never include spurious notes or annotations (e.g. do not say 'Therefore, I have High entropy').",
            f"5. Maintain scientific accuracy and keep explanations friendly, direct, and concise (2-3 sentences)."
        ]
        
        if len(matches) > 1 and matches[1]["is_covered"] and matches[1]["book_page"] != best["book_page"]:
            second = matches[1]
            context_parts.append(f"Secondary Reference: Chapter 1, Book Page {second['book_page']}: \"{second['excerpt'][:250]}...\"")

        return "\n".join(context_parts)

# Singleton Instance
KB_INSTANCE = Chapter1KnowledgeBase()

def get_chapter1_context(query: str) -> str:
    return KB_INSTANCE.format_context_prompt(query)

def search_chapter1(query: str, top_k=2) -> list:
    return KB_INSTANCE.search(query, top_k=top_k)
