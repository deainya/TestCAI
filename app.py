import streamlit as st
import requests
import json
import re
from datetime import datetime
import os
from typing import List, Dict, Any

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
    
    .message-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px;
        border-top: 1px solid #ddd;
        z-index: 1000;
    }
    
    .chat-messages {
        margin-bottom: 80px;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
    }
    
    @media (max-width: 768px) {
        .user-message {
            margin-left: 10%;
        }
        
        .assistant-message {
            margin-right: 10%;
        }
    }
</style>
""", unsafe_allow_html=True)

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Dict[str, Any]:
    """Отправка запроса в n8n"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        return {
            "success": False,
            "error": "N8N_WEBHOOK_URL не настроен"
        }
    
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
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка сервера: {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Таймаут запроса"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Ошибка подключения"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Неожиданная ошибка: {str(e)}"
        }

def display_chat_message(content: str, is_user: bool):
    """Отображение сообщения в чате"""
    if is_user:
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

def initialize_session_state():
    """Инициализация состояния сессии"""
    if 'email' not in st.session_state:
        st.session_state.email = ""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'problem_data' not in st.session_state:
        st.session_state.problem_data = {
            "equipment_type": "",
            "device_number": "",
            "description": "",
            "incident_date": "",
            "photo_url": ""
        }
    if 'show_final_form' not in st.session_state:
        st.session_state.show_final_form = False

def main():
    initialize_session_state()
    
    st.title("🔧 Запрос на обслуживание")
    
    # Проверка email
    if not st.session_state.email:
        st.markdown("### Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com")
        
        if st.button("Продолжить"):
            if validate_email(email):
                st.session_state.email = email
                st.success("Email успешно сохранен!")
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
    else:
        # Отображение email пользователя
        st.markdown(f"**Пользователь:** {st.session_state.email}")
        
        # Чат интерфейс
        st.markdown("### Чат с ассистентом")
        
        # Отображение истории чата
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
            
            if not st.session_state.chat_history:
                # Первое сообщение ассистента
                display_chat_message("Добрый день, чем могу помочь?", False)
                st.session_state.chat_history.append({
                    "content": "Добрый день, чем могу помочь?",
                    "is_user": False
                })
            else:
                for msg in st.session_state.chat_history:
                    display_chat_message(msg["content"], msg["is_user"])
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Ввод сообщения
        with st.form("chat_form", clear_on_submit=True):
            user_message = st.text_input("Введите ваше сообщение:", placeholder="Опишите проблему...")
            submit_button = st.form_submit_button("Отправить")
            
            if submit_button and user_message.strip():
                # Добавляем сообщение пользователя в историю
                st.session_state.chat_history.append({
                    "content": user_message,
                    "is_user": True
                })
                
                # Отправляем запрос в n8n
                with st.spinner("Обработка запроса..."):
                    result = send_to_n8n(
                        user_message,
                        st.session_state.chat_history,
                        st.session_state.problem_data
                    )
                
                if result["success"]:
                    response_data = result["data"]
                    
                    # Обновляем данные о проблеме
                    if "problem_data" in response_data:
                        st.session_state.problem_data.update(response_data["problem_data"])
                    
                    # Добавляем ответ ассистента в историю
                    assistant_response = response_data.get("response", "Извините, произошла ошибка")
                    st.session_state.chat_history.append({
                        "content": assistant_response,
                        "is_user": False
                    })
                    
                    st.success("Сообщение отправлено!")
                    st.rerun()
                else:
                    st.error(f"Ошибка: {result['error']}")
        
        # Проверяем, собраны ли все необходимые данные
        required_fields = ["equipment_type", "device_number", "description", "incident_date"]
        missing_fields = [field for field in required_fields if not st.session_state.problem_data.get(field)]
        
        if not missing_fields and not st.session_state.show_final_form:
            st.markdown("---")
            st.markdown("### Все данные собраны!")
            
            if st.button("Сформировать запрос на обслуживание"):
                st.session_state.show_final_form = True
                st.rerun()
        
        # Отображение итогового запроса
        if st.session_state.show_final_form:
            st.markdown("---")
            st.markdown("### Итоговый запрос на обслуживание")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Email:** {st.session_state.email}")
                st.markdown(f"**Тип оборудования:** {st.session_state.problem_data['equipment_type']}")
                st.markdown(f"**Номер устройства:** {st.session_state.problem_data['device_number']}")
            
            with col2:
                st.markdown(f"**Дата инцидента:** {st.session_state.problem_data['incident_date']}")
                if st.session_state.problem_data['photo_url']:
                    st.markdown(f"**Фото:** {st.session_state.problem_data['photo_url']}")
            
            st.markdown(f"**Описание проблемы:** {st.session_state.problem_data['description']}")
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Подтвердить и отправить"):
                    # Здесь можно добавить логику отправки финального запроса
                    st.success("Запрос на обслуживание успешно отправлен!")
                    st.balloons()
            
            with col2:
                if st.button("✏️ Редактировать"):
                    st.session_state.show_final_form = False
                    st.rerun()
            
            with col3:
                if st.button("🔄 Начать заново"):
                    st.session_state.chat_history = []
                    st.session_state.problem_data = {
                        "equipment_type": "",
                        "device_number": "",
                        "description": "",
                        "incident_date": "",
                        "photo_url": ""
                    }
                    st.session_state.show_final_form = False
                    st.rerun()

if __name__ == "__main__":
    main()
