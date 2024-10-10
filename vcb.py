from config import config

def help_format(model: str, stream: bool):
    return f"""Ваша модель: {config.models[model]}\nСтриминг ответов ИИ: {'✅' if stream else '❎'}\n\n*Команды*:\n/stream - {'Отключает режим стриминга ответов ИИ.' if stream else "Включает режим стриминга ответов ИИ."}\n/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика\n/clear - забыть историю сообщений"""