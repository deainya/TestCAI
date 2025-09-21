import streamlit as st
import requests
import json
import re
from datetime import datetime
import os
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
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
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
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .email-input {
        margin-bottom: 2rem;
    }
    
    .problem-summary {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }
        
        .chat-message {
            max-width: 90%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Инициализация session state
if 'email' not in st.session_state:
    st.session_state.email = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'problem_data' not in st.session_state:
    st.session_state.problem_data = {
        'equipment_type': '',
        'device_number': '',
        'description': '',
        'incident_date': '',
        'photo_url': ''
    }
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Dict:
    """Отправка запроса в n8n"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        return {
            'success': False,
            'error': 'N8N_WEBHOOK_URL не настроен'
        }
    
    payload = {
        'message': message,
        'chat_history': chat_history,
        'problem_data': problem_data
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'error': f'Ошибка сервера: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Таймаут запроса'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Ошибка подключения'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Неожиданная ошибка: {str(e)}'
        }

def display_chat_message(content: str, is_user: bool):
    """Отображение сообщения в чате"""
    message_class = "user-message" if is_user else "assistant-message"
    st.markdown(f'<div class="chat-message {message_class}">{content}</div>', unsafe_allow_html=True)

def display_problem_summary():
    """Отображение сводки по проблеме"""
    data = st.session_state.problem_data
    
    st.markdown("### 📋 Сводка по проблеме")
    st.markdown('<div class="problem-summary">', unsafe_allow_html=True)
    
    if data['equipment_type']:
        st.write(f"**Тип оборудования:** {data['equipment_type']}")
    if data['device_number']:
        st.write(f"**Номер устройства:** {data['device_number']}")
    if data['description']:
        st.write(f"**Описание проблемы:** {data['description']}")
    if data['incident_date']:
        st.write(f"**Дата инцидента:** {data['incident_date']}")
    if data['photo_url']:
        st.write(f"**Фото:** {data['photo_url']}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Ввод email
    st.markdown('<div class="email-input">', unsafe_allow_html=True)
    email = st.text_input(
        "Введите ваш email:",
        value=st.session_state.email or "",
        placeholder="example@company.com",
        help="Введите корректный email для продолжения"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Валидация email
    if email:
        if validate_email(email):
            st.session_state.email = email
            st.session_state.show_chat = True
            st.success("✅ Email корректный")
        else:
            st.error("❌ Неверный формат email")
            st.session_state.show_chat = False
    
    # Показ чата только после валидации email
    if st.session_state.show_chat and st.session_state.email:
        
        # Отображение сводки по проблеме
        display_problem_summary()
        
        # Чат интерфейс
        st.markdown("### 💬 Чат с ассистентом")
        
        # Контейнер для чата
        chat_container = st.container()
        
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            # Отображение истории чата
            for message in st.session_state.chat_history:
                display_chat_message(message['content'], message['is_user'])
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Ввод сообщения
        user_input = st.text_input(
            "Введите ваше сообщение:",
            placeholder="Опишите проблему...",
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            send_button = st.button("Отправить", type="primary")
        
        with col2:
            if st.button("Очистить чат"):
                st.session_state.chat_history = []
                st.session_state.problem_data = {
                    'equipment_type': '',
                    'device_number': '',
                    'description': '',
                    'incident_date': '',
                    'photo_url': ''
                }
                st.rerun()
        
        # Обработка отправки сообщения
        if send_button and user_input.strip():
            # Добавляем сообщение пользователя в историю
            st.session_state.chat_history.append({
                'content': user_input,
                'is_user': True
            })
            
            # Отправляем запрос в n8n
            with st.spinner("Обработка запроса..."):
                result = send_to_n8n(
                    user_input,
                    st.session_state.chat_history[:-1],  # История без текущего сообщения
                    st.session_state.problem_data
                )
            
            if result['success']:
                # Получаем ответ от ассистента
                response_data = result['data']
                assistant_response = response_data.get('response', 'Извините, произошла ошибка обработки.')
                
                # Обновляем данные о проблеме
                if 'problem_data' in response_data:
                    st.session_state.problem_data.update(response_data['problem_data'])
                
                # Добавляем ответ ассистента в историю
                st.session_state.chat_history.append({
                    'content': assistant_response,
                    'is_user': False
                })
                
                st.success("✅ Сообщение отправлено")
                st.rerun()
            else:
                st.error(f"❌ Ошибка: {result['error']}")
        
        # Проверка готовности запроса на обслуживание
        data = st.session_state.problem_data
        required_fields = ['equipment_type', 'device_number', 'description', 'incident_date']
        all_required_filled = all(data[field] for field in required_fields)
        
        if all_required_filled:
            st.markdown("---")
            st.markdown("### 📝 Итоговый запрос на обслуживание")
            
            # Отображение итогового запроса
            st.markdown("**Данные для запроса на обслуживание:**")
            st.write(f"**Email:** {st.session_state.email}")
            st.write(f"**Тип оборудования:** {data['equipment_type']}")
            st.write(f"**Номер устройства:** {data['device_number']}")
            st.write(f"**Описание проблемы:** {data['description']}")
            st.write(f"**Дата инцидента:** {data['incident_date']}")
            if data['photo_url']:
                st.write(f"**Фото:** {data['photo_url']}")
            
            # Кнопка подтверждения
            if st.button("✅ Отправить запрос на обслуживание", type="primary"):
                st.success("🎉 Запрос на обслуживание успешно отправлен!")
                st.balloons()
                
                # Очистка данных после отправки
                st.session_state.chat_history = []
                st.session_state.problem_data = {
                    'equipment_type': '',
                    'device_number': '',
                    'description': '',
                    'incident_date': '',
                    'photo_url': ''
                }
                st.rerun()
        else:
            missing_fields = [field for field in required_fields if not data[field]]
            st.info(f"ℹ️ Для завершения запроса необходимо заполнить: {', '.join(missing_fields)}")

if __name__ == "__main__":
    main()
