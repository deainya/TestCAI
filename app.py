import streamlit as st
import requests
import json
import re
import os
from datetime import datetime
import time

# Настройка страницы
st.set_page_config(
    page_title="Запрос на обслуживание",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS для мобильной версии
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        max-width: 80%;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-message {
        background-color: #f8f9fa;
        color: #333;
        margin-right: auto;
    }
    
    .email-input {
        margin-bottom: 2rem;
    }
    
    .success-notification {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin-bottom: 1rem;
    }
    
    .error-notification {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message_data):
    """Отправка данных в N8N webhook"""
    try:
        webhook_url = os.getenv('N8N_WEBHOOK_URL')
        if not webhook_url:
            return False, "N8N_WEBHOOK_URL не настроен"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Отправка POST запроса с таймаутом
        response = requests.post(
            webhook_url, 
            json=message_data, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            return True, "Данные успешно отправлены в N8N"
        else:
            return False, f"Ошибка сервера: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Таймаут при отправке запроса"
    except requests.exceptions.ConnectionError:
        return False, "Ошибка подключения к серверу"
    except Exception as e:
        return False, f"Неожиданная ошибка: {str(e)}"

def display_chat_message(message, is_user=True):
    """Отображение сообщения в чате"""
    if is_user:
        st.markdown(f'<div class="chat-message user-message">{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message bot-message">{message}</div>', unsafe_allow_html=True)

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Инициализация session state
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'service_request' not in st.session_state:
        st.session_state.service_request = None
    
    # Проверка email
    if st.session_state.user_email is None:
        st.markdown("### Введите ваш email для продолжения")
        
        email = st.text_input(
            "Email:",
            placeholder="example@company.com",
            key="email_input"
        )
        
        if st.button("Продолжить", type="primary"):
            if email and validate_email(email):
                st.session_state.user_email = email
                st.session_state.chat_messages = []
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
    
    else:
        # Отображение email пользователя
        st.markdown(f"**Пользователь:** {st.session_state.user_email}")
        
        # Кнопка смены email
        if st.button("Изменить email"):
            st.session_state.user_email = None
            st.session_state.chat_messages = []
            st.session_state.service_request = None
            st.rerun()
        
        st.markdown("---")
        
        # Чат интерфейс
        st.markdown("### 💬 Опишите вашу проблему")
        
        # Отображение истории чата
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                display_chat_message(message['content'], message['is_user'])
        
        # Ввод нового сообщения
        user_input = st.text_area(
            "Ваше сообщение:",
            placeholder="Опишите проблему подробно...",
            height=100,
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("Отправить", type="primary"):
                if user_input.strip():
                    # Добавляем сообщение пользователя
                    st.session_state.chat_messages.append({
                        'content': user_input,
                        'is_user': True,
                        'timestamp': datetime.now()
                    })
                    
                    # Формируем запрос на обслуживание
                    chat_history = "\n".join([msg['content'] for msg in st.session_state.chat_messages])
                    service_request = f"""
ЗАПРОС НА ОБСЛУЖИВАНИЕ
====================
Пользователь: {st.session_state.user_email}
Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Описание проблемы:
{chat_history}

====================
"""
                    
                    st.session_state.service_request = service_request
                    st.rerun()
        
        with col2:
            if st.button("Очистить чат"):
                st.session_state.chat_messages = []
                st.session_state.service_request = None
                st.rerun()
        
        # Отображение сформированного запроса
        if st.session_state.service_request:
            st.markdown("---")
            st.markdown("### 📋 Сформированный запрос на обслуживание")
            
            st.text_area(
                "Запрос:",
                value=st.session_state.service_request,
                height=200,
                disabled=True
            )
            
            # Кнопки для отправки запроса
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Отправить запрос", type="primary"):
                    # Подготавливаем данные для отправки
                    message_data = {
                        'user_email': st.session_state.user_email,
                        'service_request': st.session_state.service_request,
                        'chat_history': st.session_state.chat_messages,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Отправляем в N8N
                    with st.spinner("Отправка запроса..."):
                        success, message = send_to_n8n(message_data)
                    
                    if success:
                        st.success("✅ " + message)
                        # Очищаем чат после успешной отправки
                        st.session_state.chat_messages = []
                        st.session_state.service_request = None
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ " + message)
            
            with col2:
                if st.button("❌ Отменить"):
                    st.session_state.service_request = None
                    st.rerun()

if __name__ == "__main__":
    main()
