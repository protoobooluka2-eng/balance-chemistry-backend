"""
BALANCE Chemistry — Conversation Intent Router
Classifies student messages to provide:
- Friendly, direct, instantaneous responses for greetings and mic checks
- Context-aware routing for lab state, simplifications, translations
- Selective knowledge retrieval ONLY for academic Chemistry questions
- Complete elimination of textbook hallucinations for casual conversation
"""

import re

# Intent Constants
INTENT_MIC_CHECK = "MIC_CHECK"
INTENT_GREETING = "GREETING"
INTENT_CASUAL = "CASUAL"
INTENT_SIMPLIFY = "SIMPLIFY"
INTENT_EXPAND = "EXPAND"
INTENT_TRANSLATE = "TRANSLATE"
INTENT_CURRENT_LAB = "CURRENT_LAB"
INTENT_TEXTBOOK_SPECIFIC = "TEXTBOOK_SPECIFIC"
INTENT_ACADEMIC_CHEMISTRY = "ACADEMIC_CHEMISTRY"
INTENT_GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
INTENT_UNCLEAR = "UNCLEAR"

# Fast Deterministic Voice Responses for Immediate Turnaround (<0.5s)
FAST_DETERMINISTIC_RESPONSES = {
    "can you hear me": "Yes, loud and clear!",
    "can you hear me?": "Yes, loud and clear!",
    "can you hear me miss": "Yes, loud and clear! How can I help?",
    "can you hear me miss?": "Yes, loud and clear! How can I help?",
    "hear me": "Yes, I can hear you perfectly!",
    "is my mic working": "Yes, your microphone is working great!",
    "is my microphone working": "Yes, your microphone is working great!",
    "are you there": "Yes, I'm right here! How can I help?",
    "are you there?": "Yes, I'm right here! How can I help?",
    "hello miss": "Hey there! How are you?",
    "hello miss!": "Hey there! How are you?",
    "hello": "Hello! How are you doing today?",
    "hi": "Hi there! What shall we explore today?",
    "hey": "Hey! How can I help you in the lab?",
    "are you ready": "Absolutely! I'm ready.",
    "are you ready?": "Absolutely! I'm ready.",
    "what's your name": "I'm your Chemistry teacher! You can call me Miss Balance.",
    "what is your name": "I'm your Chemistry teacher! You can call me Miss Balance.",
    "what is your name?": "I'm your Chemistry teacher! You can call me Miss Balance.",
    "who are you": "I'm Miss Balance, your Chemistry virtual teacher!",
    "who are you?": "I'm Miss Balance, your Chemistry virtual teacher!",
    "how are you": "I'm doing wonderfully, thank you! How are you?",
    "how are you?": "I'm doing wonderfully, thank you! How are you?",
    "إنتِ سمعاني؟": "أيوة، سامعاكي تمام! أقدر أساعدك بإيه؟",
    "سامعاني؟": "أيوة، سامعاكي بوضوح!",
    "سامعني؟": "أيوة، سامعك بوضوح تام!",
    "هل تسمعني؟": "نعم، أسمعك بوضوح تام!",
    "ازيك يا مس": "أهلاً بيك! أنا تمام، يا رب تكون بخير. جاهز لتجربتنا؟",
    "ازيك": "أهلاً وسهلاً! كله تمام، تحب نبدأ بإيه النهاردة؟"
}

CHEMISTRY_KEYWORDS = {
    "atom", "atoms", "ion", "ions", "molecule", "molecules", "electron", "proton", "neutron",
    "element", "compound", "reaction", "reactions", "equilibrium", "le chatelier", "haber",
    "ammonia", "cobalt", "chloride", "nitrogen", "hydrogen", "catalyst", "exothermic",
    "endothermic", "precipitate", "neutralization", "acid", "base", "alkali", "salt",
    "dissolve", "dissolving", "melting", "entropy", "lattice", "mole", "moles",
    "concentration", "temperature", "pressure", "yield", "rate", "conservation of mass",
    "formula", "reactant", "product", "decomposition", "recombination", "litmus"
}

