import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

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
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 10px 10px 0 10px;
        margin: 5px 0;
        text-align: right;
        margin-left: 20%;
    }
    
    .assistant-message {
        background-color: #f1f3f4;
        color: black;
        padding: 10px;
        border-radius: 10px 10px 10px 0;
        margin: 5px 0;
        text-align: left;
        margin-right: 20%;
    }
    
    .email-input {
        max-width: 400px;
        margin: 0 auto;
    }
    
    .problem-summary {
        background-color: #e8f4fd;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    
    @media (max-width: 768px) {
        .chat-container {
            padding: 5px;
        }
        
        .user-message, .assistant-message {
            margin-left: 5%;
            margin-right: 5%;
        }
    }
</style>
""", unsafe_allow_html=True)

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Optional[Dict]:
    """Отправка запроса в n8n"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        st.error("N8N_WEBHOOK_URL не настроен")
        return None
    
    payload = {
        "message": message,
        "chat_history": chat_history,
        "problem_data": problem_data
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка n8n: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Таймаут при обращении к n8n")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Ошибка подключения к n8n")
        return None
    except Exception as e:
        st.error(f"Неожиданная ошибка: {str(e)}")
        return None

def display_chat_message(content: str, is_user: bool):
    """Отображение сообщения в чате"""
    if is_user:
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

def display_problem_summary(problem_data: Dict):
    """Отображение сводки по проблеме"""
    st.markdown("### 📋 Сводка по проблеме")
    
    summary_html = '<div class="problem-summary">'
    summary_html += '<h4>Собранная информация:</h4>'
    summary_html += '<ul>'
    
    if problem_data.get('equipment_type'):
        summary_html += f'<li><strong>Тип оборудования:</strong> {problem_data["equipment_type"]}</li>'
    if problem_data.get('device_number'):
        summary_html += f'<li><strong>Номер устройства:</strong> {problem_data["device_number"]}</li>'
    if problem_data.get('description'):
        summary_html += f'<li><strong>Описание проблемы:</strong> {problem_data["description"]}</li>'
    if problem_data.get('incident_date'):
        summary_html += f'<li><strong>Дата инцидента:</strong> {problem_data["incident_date"]}</li>'
    if problem_data.get('photo_url'):
        summary_html += f'<li><strong>Фото:</strong> <a href="{problem_data["photo_url"]}" target="_blank">Просмотр</a></li>'
    
    summary_html += '</ul></div>'
    st.markdown(summary_html, unsafe_allow_html=True)

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Инициализация session state
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
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
    if 'show_summary' not in st.session_state:
        st.session_state.show_summary = False
    
    # Проверка email
    if not st.session_state.user_email:
        st.markdown('<div class="email-input">', unsafe_allow_html=True)
        st.subheader("Введите ваш email для продолжения")
        
        email = st.text_input("Email:", placeholder="example@company.com")
        
        if st.button("Продолжить", type="primary"):
            if validate_email(email):
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Отображение email пользователя
    st.success(f"Вы вошли как: {st.session_state.user_email}")
    
    # Чат интерфейс
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Отображение истории чата
    for message in st.session_state.chat_history:
        display_chat_message(message['content'], message['is_user'])
    
    # Если это первый запуск, показать приветствие
    if not st.session_state.chat_history:
        welcome_message = "Добрый день, чем могу помочь?"
        st.session_state.chat_history.append({
            'content': welcome_message,
            'is_user': False
        })
        display_chat_message(welcome_message, False)
    
    # Ввод сообщения пользователя
    user_input = st.text_input("Введите ваше сообщение:", key="user_input", placeholder="Опишите проблему...")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("Отправить", type="primary")
    
    with col2:
        if st.button("Сбросить чат"):
            st.session_state.chat_history = []
            st.session_state.problem_data = {
                'equipment_type': '',
                'device_number': '',
                'description': '',
                'incident_date': '',
                'photo_url': ''
            }
            st.session_state.show_summary = False
            st.rerun()
    
    # Обработка отправки сообщения
    if send_button and user_input:
        # Добавляем сообщение пользователя в историю
        st.session_state.chat_history.append({
            'content': user_input,
            'is_user': True
        })
        
        # Отправляем запрос в n8n
        with st.spinner("Обрабатываю ваш запрос..."):
            n8n_response = send_to_n8n(
                user_input,
                st.session_state.chat_history,
                st.session_state.problem_data
            )
        
        if n8n_response:
            # Обновляем данные о проблеме
            if 'problem_data' in n8n_response:
                st.session_state.problem_data.update(n8n_response['problem_data'])
            
            # Добавляем ответ ассистента в историю
            assistant_response = n8n_response.get('text', 'Извините, произошла ошибка при обработке запроса.')
            st.session_state.chat_history.append({
                'content': assistant_response,
                'is_user': False
            })
        
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Проверка готовности данных для формирования запроса
    required_fields = ['equipment_type', 'device_number', 'description', 'incident_date']
    missing_fields = [field for field in required_fields if not st.session_state.problem_data.get(field)]
    
    if not missing_fields and not st.session_state.show_summary:
        st.markdown("---")
        if st.button("📋 Показать сводку по проблеме", type="secondary"):
            st.session_state.show_summary = True
            st.rerun()
    
    # Отображение сводки и подтверждения
    if st.session_state.show_summary:
        st.markdown("---")
        display_problem_summary(st.session_state.problem_data)
        
        st.markdown("### 📤 Подтверждение отправки запроса")
        st.info("Пожалуйста, проверьте информацию выше. После подтверждения запрос будет отправлен на обработку.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("✅ Подтвердить и отправить", type="primary"):
                # Здесь можно добавить логику отправки итогового запроса
                st.success("✅ Запрос на обслуживание успешно отправлен!")
                st.balloons()
                
                # Сброс состояния
                st.session_state.chat_history = []
                st.session_state.problem_data = {
                    'equipment_type': '',
                    'device_number': '',
                    'description': '',
                    'incident_date': '',
                    'photo_url': ''
                }
                st.session_state.show_summary = False
                st.rerun()
        
        with col2:
            if st.button("✏️ Редактировать", type="secondary"):
                st.session_state.show_summary = False
                st.rerun()
        
        with col3:
            if st.button("❌ Отменить", type="secondary"):
                st.session_state.show_summary = False
                st.rerun()

if __name__ == "__main__":
    main()
