# Hello World Streamlit App

Минимальное приложение Streamlit "Hello World" для деплоя на Streamlit Community Cloud.

## 🚀 Быстрый старт

### Локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите приложение:
```bash
streamlit run app.py
```

3. Откройте браузер по адресу: http://localhost:8501

## ☁️ Деплой на Streamlit Community Cloud

### Шаг 1: Подготовка репозитория

1. Создайте репозиторий на GitHub
2. Загрузите файлы проекта в репозиторий:
   - `app.py` - основной файл приложения
   - `requirements.txt` - зависимости
   - `README.md` - документация

### Шаг 2: Деплой на Streamlit Cloud

1. Перейдите на [share.streamlit.io](https://share.streamlit.io)
2. Войдите через GitHub
3. Нажмите "New app"
4. Выберите ваш репозиторий
5. Укажите путь к файлу: `app.py`
6. Нажмите "Deploy!"

### Шаг 3: Настройка (опционально)

Создайте файл `.streamlit/config.toml` для дополнительных настроек:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## 📁 Структура проекта

```
├── app.py              # Основной файл приложения
├── requirements.txt    # Зависимости Python
├── README.md          # Документация
└── .streamlit/        # Конфигурация Streamlit (опционально)
    └── config.toml
```

## 🛠️ Возможности приложения

- 👋 Приветственное сообщение
- 🔘 Интерактивная кнопка
- 📝 Поле ввода имени
- 📊 Метрики и статистика
- 🎨 Современный дизайн

## 📝 Требования

- Python 3.7+
- Streamlit 1.28.0+

## 🔗 Полезные ссылки

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Community Cloud](https://share.streamlit.io/)
- [Streamlit Gallery](https://streamlit.io/gallery)

