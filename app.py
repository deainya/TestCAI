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
        background-color: #f8f9fa;
        color: #333;
        margin-right: auto;
    }
    
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Инициализация session state
if 'email' not in st.session_state:
    st.session_state.email = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'service_request_data' not in st.session_state:
    st.session_state.service_request_data = {
        'equipment_type': None,
        'device_number': None,
        'problem_description': None,
        'incident_date': None,
        'photo_url': None
    }
if 'chat_active' not in st.session_state:
    st.session_state.chat_active = False

def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n(message: str, user_email: str) -> Dict:
    """Отправка сообщения в N8N для обработки LLM"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        return {
            'success': False,
            'error': 'N8N_WEBHOOK_URL не настроен. Обратитесь к администратору.'
        }
    
    payload = {
        'message': message,
        'user_email': user_email,
        'timestamp': datetime.now().isoformat(),
        'session_id': f"{user_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ServiceRequestApp/1.0'
            }
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': 'Некорректный ответ от сервера'
                }
        elif response.status_code == 404:
            return {
                'success': False,
                'error': 'Сервис временно недоступен. Попробуйте позже.'
            }
        elif response.status_code == 500:
            return {
                'success': False,
                'error': 'Внутренняя ошибка сервера. Попробуйте позже.'
            }
        else:
            return {
                'success': False,
                'error': f'Ошибка сервера: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Превышено время ожидания. Проверьте подключение к интернету.'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Ошибка подключения. Проверьте интернет-соединение.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Ошибка сети: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Неожиданная ошибка: {str(e)}'
        }

def extract_service_data(llm_response: str) -> Dict:
    """Извлечение данных о заявке из ответа LLM"""
    data = {
        'equipment_type': None,
        'device_number': None,
        'problem_description': None,
        'incident_date': None,
        'photo_url': None
    }
    
    # Поиск типа оборудования
    equipment_keywords = ['принтер', 'компьютер', 'сервер', 'роутер', 'монитор', 'сканер', 'факс', 'телефон']
    for keyword in equipment_keywords:
        if keyword.lower() in llm_response.lower():
            data['equipment_type'] = keyword
            break
    
    # Поиск номера устройства (серийный номер, инвентарный номер)
    import re
    device_patterns = [
        r'номер[:\s]+([A-Z0-9-]+)',
        r'серийный[:\s]+([A-Z0-9-]+)',
        r'инвентарный[:\s]+([A-Z0-9-]+)',
        r'устройство[:\s]+([A-Z0-9-]+)'
    ]
    
    for pattern in device_patterns:
        match = re.search(pattern, llm_response, re.IGNORECASE)
        if match:
            data['device_number'] = match.group(1)
            break
    
    # Поиск описания проблемы
    problem_keywords = ['не работает', 'сломан', 'ошибка', 'проблема', 'не включается', 'не печатает']
    for keyword in problem_keywords:
        if keyword.lower() in llm_response.lower():
            # Извлекаем предложение с описанием проблемы
            sentences = llm_response.split('.')
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    data['problem_description'] = sentence.strip()
                    break
            break
    
    # Поиск даты
    date_patterns = [
        r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4})',
        r'(сегодня|вчера|позавчера)'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, llm_response, re.IGNORECASE)
        if match:
            data['incident_date'] = match.group(1)
            break
    
    # Поиск URL фото
    url_pattern = r'https?://[^\s]+\.(jpg|jpeg|png|gif|bmp)'
    url_match = re.search(url_pattern, llm_response, re.IGNORECASE)
    if url_match:
        data['photo_url'] = url_match.group(0)
    
    return data

def check_missing_data() -> List[str]:
    """Проверка недостающих данных в заявке"""
    missing = []
    data = st.session_state.service_request_data
    
    if not data['equipment_type']:
        missing.append('тип оборудования')
    if not data['device_number']:
        missing.append('номер устройства')
    if not data['problem_description']:
        missing.append('описание проблемы')
    if not data['incident_date']:
        missing.append('дата инцидента')
    
    return missing

def generate_smart_question() -> str:
    """Генерация умного вопроса на основе недостающих данных"""
    missing = check_missing_data()
    data = st.session_state.service_request_data
    
    if not data['equipment_type']:
        return "Какой тип оборудования требует ремонта? (принтер, компьютер, сервер, роутер и т.д.)"
    elif not data['device_number']:
        return "Укажите номер или серийный номер устройства, если знаете."
    elif not data['problem_description']:
        return "Опишите подробно, в чем заключается проблема с оборудованием."
    elif not data['incident_date']:
        return "Когда произошла проблема? (дата или примерное время)"
    else:
        return "Есть ли у вас фотографии проблемы? Если да, приложите ссылку на изображение."

def display_chat_message(message: str, is_user: bool = True):
    """Отображение сообщения в чате"""
    css_class = "user-message" if is_user else "assistant-message"
    st.markdown(f'<div class="chat-message {css_class}">{message}</div>', unsafe_allow_html=True)

def main():
    st.title("🔧 Запрос на обслуживание")
    
    # Проверка email
    if not st.session_state.email:
        st.markdown("### Введите ваш email для продолжения")
        
        email = st.text_input(
            "Email:",
            placeholder="example@company.com",
            help="Введите корректный email адрес"
        )
        
        if st.button("Продолжить", type="primary"):
            if email and validate_email(email):
                st.session_state.email = email
                st.session_state.chat_active = True
                st.rerun()
            else:
                st.error("Пожалуйста, введите корректный email адрес")
    
    else:
        # Отображение email пользователя
        st.success(f"Вы вошли как: {st.session_state.email}")
        
        if st.button("Выйти", type="secondary"):
            st.session_state.email = None
            st.session_state.chat_history = []
            st.session_state.service_request_data = {
                'equipment_type': None,
                'device_number': None,
                'problem_description': None,
                'incident_date': None,
                'photo_url': None
            }
            st.session_state.chat_active = False
            st.rerun()
        
        # Чат интерфейс
        if st.session_state.chat_active:
            st.markdown("### Чат с ассистентом")
            
            # Отображение истории чата
            for message in st.session_state.chat_history:
                display_chat_message(message['content'], message['is_user'])
            
            # Проверка завершенности сбора данных
            missing_data = check_missing_data()
            total_fields = 4  # equipment_type, device_number, problem_description, incident_date
            completed_fields = total_fields - len(missing_data)
            progress = completed_fields / total_fields
            
            # Индикатор прогресса
            st.progress(progress)
            st.caption(f"Прогресс: {completed_fields}/{total_fields} полей заполнено")
            
            if missing_data:
                st.info(f"Необходимо собрать дополнительную информацию: {', '.join(missing_data)}")
            else:
                st.success("✅ Все необходимые данные собраны!")
                
                # Отображение итогового запроса
                st.markdown("### Итоговый запрос на обслуживание")
                
                data = st.session_state.service_request_data
                request_summary = f"""
