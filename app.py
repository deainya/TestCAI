import streamlit as st
import requests
import json
import re
from datetime import datetime
import time
from typing import Dict, List, Optional

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
    .chat-container {
        max-width: 100%;
        margin: 0 auto;
        padding: 10px;
    }
    
    .chat-message {
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
        max-width: 80%;
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
    
    .email-input {
        max-width: 400px;
        margin: 0 auto;
    }
    
    @media (max-width: 768px) {
        .chat-container {
            padding: 5px;
        }
        
        .chat-message {
            max-width: 90%;
            font-size: 14px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Инициализация session state
if 'email' not in st.session_state:
    st.session_state.email = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'ticket_data' not in st.session_state:
    st.session_state.ticket_data = {
        'equipment_type': None,
        'device_number': None,
        'problem_description': None,
        'incident_date': None,
        'photo_url': None
    }
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict]) -> Dict:
    """Отправка сообщения в n8n webhook"""
    n8n_url = st.secrets.get("N8N_WEBHOOK_URL")
    
    if not n8n_url:
        return {"error": "N8N_WEBHOOK_URL не настроен"}
    
    try:
        payload = {
            "message": message,
            "chat_history": chat_history,
            "ticket_data": st.session_state.ticket_data,
            "user_email": st.session_state.email
        }
        
        response = requests.post(
            n8n_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Ошибка сервера: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"error": "Таймаут запроса к n8n"}
    except requests.exceptions.ConnectionError:
        return {"error": "Ошибка подключения к n8n"}
    except Exception as e:
        return {"error": f"Неожиданная ошибка: {str(e)}"}

def display_chat_message(message: str, is_user: bool):
    """Отображение сообщения в чате"""
    css_class = "user-message" if is_user else "assistant-message"
    st.markdown(f'<div class="chat-message {css_class}">{message}</div>', unsafe_allow_html=True)

def is_ticket_complete() -> bool:
    """Проверка полноты данных заявки"""
    required_fields = ['equipment_type', 'device_number', 'problem_description', 'incident_date']
    return all(st.session_state.ticket_data[field] for field in required_fields)

def display_ticket_summary():
    """Отображение сводки заявки"""
    st.markdown("### 📋 Сводка заявки на обслуживание")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Email:** {st.session_state.email}")
        st.write(f"**Тип оборудования:** {st.session_state.ticket_data['equipment_type']}")
        st.write(f"**Номер устройства:** {st.session_state.ticket_data['device_number']}")
    
    with col2:
        st.write(f"**Дата инцидента:** {st.session_state.ticket_data['incident_date']}")
        if st.session_state.ticket_data['photo_url']:
            st.write(f"**Фото:** {st.session_state.ticket_data['photo_url']}")
    
    st.write(f"**Описание проблемы:** {st.session_state.ticket_data['problem_description']}")

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Проверка email
    if not st.session_state.email:
        st.markdown('<div class="email-input">', unsafe_allow_html=True)
        st.markdown("### Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com")
        
        if st.button("Продолжить", type="primary"):
            if email and validate_email(email):
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # Отображение email и кнопка сброса
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"Вы вошли как: {st.session_state.email}")
        with col2:
            if st.button("Сменить email"):
                st.session_state.email = None
                st.session_state.chat_history = []
                st.session_state.ticket_data = {
                    'equipment_type': None,
                    'device_number': None,
                    'problem_description': None,
                    'incident_date': None,
                    'photo_url': None
                }
                st.session_state.chat_started = False
                st.rerun()
        
        # Чат интерфейс
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Отображение истории чата
        for message in st.session_state.chat_history:
            display_chat_message(message['content'], message['is_user'])
        
        # Начальное сообщение ассистента
        if not st.session_state.chat_started:
            initial_message = "Добрый день, чем могу помочь?"
            display_chat_message(initial_message, False)
            st.session_state.chat_history.append({
                'content': initial_message,
                'is_user': False,
                'timestamp': datetime.now()
            })
            st.session_state.chat_started = True
        
        # Проверка полноты данных
        if is_ticket_complete():
            st.markdown("---")
            display_ticket_summary()
            
            if st.button("📤 Отправить заявку", type="primary"):
                with st.spinner("Отправка заявки..."):
                    # Здесь можно добавить логику отправки заявки
                    st.success("✅ Заявка успешно отправлена!")
                    st.balloons()
        else:
            # Ввод сообщения
            user_input = st.text_input("Введите ваше сообщение:", key="user_input", placeholder="Опишите проблему...")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Отправить", type="primary"):
                    if user_input:
                        # Добавление сообщения пользователя в историю
                        st.session_state.chat_history.append({
                            'content': user_input,
                            'is_user': True,
                            'timestamp': datetime.now()
                        })
                        
                        # Отправка в n8n
                        with st.spinner("Обработка запроса..."):
                            response = send_to_n8n(user_input, st.session_state.chat_history)
                            
                            if "error" in response:
                                st.error(f"Ошибка: {response['error']}")
                            else:
                                # Добавление ответа ассистента
                                assistant_response = response.get('response', 'Извините, произошла ошибка обработки.')
                                st.session_state.chat_history.append({
                                    'content': assistant_response,
                                    'is_user': False,
                                    'timestamp': datetime.now()
                                })
                                
                                # Обновление данных заявки если они есть в ответе
                                if 'ticket_data' in response:
                                    st.session_state.ticket_data.update(response['ticket_data'])
                        
                        st.rerun()
            
            with col2:
                if st.button("📷 Добавить фото"):
                    photo_url = st.text_input("URL фото:", placeholder="https://example.com/photo.jpg")
                    if photo_url:
                        st.session_state.ticket_data['photo_url'] = photo_url
                        st.success("Фото добавлено!")
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
