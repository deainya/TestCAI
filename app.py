import streamlit as st
import requests
import json
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

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
        max-width: 800px;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
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
        background-color: #f8f9fa;
        color: #333;
        border: 1px solid #dee2e6;
    }
    
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .email-input {
        margin-bottom: 2rem;
    }
    
    .problem-data {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
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
        "equipment_type": "",
        "device_number": "",
        "description": "",
        "incident_date": "",
        "photo_url": ""
    }
if 'show_confirmation' not in st.session_state:
    st.session_state.show_confirmation = False
if 'final_request' not in st.session_state:
    st.session_state.final_request = None

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, chat_history: List[Dict], problem_data: Dict) -> Optional[Dict]:
    """Отправка данных в n8n"""
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
            st.error(f"Ошибка n8n: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Таймаут при обращении к n8n")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Ошибка подключения к n8n")
        return None
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None

def is_problem_data_complete(problem_data: Dict) -> bool:
    """Проверка полноты данных о проблеме"""
    required_fields = ["equipment_type", "device_number", "description", "incident_date"]
    return all(problem_data.get(field, "").strip() for field in required_fields)

def format_final_request(problem_data: Dict, email: str) -> str:
    """Форматирование итогового запроса"""
    return f"""
**ЗАПРОС НА ОБСЛУЖИВАНИЕ**

**Email:** {email}
**Тип оборудования:** {problem_data.get('equipment_type', 'Не указан')}
**Номер устройства:** {problem_data.get('device_number', 'Не указан')}
**Описание проблемы:** {problem_data.get('description', 'Не указано')}
**Дата инцидента:** {problem_data.get('incident_date', 'Не указана')}
**Фото:** {problem_data.get('photo_url', 'Не приложено')}

**Дата создания заявки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Ввод email
    if not st.session_state.email:
        st.markdown("### Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com", key="email_input")
        
        if st.button("Продолжить"):
            if validate_email(email):
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
    
    else:
        st.success(f"Вы вошли как: {st.session_state.email}")
        
        # Кнопка выхода
        if st.button("Выйти"):
            st.session_state.email = None
            st.session_state.chat_history = []
            st.session_state.problem_data = {
                "equipment_type": "",
                "device_number": "",
                "description": "",
                "incident_date": "",
                "photo_url": ""
            }
            st.session_state.show_confirmation = False
            st.session_state.final_request = None
            st.rerun()
        
        # Чат интерфейс
        st.markdown("### Чат с ассистентом")
        
        # Отображение истории чата
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_history:
                for msg in st.session_state.chat_history:
                    if msg['is_user']:
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>Вы:</strong> {msg['content']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message assistant-message">
                            <strong>Ассистент:</strong> {msg['content']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Первое сообщение ассистента
                if not st.session_state.chat_history:
                    initial_message = "Добрый день! Чем могу помочь? Расскажите о проблеме с оборудованием."
                    st.session_state.chat_history.append({
                        "content": initial_message,
                        "is_user": False
                    })
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Ассистент:</strong> {initial_message}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Ввод сообщения
        if not st.session_state.show_confirmation:
            user_input = st.text_input("Введите ваше сообщение:", key="user_input", placeholder="Опишите проблему...")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Отправить", type="primary"):
                    if user_input.strip():
                        # Добавляем сообщение пользователя в историю
                        st.session_state.chat_history.append({
                            "content": user_input,
                            "is_user": True
                        })
                        
                        # Отправляем в n8n
                        with st.spinner("Обработка запроса..."):
                            response = send_to_n8n(
                                user_input,
                                st.session_state.chat_history,
                                st.session_state.problem_data
                            )
                        
                        if response:
                            # Обновляем данные о проблеме
                            if 'problem_data' in response:
                                st.session_state.problem_data.update(response['problem_data'])
                            
                            # Добавляем ответ ассистента
                            if 'response' in response:
                                st.session_state.chat_history.append({
                                    "content": response['response'],
                                    "is_user": False
                                })
                        
                        st.rerun()
                    else:
                        st.warning("Пожалуйста, введите сообщение")
        
        # Отображение собранных данных
        if any(st.session_state.problem_data.values()):
            st.markdown("### Собранная информация о проблеме")
            problem_data_display = st.session_state.problem_data.copy()
            
            for key, value in problem_data_display.items():
                if value:
                    field_names = {
                        "equipment_type": "Тип оборудования",
                        "device_number": "Номер устройства",
                        "description": "Описание проблемы",
                        "incident_date": "Дата инцидента",
                        "photo_url": "Фото"
                    }
                    st.write(f"**{field_names.get(key, key)}:** {value}")
        
        # Проверка готовности к отправке
        if is_problem_data_complete(st.session_state.problem_data) and not st.session_state.show_confirmation:
            st.success("✅ Все необходимые данные собраны!")
            if st.button("Сформировать запрос на обслуживание", type="primary"):
                st.session_state.final_request = format_final_request(st.session_state.problem_data, st.session_state.email)
                st.session_state.show_confirmation = True
                st.rerun()
        
        # Подтверждение и отправка
        if st.session_state.show_confirmation and st.session_state.final_request:
            st.markdown("### Подтверждение запроса на обслуживание")
            st.markdown(st.session_state.final_request)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Подтвердить и отправить", type="primary"):
                    # Отправляем финальный запрос
                    with st.spinner("Отправка запроса..."):
                        response = send_to_n8n(
                            "done-request",
                            st.session_state.chat_history,
                            st.session_state.problem_data
                        )
                    
                    if response:
                        st.success("✅ Запрос на обслуживание успешно отправлен!")
                        
                        # Очищаем данные
                        st.session_state.chat_history = []
                        st.session_state.problem_data = {
                            "equipment_type": "",
                            "device_number": "",
                            "description": "",
                            "incident_date": "",
                            "photo_url": ""
                        }
                        st.session_state.show_confirmation = False
                        st.session_state.final_request = None
                        st.rerun()
                    else:
                        st.error("Ошибка при отправке запроса")
            
            with col2:
                if st.button("❌ Отменить"):
                    st.session_state.show_confirmation = False
                    st.session_state.final_request = None
                    st.rerun()

if __name__ == "__main__":
    main()
