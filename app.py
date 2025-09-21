import streamlit as st
import requests
import json
import re
from datetime import datetime
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
        max-width: 80%;
        margin-left: auto;
    }
    
    .assistant-message {
        background-color: #f1f3f4;
        color: black;
        padding: 10px;
        border-radius: 10px 10px 10px 0;
        margin: 5px 0;
        max-width: 80%;
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
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message, chat_history, problem_data):
    """Отправка запроса в n8n"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        return {"error": "N8N_WEBHOOK_URL не настроен"}
    
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
            response_data = response.json()
            
            # Парсинг ответа в зависимости от структуры
            if isinstance(response_data, list) and len(response_data) > 0:
                # Если ответ - массив (как в примере)
                first_item = response_data[0]
                if 'message' in first_item and 'content' in first_item['message']:
                    content = first_item['message']['content']
                    return {
                        "response": content.get("response", "Извините, не удалось получить ответ."),
                        "problem_data": content.get("problem_data", {})
                    }
                else:
                    return {"error": "Неожиданная структура ответа от n8n"}
            elif isinstance(response_data, dict):
                # Если ответ - объект
                return {
                    # "response": response_data.get("response", "Извините, не удалось получить ответ."),
                    "response": json.dumps(response_data, ensure_ascii=False, indent=2)
                    "problem_data": response_data.get("problem_data", {})
                }
            else:
                return {"error": "Неожиданный формат ответа от n8n"}
        else:
            return {"error": f"Ошибка сервера: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"error": "Таймаут запроса"}
    except requests.exceptions.ConnectionError:
        return {"error": "Ошибка подключения"}
    except Exception as e:
        return {"error": f"Неожиданная ошибка: {str(e)}"}

def initialize_session_state():
    """Инициализация состояния сессии"""
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

def display_chat():
    """Отображение чата"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.chat_history:
        if message['is_user']:
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_final_form():
    """Отображение итоговой формы"""
    st.subheader("📋 Итоговый запрос на обслуживание")
    
    with st.form("final_request"):
        st.write("**Проверьте данные перед отправкой:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            equipment_type = st.text_input(
                "Тип оборудования",
                value=st.session_state.problem_data.get("equipment_type", ""),
                disabled=True
            )
            device_number = st.text_input(
                "Номер устройства",
                value=st.session_state.problem_data.get("device_number", ""),
                disabled=True
            )
        
        with col2:
            incident_date = st.text_input(
                "Дата инцидента",
                value=st.session_state.problem_data.get("incident_date", ""),
                disabled=True
            )
            photo_url = st.text_input(
                "URL фото (опционально)",
                value=st.session_state.problem_data.get("photo_url", ""),
                disabled=True
            )
        
        description = st.text_area(
            "Описание проблемы",
            value=st.session_state.problem_data.get("description", ""),
            disabled=True,
            height=100
        )
        
        submitted = st.form_submit_button("✅ Отправить запрос", type="primary")
        
        if submitted:
            # Здесь можно добавить логику отправки итогового запроса
            st.success("✅ Запрос на обслуживание успешно отправлен!")
            st.balloons()
            
            # Очистка данных после отправки
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

def main():
    """Основная функция приложения"""
    initialize_session_state()
    
    st.title("🔧 Запрос на обслуживание")
    st.markdown("---")
    
    # Проверка email
    if not st.session_state.email:
        st.subheader("📧 Введите ваш email")
        email = st.text_input("Email", placeholder="example@company.com")
        
        if st.button("Продолжить", type="primary"):
            if validate_email(email):
                st.session_state.email = email
                st.success("✅ Email подтвержден!")
                st.rerun()
            else:
                st.error("❌ Пожалуйста, введите корректный email адрес")
    else:
        # Отображение email пользователя
        st.info(f"👤 Пользователь: {st.session_state.email}")
        
        # Проверка готовности данных для итоговой формы
        required_fields = ["equipment_type", "device_number", "description", "incident_date"]
        all_required_filled = all(st.session_state.problem_data.get(field) for field in required_fields)
        
        if all_required_filled and not st.session_state.show_final_form:
            if st.button("📋 Показать итоговый запрос", type="primary"):
                st.session_state.show_final_form = True
                st.rerun()
        
        if st.session_state.show_final_form:
            display_final_form()
        else:
            # Чат интерфейс
            st.subheader("💬 Чат с ассистентом")
            display_chat()
            
            # Ввод сообщения
            with st.form("chat_form", clear_on_submit=True):
                user_message = st.text_input("Введите ваше сообщение:", placeholder="Опишите проблему...")
                submitted = st.form_submit_button("Отправить", type="primary")
                
                if submitted and user_message:
                    # Добавляем сообщение пользователя в историю
                    st.session_state.chat_history.append({
                        "content": user_message,
                        "is_user": True
                    })
                    
                    # Отправляем запрос в n8n
                    with st.spinner("Ассистент печатает..."):
                        response = send_to_n8n(
                            user_message,
                            st.session_state.chat_history,
                            st.session_state.problem_data
                        )
                    
                    if "error" in response:
                        st.error(f"❌ {response['error']}")
                        # Добавляем сообщение об ошибке
                        st.session_state.chat_history.append({
                            "content": f"Извините, произошла ошибка: {response['error']}",
                            "is_user": False
                        })
                    else:
                        # Добавляем весь JSON ответ от n8n
                        assistant_response = json.dumps(response, ensure_ascii=False, indent=2)
                        st.session_state.chat_history.append({
                            "content": assistant_response,
                            "is_user": False
                        })
                        
                        # Обновляем данные о проблеме
                        if "problem_data" in response:
                            st.session_state.problem_data.update(response["problem_data"])
                            print(f"Обновленные problem_data: {st.session_state.problem_data}")
                    
                    st.rerun()
        
        # Кнопка сброса
        if st.button("🔄 Начать заново"):
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

if __name__ == "__main__":
    main()
