# Chat Bot с функцией времени

Простой stateless chat-graph с одним инструментом `get_current_time`.

## Установка и запуск

```bash
git clone <your_repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Установите переменную окружения:
```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Запуск

### Консольный чат (рекомендуется)
```bash
python main.py
```

### Через LangGraph Dev (веб-интерфейс)
```bash
langgraph dev
```

## Функциональность

- Бот отвечает на русском языке
- При вопросах о времени автоматически вызывает функцию `get_current_time`
- Возвращает текущее UTC время в формате ISO-8601

## Тест

Спросите: "Сколько времени?" или "Какое сейчас время?" - бот должен вызвать функцию и вернуть актуальное время. 