# AI Assistant Chat - Streamlit App

Простое приложение для чата с AI-ассистентом, интегрированное с n8n через webhook. Приложение оптимизировано для мобильных устройств и готово для деплоя на Streamlit Community Cloud.

## 🚀 Возможности

- 💬 Интерактивный чат-интерфейс
- 📱 Мобильная адаптивность
- 🔗 Интеграция с n8n через webhook
- ⚡ Быстрые ответы от AI-ассистента
- 🎨 Современный UI/UX дизайн

## 📋 Требования

- Python 3.8+
- Streamlit
- n8n workflow с webhook

## 🛠️ Установка и запуск локально

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd TestCAI
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите переменную окружения:
```bash
# Windows
set N8N_WEBHOOK_URL=your_n8n_webhook_url

# Linux/Mac
export N8N_WEBHOOK_URL=your_n8n_webhook_url
```

4. Запустите приложение:
```bash
streamlit run app.py
```

## ☁️ Деплой на Streamlit Community Cloud

### Шаг 1: Подготовка репозитория

1. Загрузите код в GitHub репозиторий
2. Убедитесь, что файлы `app.py` и `requirements.txt` находятся в корне репозитория

### Шаг 2: Настройка n8n workflow

Создайте workflow в n8n со следующими компонентами:

1. **Webhook Trigger** - для получения запросов от приложения
2. **LLM Node** - для обработки сообщений (например, OpenAI, Anthropic, или другой LLM)
3. **Response Node** - для отправки ответа обратно

**Пример структуры n8n workflow:**
```
Webhook → LLM Processing → Response
```

### Шаг 3: Деплой на Streamlit Community Cloud

1. Перейдите на [share.streamlit.io](https://share.streamlit.io)
2. Войдите в свой аккаунт GitHub
3. Нажмите "New app"
4. Выберите репозиторий и ветку
5. Укажите путь к файлу: `app.py`
6. В разделе "Advanced settings" добавьте переменную окружения:
   - **Name**: `N8N_WEBHOOK_URL`
   - **Value**: URL вашего n8n webhook (например: `https://your-n8n-instance.com/webhook/your-webhook-id`)

### Шаг 4: Настройка переменных окружения

В настройках приложения на Streamlit Community Cloud добавьте:

| Переменная | Значение | Описание |
|------------|----------|----------|
| `N8N_WEBHOOK_URL` | `https://your-n8n.com/webhook/chat` | URL webhook'а n8n |

## 📡 Формат интеграции с n8n

### Данные, отправляемые в n8n:
```json
{
    "message": "Привет, как дела?",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "session_id": "default"
}
```

### Ожидаемый ответ от n8n:
```json
{
    "response": "Привет! У меня все хорошо, спасибо! Как дела у вас?"
}
```

## 🎨 Особенности интерфейса

- **Мобильная адаптивность**: Оптимизирован для смартфонов и планшетов
- **Современный дизайн**: Чистый и интуитивный интерфейс
- **Индикаторы загрузки**: Показывает, когда ассистент "печатает"
- **История чата**: Сохраняется в рамках сессии
- **Очистка чата**: Возможность начать разговор заново

## 🔧 Настройка n8n workflow

### Пример n8n workflow:

1. **Webhook Node**:
   - Метод: POST
   - Путь: `/webhook/chat`
   - Response Mode: "On Received"

2. **LLM Node** (например, OpenAI):
   - Модель: `gpt-3.5-turbo` или `gpt-4`
   - Промпт: Используйте `{{ $json.message }}` как пользовательский ввод

3. **Response Node**:
   - Формат ответа: `{ "response": "{{ $json.choices[0].message.content }}" }`

## 🐛 Устранение неполадок

### Частые проблемы:

1. **"N8N_WEBHOOK_URL не настроен"**
   - Убедитесь, что переменная окружения установлена в Streamlit Community Cloud

2. **"Ошибка при отправке запроса"**
   - Проверьте URL webhook'а в n8n
   - Убедитесь, что n8n workflow активен

3. **"Превышено время ожидания"**
   - Увеличьте timeout в n8n workflow
   - Проверьте производительность LLM

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы, создайте issue в репозитории.
