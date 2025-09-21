# Запрос на обслуживание

Приложение для создания запросов на обслуживание с чат-интерфейсом и интеграцией с n8n.

## Функциональность

- ✅ Валидация email пользователя
- ✅ Мобильный чат-интерфейс
- ✅ Интеграция с n8n через webhook
- ✅ Сбор данных о проблеме через диалог
- ✅ Итоговая форма с подтверждением
- ✅ Обработка ошибок

## Деплой на Streamlit Community Cloud

1. Загрузите файлы `app.py` и `requirements.txt` в репозиторий GitHub
2. Перейдите на [share.streamlit.io](https://share.streamlit.io)
3. Подключите ваш GitHub репозиторий
4. Установите переменную окружения `N8N_WEBHOOK_URL` в настройках приложения
5. Запустите приложение

## Настройка n8n

Приложение отправляет POST запросы с JSON payload:

```json
{
  "message": "Сообщение пользователя",
  "chat_history": [
    {
      "content": "Текст сообщения",
      "is_user": true/false
    }
  ],
  "problem_data": {
    "equipment_type": "Тип оборудования",
    "device_number": "Номер устройства", 
    "description": "Описание проблемы",
    "incident_date": "Дата инцидента",
    "photo_url": "URL фото"
  }
}
```

n8n должен возвращать JSON ответ:

```json
{
  "response": "Ответ ассистента пользователю",
  "problem_data": {
    "equipment_type": "Обновленные данные",
    "device_number": "Обновленные данные",
    "description": "Обновленные данные", 
    "incident_date": "Обновленные данные",
    "photo_url": "Обновленные данные"
  }
}
```

## Локальный запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```
