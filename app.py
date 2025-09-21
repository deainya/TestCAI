import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
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
    
    .chat-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px;
        border-top: 1px solid #ddd;
        z-index: 1000;
    }
    
    .main-container {
        padding-bottom: 100px;
    }
    
    @media (max-width: 768px) {
        .chat-container {
            padding: 5px;
        }
        
        .user-message {
            margin-left: 10%;
        }
        
        .assistant-message {
            margin-right: 10%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Функция валидации email
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Функция для отправки запроса в n8n
def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Dict:
    """
    Отправляет запрос в n8n и возвращает ответ
    """
    try:
        webhook_url = st.secrets.get("N8N_WEBHOOK_URL")
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
            "error": "Таймаут запроса к n8n"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Ошибка подключения к n8n"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Неожиданная ошибка: {str(e)}"
        }

# Функция для отображения сообщений чата
def display_chat_message(content: str, is_user: bool):
    if is_user:
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

# Функция для проверки полноты данных о проблеме
def is_problem_data_complete(problem_data: Dict) -> bool:
    required_fields = ["equipment_type", "device_number", "description", "incident_date"]
    return all(problem_data.get(field) for field in required_fields)

# Инициализация session state
if 'email' not in st.session_state:
    st.session_state.email = None
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

# Главный интерфейс
def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Проверка email
    if not st.session_state.email:
        st.markdown("### Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com")
        
        if st.button("Продолжить"):
            if validate_email(email):
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
        
        return
    
    # Отображение email пользователя
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Вы вошли как: {st.session_state.email}")
    with col2:
        if st.button("Сменить email"):
            st.session_state.email = None
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
    
    # Если данные о проблеме собраны, показываем итоговую форму
    if is_problem_data_complete(st.session_state.problem_data) and not st.session_state.show_final_form:
        st.session_state.show_final_form = True
    
    if st.session_state.show_final_form:
        display_final_form()
    else:
        display_chat_interface()

def display_final_form():
    """Отображение итоговой формы запроса на обслуживание"""
    st.markdown("### 📋 Итоговый запрос на обслуживание")
    
    st.markdown("**Проверьте данные перед отправкой:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Тип оборудования:** {st.session_state.problem_data['equipment_type']}")
        st.markdown(f"**Номер устройства:** {st.session_state.problem_data['device_number']}")
    
    with col2:
        st.markdown(f"**Дата инцидента:** {st.session_state.problem_data['incident_date']}")
        if st.session_state.problem_data['photo_url']:
            st.markdown(f"**Фото:** {st.session_state.problem_data['photo_url']}")
    
    st.markdown(f"**Описание проблемы:** {st.session_state.problem_data['description']}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Подтвердить и отправить", type="primary"):
            # Здесь можно добавить логику отправки итогового запроса
            st.success("Запрос на обслуживание успешно отправлен!")
            st.balloons()
            
            # Сброс данных
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

def display_chat_interface():
    """Отображение чат-интерфейса"""
    st.markdown("### 💬 Чат с ассистентом")
    st.markdown("Опишите вашу проблему, и я помогу собрать всю необходимую информацию.")
    
    # Отображение истории чата
    if st.session_state.chat_history:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            display_chat_message(message['content'], message['is_user'])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Первое сообщение от ассистента
        if not st.session_state.chat_history:
            initial_message = "Добрый день! Чем могу помочь? Опишите, пожалуйста, проблему с оборудованием."
            st.session_state.chat_history.append({
                "content": initial_message,
                "is_user": False
            })
            display_chat_message(initial_message, False)
    
    # Ввод сообщения
    st.markdown("---")
    user_message = st.text_input("Введите ваше сообщение:", placeholder="Опишите проблему...")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("Отправить", type="primary"):
            if user_message.strip():
                # Добавляем сообщение пользователя в историю
                st.session_state.chat_history.append({
                    "content": user_message,
                    "is_user": True
                })
                
                # Отправляем запрос в n8n
                with st.spinner("Обрабатываю ваш запрос..."):
                    result = send_to_n8n(
                        user_message,
                        st.session_state.chat_history,
                        st.session_state.problem_data
                    )
                
                if result["success"]:
                    response_data = result["data"]
                    assistant_response = response_data.get("response", "Извините, произошла ошибка при обработке запроса.")
                    
                    # Обновляем данные о проблеме
                    if "problem_data" in response_data:
                        st.session_state.problem_data.update(response_data["problem_data"])
                    
                    # Добавляем ответ ассистента в историю
                    st.session_state.chat_history.append({
                        "content": assistant_response,
                        "is_user": False
                    })
                    
                    st.rerun()
                else:
                    st.error(f"Ошибка: {result['error']}")
    
    with col2:
        if st.button("🔄 Очистить чат"):
            st.session_state.chat_history = []
            st.session_state.problem_data = {
                "equipment_type": "",
                "device_number": "",
                "description": "",
                "incident_date": "",
                "photo_url": ""
            }
            st.rerun()

if __name__ == "__main__":
    main()