def classify_intent(text: str, lab_id: str = "lab01", lab_state: dict = None) -> tuple:
    """
    Classifies student message into conversational intent.
    Returns: (intent, should_retrieve_knowledge, fast_response_or_none)
    """
    clean = text.strip().lower()
    clean_no_punct = re.sub(r'[?!.,;:\'"]', '', clean).strip()

    # Check immediate fast deterministic table
    for candidate in (clean, clean_no_punct):
        if candidate in FAST_DETERMINISTIC_RESPONSES:
            resp = FAST_DETERMINISTIC_RESPONSES[candidate]
            if any(w in candidate for w in ("hear", "mic", "سامع", "سمع", "تسمع")):
                return (INTENT_MIC_CHECK, False, resp)
            elif any(w in candidate for w in ("ready", "name", "who are", "how are")):
                return (INTENT_CASUAL, False, resp)
            else:
                return (INTENT_GREETING, False, resp)

    # 1. Microphone Check Intent
    if re.search(r'\b(can you hear me|hear me|hear my voice|is my mic working|can u hear me|microphone test|testing 1 2|test test|are you listening|do you hear me|am i audible|hear us|سامعاني|سامعني|سمعاني|هل تسمعني|تسمعني|الصوت واضح|سامع)\b', clean):
        is_ar = bool(re.search(r'[\u0600-\u06FF]', clean))
        reply = "أيوة، سامعاك تمام!" if is_ar else "Yes, loud and clear!"
        return (INTENT_MIC_CHECK, False, reply)

    # 2. Greeting Intent
    if re.match(r'^\s*(hello|hi|hey|good morning|good afternoon|good evening|greetings|howdy|miss|miss balance|صباح الخير|مساء الخير|مرحبا|أهلا|اهلا|ازيك|ازيك يا مس|هاي)\b', clean) and len(clean.split()) <= 4:
        is_ar = bool(re.search(r'[\u0600-\u06FF]', clean))
        reply = "أهلاً بيك! إزيك النهاردة؟" if is_ar else "Hey there! How are you?"
        return (INTENT_GREETING, False, reply)

    # 3. Casual Conversation Intent
    if re.search(r'\b(how are you|who are you|what is your name|what\'?s your name|tell me about yourself|are you ready|are you there|thanks|thank you|bye|goodbye|see you|مع السلامة|شكرا|شكرًا)\b', clean):
        if "ready" in clean:
            return (INTENT_CASUAL, False, "Absolutely! I'm ready.")
        if "name" in clean or "who are you" in clean:
            return (INTENT_CASUAL, False, "I'm your Chemistry teacher! You can call me Miss Balance.")
        if "how are you" in clean:
            return (INTENT_CASUAL, False, "I'm doing wonderfully, thank you! How are you?")
        if "thank" in clean or "شكرا" in clean:
            return (INTENT_CASUAL, False, "You're very welcome! Let me know if you need anything else.")
        return (INTENT_CASUAL, False, None)

    # 4. Translation Request
    if re.search(r'\b(explain (it|that|this)? in arabic|in arabic|in english|translate|بالعربي|باللغة العربية|بالانجليزي|ترجم|ترجميها)\b', clean):
        return (INTENT_TRANSLATE, False, None)

    # 5. Simplification Request
    if re.search(r'\b(i don\'?t understand|explain (it )?(more )?simply|make it simpler|simpler please|too hard|too complicated|in simple terms|مش فاهم|مش فاهمة|بسطها|بسطيها|مش واضحة)\b', clean):
        return (INTENT_SIMPLIFY, False, None)

    # 6. Deep Explanation / Expand Request
    if re.search(r'\b(more details|give me more details|tell me more|expand on (that|this)|elaborate|more detail|تفاصيل اكثر|اشرح بالتفصيل)\b', clean):
        return (INTENT_EXPAND, True, None)

    # 7. Current Active Laboratory Observation
    if re.search(r'\b(why did (my|the|this) (solution|tube|liquid|beaker|crystal|color|colour|temperature|temp|gas|pressure)|what happened (to|in)|what should i (do|try) next|why did that happen|why did it happen)\b', clean) or re.search(r'(لون المحلول|تغير اللون|المحلول اتغير|ليه المحلول|ليه اتغير|في التجربة|في المعمل|الأنبوبة|الكوبلت|كلوريد)', clean):
        return (INTENT_CURRENT_LAB, True, None)

    # 8. Textbook Specific Inquiries
    if re.search(r'\b(textbook|chapter 1|book page|page number|in the book|what does the book say|gary horner|oxford myp|الكتاب|الفصل الأول)\b', clean):
        return (INTENT_TEXTBOOK_SPECIFIC, True, None)

    # Check words against Chemistry Keywords
    tokens = set(re.findall(r'\b[a-z]{3,}\b', clean))
    is_chem = len(tokens.intersection(CHEMISTRY_KEYWORDS)) > 0

    if is_chem:
        return (INTENT_ACADEMIC_CHEMISTRY, True, None)

    # 9. General Knowledge (space, trivia, general world questions)
    return (INTENT_GENERAL_KNOWLEDGE, False, None)

