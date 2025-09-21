import streamlit as st
import requests
import json
import os
from datetime import datetime
import time

# Настройка страницы для мобильных устройств
st.set_page_config(
    page_title="AI Assistant Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS для мобильной адаптивности
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    .stTextInput > div > div > input {
        font-size: 16px; /* Предотвращает зум на iOS */
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 85%;
        word-wrap: break-word;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .assistant-message {
        background-color: #f1f3f4;
        color: black;
        margin-right: auto;
    }
    
    .chat-container {
        height: 70vh;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .chat-message {
            max-width: 90%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

def send_to_n8n(message):
    """Отправляет сообщение в n8n webhook"""
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    if not webhook_url:
        st.error("N8N_WEBHOOK_URL не настроен. Пожалуйста, настройте переменную окружения.")
        return None
    
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "session_id": st.session_state.get("session_id", "default")
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при отправке запроса: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Превышено время ожидания ответа от сервера")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка соединения: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Неожиданная ошибка: {str(e)}")
        return None

def display_chat():
    """Отображает историю чата"""
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>Вы:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Ассистент:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)

def main():
    # Заголовок приложения
    st.title("🤖 AI Assistant Chat")
    st.markdown("---")
    
    # Отображение истории чата
    display_chat()
    
    # Индикатор загрузки
    if st.session_state.is_loading:
        with st.spinner("Ассистент печатает..."):
            time.sleep(0.5)
    
    # Форма ввода сообщения
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Введите ваше сообщение:",
            placeholder="Напишите что-нибудь...",
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("Отправить", use_container_width=True)
        with col2:
            clear_button = st.form_submit_button("Очистить чат", use_container_width=True)
    
    # Обработка отправки сообщения
    if submit_button and user_input:
        # Добавляем сообщение пользователя
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Показываем индикатор загрузки
        st.session_state.is_loading = True
        st.rerun()
    
    # Обработка очистки чата
    if clear_button:
        st.session_state.messages = []
        st.rerun()
    
    # Обработка запроса к n8n (если есть новое сообщение пользователя)
    if st.session_state.messages and st.session_state.is_loading:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            # Отправляем запрос в n8n
            response = send_to_n8n(last_message["content"])
            
            if response:
                # Извлекаем ответ ассистента из ответа n8n
                assistant_response = response.get("response", "Извините, не удалось получить ответ.")
            else:
                assistant_response = "Извините, произошла ошибка при обработке вашего запроса."
            
            # Добавляем ответ ассистента
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now()
            })
            
            # Убираем индикатор загрузки
            st.session_state.is_loading = False
            st.rerun()

    # Информация о настройке
    with st.expander("ℹ️ Информация о настройке"):
        st.markdown("""
        **Для работы приложения необходимо настроить переменную окружения:**
        - `N8N_WEBHOOK_URL` - URL webhook'а вашего n8n workflow
        
        **Формат данных, отправляемых в n8n:**
        ```json
        {
            "message": "текст сообщения пользователя",
            "timestamp": "2024-01-01T12:00:00",
            "session_id": "идентификатор сессии"
        }
        ```
        
        **Ожидаемый формат ответа от n8n:**
        ```json
        {
            "response": "ответ ассистента"
        }
        ```
        """)

if __name__ == "__main__":
    main()
