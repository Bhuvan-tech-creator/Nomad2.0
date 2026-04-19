from deep_translator import GoogleTranslator

def translate_payload(data, target_lang):
    if not data or "error" in data:
        return data
    
    lang_clean = target_lang.strip().lower()
    if lang_clean == "english":
        data["local_name"] = data.get("eng_name")
        return data

    try:
        print(f"[TRANSLATOR] Translating English -> {target_lang}...")
        translator = GoogleTranslator(source='auto', target=lang_clean)
        data["local_name"] = translator.translate(data.get("eng_name", ""))
        data["contents"] = translator.translate(data.get("contents", ""))
        return data
    except Exception as e:
        print(f"[TRANSLATOR ERROR] Translation failed: {e}")
        data["local_name"] = data.get("eng_name")
        return data