COMMON_ARABIC_TRANSLATIONS = {
    "هو ليه لون المحلول اتغير؟": "Why did the solution change colour?",
    "هو ليه لون المحلول يتغير؟": "Why did the solution change colour?",
    "ليه لون المحلول اتغير؟": "Why did the solution change colour?",
    "ليه لون المحلول اتغير": "Why did the solution change colour?",
    "إنتِ سمعاني؟": "Can you hear me?",
    "إنت سمعاني؟": "Can you hear me?",
    "سامعاني؟": "Can you hear me?",
    "سامعني؟": "Can you hear me?",
    "هل تسمعني؟": "Can you hear me?",
    "هو ليه الاتزان اتغير؟": "Why did the equilibrium shift?",
    "ليه الاتزان انزاح لليمين؟": "Why did the equilibrium shift to the right?",
    "يعني ايه ذرة؟": "What is an atom?",
    "ما هي الذرة؟": "What is an atom?",
    "ما هو الأيون؟": "What is an ion?",
    "يعني ايه ايون؟": "What is an ion?",
    "ما هو الاتزان الكيميائي؟": "What is chemical equilibrium?",
    "ما هو مبدأ لوشاتيليه؟": "What is Le Chatelier's principle?",
    "مش فاهم": "I don't understand",
    "مش فاهمة": "I don't understand",
    "اشرحيها بالعربي": "Explain it in Arabic",
    "قوليلي معلومة عن الفضاء": "Tell me a fun fact about space",
    "ازيك يا مس": "How are you, Miss?",
    "جاهزة؟": "Are you ready?"
}

def get_translation_hint(text: str) -> str:
    """
    Returns an English translation for Arabic speech without delaying the voice pipeline.
    """
    clean = text.strip()
    if clean in COMMON_ARABIC_TRANSLATIONS:
        return COMMON_ARABIC_TRANSLATIONS[clean]
    
    clean_no_punct = re.sub(r'[؟!.,;:]', '', clean).strip()
    if clean_no_punct in COMMON_ARABIC_TRANSLATIONS:
        return COMMON_ARABIC_TRANSLATIONS[clean_no_punct]

    # Pattern based heuristics for common Arabic student speech
    if "لون المحلول" in clean and ("تغير" in clean or "اتغير" in clean):
        return "Why did the solution change colour?"
    if "سامع" in clean or "تسمع" in clean:
        return "Can you hear me?"
    if "اتزان" in clean and ("انزاح" in clean or "تغير" in clean or "يمين" in clean):
        return "Why did the equilibrium shift?"
    if "ذرة" in clean:
        return "What is an atom?"
    if "أيون" in clean or "ايون" in clean:
        return "What is an ion?"
    if "لوشاتيليه" in clean:
        return "Can you explain Le Chatelier's principle?"
    if "مش فاهم" in clean:
        return "I don't understand"

    return None

