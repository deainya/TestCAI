import streamlit as st

# Настройка страницы
st.set_page_config(
    page_title="Hello World App",
    page_icon="👋",
    layout="wide"
)

# Заголовок приложения
st.title("👋 Hello World!")
st.subheader("Добро пожаловать в Streamlit!")

# Основной контент
st.write("Это минимальное приложение Streamlit для демонстрации.")

# Добавим интерактивные элементы
st.markdown("---")

# Секция с кнопкой
if st.button("Нажми меня!"):
    st.success("🎉 Кнопка нажата! Приложение работает!")

# Секция с вводом текста
name = st.text_input("Введите ваше имя:", placeholder="Ваше имя")
if name:
    st.write(f"Привет, {name}! 👋")

# Секция с выбором
option = st.selectbox(
    "Выберите ваш любимый язык программирования:",
    ["Python", "JavaScript", "Java", "C++", "Go", "Rust"]
)

if option:
    st.write(f"Отличный выбор! {option} - замечательный язык! 🚀")

# Секция с метриками
st.markdown("---")
st.markdown("### 📊 Статистика")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Пользователи", "1,234", "123")

with col2:
    st.metric("Сессии", "5,678", "456")

with col3:
    st.metric("Конверсия", "12.5%", "2.1%")

# Футер
st.markdown("---")
st.markdown("Создано с ❤️ используя Streamlit")