**Тип оборудования:** {data['equipment_type']}
**Номер устройства:** {data['device_number']}
**Описание проблемы:** {data['problem_description']}
**Дата инцидента:** {data['incident_date']}
"""
                if data['photo_url']:
                    request_summary += f"**Фото:** {data['photo_url']}\n"
                
                st.markdown(request_summary)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Отправить заявку", type="primary"):
                        # Отправка итогового запроса
                        final_request = {
                            'user_email': st.session_state.email,
                            'equipment_type': data['equipment_type'],
                            'device_number': data['device_number'],
                            'problem_description': data['problem_description'],
                            'incident_date': data['incident_date'],
                            'photo_url': data['photo_url'],
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        result = send_to_n8n(json.dumps(final_request), st.session_state.email)
                        
                        if result['success']:
                            st.success("✅ Заявка успешно отправлена!")
                            st.balloons()
                            
                            # Очистка данных после успешной отправки
                            st.session_state.chat_history = []
                            st.session_state.service_request_data = {
                                'equipment_type': None,
                                'device_number': None,
                                'problem_description': None,
                                'incident_date': None,
                                'photo_url': None
                            }
                            
                            # Показать кнопку для новой заявки
                            if st.button("Создать новую заявку", type="primary"):
                                st.rerun()
                        else:
                            st.error(f"❌ Ошибка отправки: {result['error']}")
                            st.info("Попробуйте еще раз или обратитесь к администратору.")
                
                with col2:
                    if st.button("Редактировать данные"):
                        st.session_state.service_request_data = {
                            'equipment_type': None,
                            'device_number': None,
                            'problem_description': None,
                            'incident_date': None,
                            'photo_url': None
                        }
                        st.rerun()
            
            # Поле ввода сообщения
            user_message = st.text_input(
                "Введите ваше сообщение:",
                placeholder="Опишите проблему...",
                key="user_input"
            )
            
            if st.button("Отправить", type="primary") and user_message:
                # Добавление сообщения пользователя в историю
                st.session_state.chat_history.append({
                    'content': user_message,
                    'is_user': True
                })
                
                # Отправка в N8N
                with st.spinner("Обработка запроса..."):
                    result = send_to_n8n(user_message, st.session_state.email)
                    
                    if result['success']:
                        # Получение ответа от LLM
                        llm_response = result['data'].get('response', 'Извините, не удалось обработать запрос.')
                        
                        # Обновление данных заявки из ответа пользователя
                        extracted_data = extract_service_data(user_message)
                        for key, value in extracted_data.items():
                            if value:
                                st.session_state.service_request_data[key] = value
                        
                        # Проверяем, нужны ли дополнительные вопросы
                        missing_data = check_missing_data()
                        if missing_data:
                            # Генерируем умный вопрос
                            smart_question = generate_smart_question()
                            assistant_response = f"{llm_response}\n\n{smart_question}"
                        else:
                            assistant_response = f"{llm_response}\n\n✅ Отлично! Я собрал всю необходимую информацию. Теперь можно сформировать заявку на обслуживание."
                        
                        # Добавление ответа ассистента в историю
                        st.session_state.chat_history.append({
                            'content': assistant_response,
                            'is_user': False
                        })
                        
                        st.rerun()
                    else:
                        st.error(f"Ошибка: {result['error']}")
            
            # Показываем подсказки для пользователя
            if not st.session_state.chat_history:
                st.markdown("""
                **💡 Подсказка:** Опишите проблему с оборудованием. Ассистент поможет собрать всю необходимую информацию:
                - Тип оборудования (принтер, компьютер, сервер и т.д.)
                - Номер или серийный номер устройства
                - Подробное описание проблемы
                - Дата возникновения проблемы
                - Фото проблемы (если есть)
                """)

if __name__ == "__main__":
    main()
