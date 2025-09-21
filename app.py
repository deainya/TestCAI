import streamlit as st
import requests
import json
import re
from datetime import datetime
import time

# Настройка страницы для мобильной версии
st.set_page_config(
    page_title="Запрос на обслуживание",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS для мобильной версии
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stTextInput > div > div > input {
        font-size: 16px;
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
        color: #333;
        margin-right: auto;
    }
    
    .error-message {
        background-color: #dc3545;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #28a745;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
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
        'equipment_type': None,
        'device_number': None,
        'description': None,
        'incident_date': None,
        'photo_url': None
    }
if 'final_request' not in st.session_state:
    st.session_state.final_request = None

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message, chat_history):
    """Отправка сообщения в n8n для обработки LLM"""
    try:
        webhook_url = st.secrets.get("N8N_WEBHOOK_URL")
        if not webhook_url:
            return {"error": "N8N_WEBHOOK_URL не настроен"}
        
        payload = {
            "message": message,
            "chat_history": chat_history,
            "problem_data": st.session_state.problem_data
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30
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

def display_chat_message(message, is_user=True):
    """Отображение сообщения в чате"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            {message}
        </div>
        """, unsafe_allow_html=True)

def check_required_fields():
    """Проверка заполнения обязательных полей"""
    required = ['equipment_type', 'device_number', 'description', 'incident_date']
    missing = [field for field in required if not st.session_state.problem_data.get(field)]
    return missing

def generate_final_request():
    """Генерация итогового запроса на обслуживание"""
    data = st.session_state.problem_data
    request = f"""
**ЗАПРОС НА ОБСЛУЖИВАНИЕ**

**Email пользователя:** {st.session_state.email}

**Тип оборудования:** {data['equipment_type']}

**Номер устройства:** {data['device_number']}

**Описание проблемы:** {data['description']}

**Дата инцидента:** {data['incident_date']}

**Фото (если приложено):** {data['photo_url'] or 'Не приложено'}

**Дата создания запроса:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
    """
    return request.strip()

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Проверка email
    if not st.session_state.email:
        st.markdown("### Введите ваш email для продолжения")
        email = st.text_input("Email:", placeholder="example@company.com")
        
        if st.button("Продолжить"):
            if email and validate_email(email):
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
        return
    
    # Основной интерфейс после ввода email
    st.markdown(f"**Пользователь:** {st.session_state.email}")
    
    # Чат интерфейс
    st.markdown("### Чат с ассистентом")
    
    # Отображение истории чата
    for message in st.session_state.chat_history:
        display_chat_message(message['content'], message['is_user'])
    
    # Если чат пустой, показываем приветствие
    if not st.session_state.chat_history:
        display_chat_message("Добрый день, чем могу помочь?", False)
        st.session_state.chat_history.append({
            'content': "Добрый день, чем могу помочь?",
            'is_user': False
        })
    
    # Поле ввода сообщения
    user_input = st.text_input("Ваше сообщение:", placeholder="Опишите проблему...", key="user_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Отправить"):
            if user_input:
                # Добавляем сообщение пользователя
                st.session_state.chat_history.append({
                    'content': user_input,
                    'is_user': True
                })
                
                # Отправляем в n8n для обработки
                with st.spinner("Обрабатываю запрос..."):
                    response = send_to_n8n(user_input, st.session_state.chat_history)
                
                if "error" in response:
                    st.error(f"Ошибка: {response['error']}")
                else:
                    # Добавляем ответ ассистента
                    assistant_response = response.get('response', 'Извините, произошла ошибка обработки')
                    st.session_state.chat_history.append({
                        'content': assistant_response,
                        'is_user': False
                    })
                    
                    # Обновляем данные о проблеме если они есть в ответе
                    if 'problem_data' in response:
                        st.session_state.problem_data.update(response['problem_data'])
                
                st.rerun()
    
    with col2:
        if st.button("Очистить чат"):
            st.session_state.chat_history = []
            st.session_state.problem_data = {
                'equipment_type': None,
                'device_number': None,
                'description': None,
                'incident_date': None,
                'photo_url': None
            }
            st.rerun()
    
    # Проверка заполнения обязательных полей
    missing_fields = check_required_fields()
    
    if not missing_fields:
        st.markdown("---")
        st.markdown("### ✅ Все данные собраны")
        
        # Показываем собранные данные
        st.markdown("**Собранная информация:**")
        data = st.session_state.problem_data
        st.write(f"**Тип оборудования:** {data['equipment_type']}")
        st.write(f"**Номер устройства:** {data['device_number']}")
        st.write(f"**Описание проблемы:** {data['description']}")
        st.write(f"**Дата инцидента:** {data['incident_date']}")
        if data['photo_url']:
            st.write(f"**Фото:** {data['photo_url']}")
        
        # Генерация итогового запроса
        if st.button("Сформировать запрос на обслуживание"):
            st.session_state.final_request = generate_final_request()
            st.rerun()
    
    # Отображение итогового запроса
    if st.session_state.final_request:
        st.markdown("---")
        st.markdown("### 📋 Итоговый запрос на обслуживание")
        st.markdown(st.session_state.final_request)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Подтвердить и отправить"):
                # Отправка финального запроса
                with st.spinner("Отправляю запрос..."):
                    final_response = send_to_n8n(
                        "FINAL_REQUEST", 
                        st.session_state.chat_history
                    )
                
                if "error" in final_response:
                    st.error(f"Ошибка отправки: {final_response['error']}")
                else:
                    st.success("✅ Запрос на обслуживание успешно отправлен!")
                    st.session_state.final_request = None
                    st.session_state.chat_history = []
                    st.session_state.problem_data = {
                        'equipment_type': None,
                        'device_number': None,
                        'description': None,
                        'incident_date': None,
                        'photo_url': None
                    }
                    st.rerun()
        
        with col2:
            if st.button("❌ Отменить"):
                st.session_state.final_request = None
                st.rerun()
    
    # Показываем какие поля еще нужно заполнить
    if missing_fields:
        st.markdown("---")
        st.markdown("### 📝 Требуется дополнительная информация:")
        field_names = {
            'equipment_type': 'Тип оборудования',
            'device_number': 'Номер устройства', 
            'description': 'Описание проблемы',
            'incident_date': 'Дата инцидента'
        }
        for field in missing_fields:
            st.write(f"• {field_names.get(field, field)}")

if __name__ == "__main__":
    main()
