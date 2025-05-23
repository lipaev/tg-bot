def voice_name(func):
    def decorator(tts_name: str):
        def wrapper(message, text):
            return func(message=message, text=text, voice_name=tts_name)
        return wrapper
    return decorator