import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
        background-color: #f8f9fa;
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

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Tuple[bool, str, Dict]:
    """
    Отправка запроса в n8n и получение ответа
    
    Returns:
        Tuple[bool, str, Dict]: (success, response_text, updated_problem_data)
    """
    n8n_url = st.secrets.get("N8N_WEBHOOK_URL")
    
    if not n8n_url:
        return False, "Ошибка: N8N_WEBHOOK_URL не настроен", {}
    
    payload = {
        "message": message,
        "chat_history": chat_history,
        "problem_data": problem_data
    }
    
    try:
        response = requests.post(
            n8n_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", "Ответ получен"), data.get("problem_data", {})
        else:
            return False, f"Ошибка сервера: {response.status_code}", {}
            
    except requests.exceptions.Timeout:
        return False, "Ошибка: Превышено время ожидания ответа", {}
    except requests.exceptions.ConnectionError:
        return False, "Ошибка: Не удается подключиться к серверу", {}
    except requests.exceptions.RequestException as e:
        return False, f"Ошибка запроса: {str(e)}", {}
    except json.JSONDecodeError:
        return False, "Ошибка: Неверный формат ответа от сервера", {}
    except Exception as e:
        return False, f"Неожиданная ошибка: {str(e)}", {}

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
    if 'final_request_approved' not in st.session_state:
        st.session_state.final_request_approved = False

def display_chat_message(content: str, is_user: bool):
    """Отображение сообщения в чате"""
    css_class = "user-message" if is_user else "assistant-message"
    st.markdown(f'<div class="chat-message {css_class}">{content}</div>', unsafe_allow_html=True)

def display_chat_history():
    """Отображение истории чата"""
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for message in st.session_state.chat_history:
            display_chat_message(message["content"], message["is_user"])
        
        st.markdown('</div>', unsafe_allow_html=True)

def is_problem_data_complete(problem_data: Dict) -> bool:
    """Проверка полноты данных о проблеме"""
    required_fields = ["equipment_type", "device_number", "description", "incident_date"]
    return all(problem_data.get(field, "").strip() for field in required_fields)

def format_final_request(problem_data: Dict, email: str) -> str:
    """Форматирование итогового запроса"""
    return f"""
**ЗАПРОС НА ОБСЛУЖИВАНИЕ**

**Email:** {email}
**Тип оборудования:** {problem_data.get('equipment_type', 'Не указано')}
**Номер устройства:** {problem_data.get('device_number', 'Не указано')}
**Описание проблемы:** {problem_data.get('description', 'Не указано')}
**Дата инцидента:** {problem_data.get('incident_date', 'Не указано')}
**Фото:** {problem_data.get('photo_url', 'Не приложено')}

**Дата создания запроса:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

def main():
    initialize_session_state()
    
    st.title("🔧 Запрос на обслуживание")
    st.markdown("---")
    
    # Ввод email
    if not st.session_state.email:
        st.subheader("Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com", key="email_input")
        
        if st.button("Продолжить", type="primary"):
            if email and validate_email(email):
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
    
    else:
        st.success(f"Вы вошли как: {st.session_state.email}")
        
        # Кнопка выхода
        if st.button("Выйти", type="secondary"):
            st.session_state.email = ""
            st.session_state.chat_history = []
            st.session_state.problem_data = {
                "equipment_type": "",
                "device_number": "",
                "device_number": "",
                "description": "",
                "incident_date": "",
                "photo_url": ""
            }
            st.session_state.show_final_form = False
            st.session_state.final_request_approved = False
            st.rerun()
        
        st.markdown("---")
        
        # Чат-интерфейс
        if not st.session_state.show_final_form:
            st.subheader("💬 Чат с ассистентом")
            st.markdown("Опишите вашу проблему, и ассистент поможет собрать всю необходимую информацию.")
            
            # Отображение истории чата
            display_chat_history()
            
            # Поле ввода сообщения
            user_message = st.text_input("Ваше сообщение:", placeholder="Введите сообщение...", key="user_input")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                send_button = st.button("Отправить", type="primary")
            
            # Обработка отправки сообщения
            if send_button and user_message.strip():
                # Добавляем сообщение пользователя в историю
                st.session_state.chat_history.append({
                    "content": user_message,
                    "is_user": True
                })
                
                # Отправляем в n8n
                with st.spinner("Обработка запроса..."):
                    success, response, updated_data = send_to_n8n(
                        user_message,
                        st.session_state.chat_history,
                        st.session_state.problem_data
                    )
                
                if success:
                    # Добавляем ответ ассистента в историю
                    st.session_state.chat_history.append({
                        "content": response,
                        "is_user": False
                    })
                    
                    # Обновляем данные о проблеме
                    st.session_state.problem_data.update(updated_data)
                    
                    # Проверяем, заполнены ли все необходимые данные
                    if is_problem_data_complete(st.session_state.problem_data):
                        st.session_state.show_final_form = True
                        st.rerun()
                else:
                    st.error(f"Ошибка: {response}")
            
            # Отображение текущих данных о проблеме
            if any(st.session_state.problem_data.values()):
                st.markdown("---")
                st.subheader("📋 Собранная информация")
                
                data_display = {
                    "Тип оборудования": st.session_state.problem_data.get("equipment_type", "❌ Не указано"),
                    "Номер устройства": st.session_state.problem_data.get("device_number", "❌ Не указано"),
                    "Описание проблемы": st.session_state.problem_data.get("description", "❌ Не указано"),
                    "Дата инцидента": st.session_state.problem_data.get("incident_date", "❌ Не указано"),
                    "Фото": st.session_state.problem_data.get("photo_url", "❌ Не приложено")
                }
                
                for key, value in data_display.items():
                    st.write(f"**{key}:** {value}")
        
        # Форма итогового запроса
        else:
            st.subheader("📝 Итоговый запрос на обслуживание")
            
            final_request = format_final_request(st.session_state.problem_data, st.session_state.email)
            st.markdown(final_request)
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ Подтвердить и отправить", type="primary"):
                    st.session_state.final_request_approved = True
                    st.success("✅ Запрос на обслуживание успешно отправлен!")
                    st.balloons()
            
            with col2:
                if st.button("✏️ Редактировать", type="secondary"):
                    st.session_state.show_final_form = False
                    st.rerun()
            
            with col3:
                if st.button("🔄 Новый запрос", type="secondary"):
                    st.session_state.chat_history = []
                    st.session_state.problem_data = {
                        "equipment_type": "",
                        "device_number": "",
                        "description": "",
                        "incident_date": "",
                        "photo_url": ""
                    }
                    st.session_state.show_final_form = False
                    st.session_state.final_request_approved = False
                    st.rerun()

if __name__ == "__main__":
    main()
