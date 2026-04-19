from deep_translator import GoogleTranslator

def translate_payload(data, target_lang):
    """
    Translates English HUD data into the target language.
    """
    if not data or "error" in data:
        return data
    
    lang_clean = target_lang.strip().lower()
    if lang_clean == "english":
        return data

    try:
        print(f"[TRANSLATOR] Converting English -> {target_lang}...")
        # auto detection for source, target_lang for destination
        translator = GoogleTranslator(source='auto', target=lang_clean)
        
        # We translate the display names and the reasoning text
        data["local_name"] = translator.translate(data.get("eng_name", ""))
        data["contents"] = translator.translate(data.get("contents", ""))
        
        return data
    except Exception as e:
        print(f"[ERROR] Translation failed for {target_lang}: {e}")
        return data